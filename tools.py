"""
Pluggable Tool Registry & MCP Integration Layer for HIVE.
Agents autonomously discover and call tools — REST APIs, MCP servers,
CLI commands, Python functions — during research missions.
"""

import json
import os
import re
import time
import asyncio
import importlib
import subprocess
from uuid import uuid4
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Callable, Any


@dataclass
class ToolResult:
    """Result from executing a tool. output is formatted text for LLM context."""
    tool_name: str
    success: bool
    output: str = ""
    raw: Any = None
    duration_ms: float = 0.0
    error: str | None = None
    agent_id: str | None = None


# ============================================================
# TOOL CLASSES
# ============================================================

class BaseTool(ABC):
    """Abstract tool. All tools extend this."""

    def __init__(self, name: str, description: str = "",
                 input_schema: dict = None, tool_type: str = "unknown"):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {
            "type": "object", "properties": {}, "required": [],
        }
        self.type = tool_type
        self.enabled = True

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments. Must be implemented."""

    def to_manifest_entry(self) -> dict:
        """Format for LLM tool manifest prompt block."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "type": self.type,
        }

    def to_dict(self) -> dict:
        """Serializable representation for API/UI."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "type": self.type,
            "enabled": self.enabled,
        }


class PythonFunctionTool(BaseTool):
    """Wraps any Python function (sync or async) as a tool."""

    def __init__(self, fn: Callable, name: str, description: str = "",
                 input_schema: dict = None, tool_type: str = "python"):
        super().__init__(name, description, input_schema, tool_type)
        self.fn = fn

    async def execute(self, **kwargs) -> ToolResult:
        t0 = time.monotonic()
        try:
            if asyncio.iscoroutinefunction(self.fn):
                result = await self.fn(**kwargs)
            else:
                result = await asyncio.to_thread(self.fn, **kwargs)
            duration = (time.monotonic() - t0) * 1000
            output = str(result) if result else "No results returned."
            return ToolResult(
                tool_name=self.name, success=True, output=output,
                duration_ms=duration, raw=result,
            )
        except Exception as e:
            duration = (time.monotonic() - t0) * 1000
            return ToolResult(
                tool_name=self.name, success=False, output="",
                duration_ms=duration, error=str(e)[:500],
            )


class BuiltinTool(PythonFunctionTool):
    """System-level tool that cannot be removed by the UI."""
    pass


class HttpApiTool(BaseTool):
    """REST API client tool. Calls external HTTP APIs."""

    def __init__(self, name: str, description: str = "",
                 input_schema: dict = None,
                 base_url: str = "", method: str = "GET",
                 path: str = "", headers: dict = None,
                 body_template: dict = None):
        super().__init__(name, description, input_schema, "http")
        self.base_url = base_url.rstrip("/")
        self.method = method.upper()
        self.path = path
        self.headers = headers or {}
        self.body_template = body_template

    async def execute(self, **kwargs) -> ToolResult:
        t0 = time.monotonic()
        try:
            import httpx
        except ImportError:
            return ToolResult(
                tool_name=self.name, success=False, output="",
                error="httpx not installed. Run: pip install httpx",
            )
        try:
            # Build URL from path template
            formatted_path = self.path.format(**kwargs) if self.path else ""
            url = f"{self.base_url}{formatted_path}"

            # Build body from template
            body = None
            if self.body_template:
                body = {
                    k: (v.format(**kwargs) if isinstance(v, str) else v)
                    for k, v in self.body_template.items()
                }

            # Resolve header values with kwargs
            resolved_headers = {}
            for k, v in self.headers.items():
                if isinstance(v, str) and "{" in v:
                    try:
                        resolved_headers[k] = v.format(**kwargs)
                    except KeyError:
                        resolved_headers[k] = v
                else:
                    resolved_headers[k] = v

            async with httpx.AsyncClient(timeout=30) as client:
                if self.method == "GET":
                    resp = await client.get(url, headers=resolved_headers)
                elif self.method == "POST":
                    resp = await client.post(url, json=body, headers=resolved_headers)
                elif self.method == "PUT":
                    resp = await client.put(url, json=body, headers=resolved_headers)
                else:
                    resp = await client.request(self.method, url,
                                                json=body, headers=resolved_headers)

                duration = (time.monotonic() - t0) * 1000
                text = resp.text[:5000]
                if resp.is_success:
                    try:
                        parsed = resp.json()
                        output = json.dumps(parsed, indent=2)[:5000]
                    except Exception:
                        output = text
                    return ToolResult(
                        tool_name=self.name, success=True, output=output,
                        duration_ms=duration, raw=resp.json() if resp.is_success else text,
                    )
                else:
                    return ToolResult(
                        tool_name=self.name, success=False, output=text[:1000],
                        duration_ms=duration, error=f"HTTP {resp.status_code}: {text[:200]}",
                    )
        except Exception as e:
            duration = (time.monotonic() - t0) * 1000
            return ToolResult(
                tool_name=self.name, success=False, output="",
                duration_ms=duration, error=str(e)[:500],
            )


class McpClientTool(BaseTool):
    """MCP (Model Context Protocol) server tool via stdio JSON-RPC subprocess."""

    def __init__(self, name: str, server_command: list[str],
                 description: str = "", input_schema: dict = None,
                 env: dict = None):
        super().__init__(name, description, input_schema, "mcp")
        self.server_command = server_command
        self.env = env or {}
        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._tools_listed: list[dict] | None = None
        self._lock = asyncio.Lock()

    async def _ensure_connected(self):
        """Start the MCP server subprocess if not running."""
        if (self._process and self._process.returncode is None
                and self._writer and not self._writer.is_closing()):
            return
        # Kill stale process
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
            except Exception:
                pass

        merged_env = {**os.environ, **{k: str(v) for k, v in self.env.items()}}
        self._process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )
        self._reader = self._process.stdout
        self._writer = self._process.stdin

    async def _send_jsonrpc(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC 2.0 message and await response line."""
        await self._ensure_connected()
        async with self._lock:
            req_id = str(uuid4())[:8]
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params or {},
            }
            payload = json.dumps(request) + "\n"
            self._writer.write(payload.encode())
            await self._writer.drain()

            # Read response line
            try:
                line = await asyncio.wait_for(self._reader.readline(), timeout=30)
                if not line:
                    raise ConnectionError("MCP server closed connection")
                return json.loads(line.decode())
            except asyncio.TimeoutError:
                raise TimeoutError(f"MCP server timed out on {method}")

    async def _discover_tools(self):
        """Call MCP tools/list to discover available tools."""
        if self._tools_listed:
            return self._tools_listed
        result = await self._send_jsonrpc("tools/list")
        self._tools_listed = result.get("result", {}).get("tools", [])
        if self._tools_listed and not self.description:
            first = self._tools_listed[0]
            self.description = first.get("description", self.description)
            self.input_schema = first.get("inputSchema", self.input_schema)
        return self._tools_listed

    async def execute(self, **kwargs) -> ToolResult:
        t0 = time.monotonic()
        try:
            await self._discover_tools()
            result = await self._send_jsonrpc("tools/call", {
                "name": self.name,
                "arguments": kwargs,
            })
            duration = (time.monotonic() - t0) * 1000

            rpc_result = result.get("result", {})
            content = rpc_result.get("content", [])
            is_error = "error" in result

            if is_error:
                err = result.get("error", {})
                return ToolResult(
                    tool_name=self.name, success=False, output="",
                    duration_ms=duration,
                    error=str(err.get("message", err))[:500],
                )

            output_parts = []
            for item in content:
                if isinstance(item, dict):
                    output_parts.append(item.get("text", json.dumps(item)))
                else:
                    output_parts.append(str(item))
            output = "\n".join(output_parts)

            return ToolResult(
                tool_name=self.name, success=True, output=output[:5000],
                duration_ms=duration, raw=result,
            )
        except Exception as e:
            duration = (time.monotonic() - t0) * 1000
            return ToolResult(
                tool_name=self.name, success=False, output="",
                duration_ms=duration, error=str(e)[:500],
            )

    async def cleanup(self):
        """Terminate the MCP subprocess."""
        if self._writer and not self._writer.is_closing():
            self._writer.close()
        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass


class CliTool(BaseTool):
    """Shell command execution tool. Template-based command construction."""

    def __init__(self, name: str, description: str = "",
                 input_schema: dict = None,
                 command_template: str = "", timeout: int = 30,
                 working_dir: str = None):
        super().__init__(name, description, input_schema, "cli")
        self.command_template = command_template
        self.timeout = timeout
        self.working_dir = working_dir

    async def execute(self, **kwargs) -> ToolResult:
        t0 = time.monotonic()
        try:
            # Build command by formatting template with kwargs
            cmd = self.command_template
            for key, val in kwargs.items():
                cmd = cmd.replace(f"{{{key}}}", str(val))

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                duration = (time.monotonic() - t0) * 1000
                return ToolResult(
                    tool_name=self.name, success=False, output="",
                    duration_ms=duration,
                    error=f"Command timed out after {self.timeout}s",
                )

            duration = (time.monotonic() - t0) * 1000
            output = stdout.decode()[:5000] if stdout else ""
            stderr_text = stderr.decode()[:1000] if stderr else ""

            if proc.returncode != 0:
                return ToolResult(
                    tool_name=self.name, success=False,
                    output=output, duration_ms=duration,
                    error=stderr_text or f"Exit code: {proc.returncode}",
                )

            return ToolResult(
                tool_name=self.name, success=True,
                output=output or "Command completed (no output)",
                duration_ms=duration, raw={"stdout": output, "stderr": stderr_text},
            )
        except Exception as e:
            duration = (time.monotonic() - t0) * 1000
            return ToolResult(
                tool_name=self.name, success=False, output="",
                duration_ms=duration, error=str(e)[:500],
            )


# ============================================================
# TOOL REGISTRY
# ============================================================

class ToolRegistry:
    """Manages tool registration, discovery, execution, and usage logging."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._usage_log: list[dict] = []

    def register(self, tool: BaseTool):
        """Register a tool. Raises ValueError on duplicate name."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str):
        """Remove a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """Return all registered tools as serializable dicts."""
        return [t.to_dict() for t in self._tools.values()]

    def get_manifest(self) -> str:
        """Format all enabled tools as a prompt block for the LLM."""
        enabled = [t for t in self._tools.values() if t.enabled]
        if not enabled:
            return ""
        lines = [
            "\n\n=== AVAILABLE TOOLS ===",
            "You have access to these research tools. To use a tool, include",
            "a tool_call block in your response. You may call multiple tools.",
            "",
        ]
        for tool in enabled:
            schema_str = json.dumps(tool.input_schema, indent=2)
            lines.append(f"## Tool: {tool.name}")
            lines.append(f"Type: {tool.type}")
            lines.append(f"Description: {tool.description}")
            lines.append(f"Input Schema:\n{schema_str}")
            lines.append("")
            lines.append("To call this tool, output exactly:")
            lines.append("```tool_call")
            lines.append(json.dumps({"tool": tool.name, "args": {"<key>": "<value>"}}))
            lines.append("```")
            lines.append("")
        lines.append("When you have enough information, produce your final JSON analysis.")
        lines.append("Do NOT include tool_call blocks in your final analysis response.")
        return "\n".join(lines)

    async def execute(self, name: str, agent_id: str = None,
                      **kwargs) -> ToolResult:
        """Execute a tool by name. Logs the call for UI/API."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_name=name, success=False, output="",
                error=f"Unknown tool: {name}",
            )
        if not tool.enabled:
            return ToolResult(
                tool_name=name, success=False, output="",
                error=f"Tool '{name}' is disabled",
            )
        result = await tool.execute(**kwargs)
        result.agent_id = agent_id
        self._usage_log.append({
            "tool_name": name,
            "agent_id": agent_id,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "timestamp": time.time(),
            "error": result.error,
        })
        return result

    def get_usage(self) -> list[dict]:
        """Return the tool call log (most recent calls first)."""
        return list(reversed(self._usage_log))[:200]

    def clone(self) -> "ToolRegistry":
        """Create a new registry sharing the same tool instances but fresh usage log."""
        new_reg = ToolRegistry()
        for name, tool in self._tools.items():
            new_reg._tools[name] = tool
        return new_reg

    @classmethod
    def from_config(cls, configs: list[dict], env: dict = None) -> "ToolRegistry":
        """Build a registry from configuration dicts (from API or file)."""
        registry = cls()
        env = env or {}
        for cfg in configs:
            tool = _build_tool_from_config(cfg, env)
            if tool:
                try:
                    registry.register(tool)
                except ValueError:
                    pass  # Skip duplicates
        return registry

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# ============================================================
# FACTORY FUNCTIONS
# ============================================================

def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with built-in search tools."""
    from search import search_web, search_news

    registry = ToolRegistry()
    registry.register(BuiltinTool(
        fn=search_web,
        name="search_web",
        description=(
            "Search the live web for current information using DuckDuckGo and Bing. "
            "Returns formatted results with titles, snippets, and URLs. "
            "Use this for factual research, market data, competitor analysis, and "
            "any topic that requires up-to-date information from the internet."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query — be specific and include relevant keywords",
                },
                "max_results": {
                    "type": "integer",
                    "default": 6,
                    "description": "Maximum number of results to return (1-10)",
                },
            },
            "required": ["query"],
        },
    ))
    registry.register(BuiltinTool(
        fn=search_news,
        name="search_news",
        description=(
            "Search recent news articles about a topic using Google News and DuckDuckGo News. "
            "Returns recent headlines and article summaries. "
            "Use this for time-sensitive topics, current events, market trends, and "
            "any research that benefits from the latest news coverage."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The news search query — include relevant keywords and time context",
                },
                "max_results": {
                    "type": "integer",
                    "default": 6,
                    "description": "Maximum number of results to return (1-10)",
                },
            },
            "required": ["query"],
        },
    ))
    return registry


def _build_tool_from_config(cfg: dict, env: dict = None) -> BaseTool | None:
    """Build a single tool instance from a configuration dict."""
    env = env or {}
    ttype = cfg.get("type", "python")
    try:
        if ttype == "python":
            module_path = cfg.get("module", "")
            fn_name = cfg.get("function", "")
            if not module_path or not fn_name:
                print(f"[tools] python tool requires 'module' and 'function' fields")
                return None
            mod = importlib.import_module(module_path)
            fn = getattr(mod, fn_name)
            return PythonFunctionTool(
                fn=fn,
                name=cfg["name"],
                description=cfg.get("description", ""),
                input_schema=cfg.get("input_schema", {}),
            )
        elif ttype == "http":
            return HttpApiTool(
                name=cfg["name"],
                description=cfg.get("description", ""),
                input_schema=cfg.get("input_schema", {}),
                base_url=cfg.get("base_url", ""),
                method=cfg.get("method", "GET"),
                path=cfg.get("path", ""),
                headers=cfg.get("headers", {}),
                body_template=cfg.get("body_template"),
            )
        elif ttype == "mcp":
            return McpClientTool(
                name=cfg["name"],
                server_command=cfg.get("command", []),
                description=cfg.get("description", ""),
                input_schema=cfg.get("input_schema", {}),
                env={**env, **cfg.get("env", {})},
            )
        elif ttype == "cli":
            return CliTool(
                name=cfg["name"],
                description=cfg.get("description", ""),
                input_schema=cfg.get("input_schema", {}),
                command_template=cfg.get("command_template", ""),
                timeout=cfg.get("timeout", 30),
                working_dir=cfg.get("working_dir"),
            )
        else:
            print(f"[tools] Unknown tool type: {ttype}")
            return None
    except Exception as e:
        print(f"[tools] Failed to build tool '{cfg.get('name', '?')}': {e}")
        return None


# ============================================================
# LLM RESPONSE PARSING
# ============================================================

def extract_tool_calls(raw: str) -> list[dict]:
    """Extract tool_call JSON blocks from an LLM response.

    Parses blocks like:
    ```tool_call
    {"tool": "search_web", "args": {"query": "AI market size 2025"}}
    ```
    Returns a list of {tool, args} dicts.
    """
    pattern = r"```tool_call\s*\n(.*?)\n```"
    matches = re.findall(pattern, raw, re.DOTALL)
    calls = []
    for m in matches:
        try:
            parsed = json.loads(m.strip())
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            if isinstance(parsed, dict) and "tool" in parsed:
                calls.append({
                    "tool": parsed["tool"],
                    "args": parsed.get("args", {}),
                })
        except (json.JSONDecodeError, TypeError):
            continue
    return calls

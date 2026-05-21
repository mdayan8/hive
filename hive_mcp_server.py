#!/usr/bin/env python3
"""
HIVE MCP Server — Exposes HIVE swarm intelligence as Model Context Protocol tools.

Allows any MCP-compatible host (Claude Desktop, VS Code, Cursor, custom agents)
to run simulations, query past runs, and retrieve reports.

Usage:
    python hive_mcp_server.py                    # stdio transport (default)
    python hive_mcp_server.py --transport sse     # SSE transport over HTTP
    python hive_mcp_server.py --transport sse --port 8932

Claude Desktop config:
    {
        "mcpServers": {
            "hive": {
                "command": "python",
                "args": ["/path/to/hive/hive_mcp_server.py"]
            }
        }
    }
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("hive-mcp")

TOOL_DEFINITIONS = [
    {
        "name": "run_simulation",
        "description": (
            "Run a full autonomous swarm forecast on any goal. "
            "Returns a comprehensive verdict with probability scores, "
            "predicted developments, risk analysis, and narrative forecast."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The goal or scenario to analyze",
                },
                "constraints": {
                    "type": "string",
                    "description": "Optional constraints (solo, budget, runway, etc.)",
                },
                "timeline": {
                    "type": "string",
                    "description": "Optional timeline horizon (e.g. 'Q3 2026', '6 months')",
                },
                "risk_tolerance": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Risk tolerance for the analysis",
                    "default": "medium",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "list_runs",
        "description": "List all previous simulation runs with their goal snippets and probability scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of runs to return (default 20)",
                    "default": 20,
                }
            },
        },
    },
    {
        "name": "get_run",
        "description": "Get full details for a specific simulation run including verdict, agents, debate, and scenarios.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Run ID (e.g. run_20260521_120000)",
                }
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "get_report",
        "description": "Get the full markdown report for a specific simulation run.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Run ID (e.g. run_20260521_120000)",
                }
            },
            "required": ["run_id"],
        },
    },
]


async def _run_simulation(goal, constraints="", timeline="", risk_tolerance="medium"):
    """Run a full simulation and wait for the verdict."""
    from orchestrator import run_orchestration_stream
    from events import bus

    result = {}

    async def watcher():
        nonlocal result
        q = bus.subscribe()
        try:
            async for msg in bus.stream(q):
                if msg.get("type") == "verdict_ready":
                    result.update(msg.get("verdict", {}))
                if msg.get("type") == "complete":
                    break
        finally:
            bus.unsubscribe(q)

    watch_task = asyncio.create_task(watcher())
    try:
        await run_orchestration_stream(
            goal=goal,
            constraints=constraints,
            timeline=timeline,
            risk_tolerance=risk_tolerance,
        )
    finally:
        watch_task.cancel()
        try:
            await watch_task
        except asyncio.CancelledError:
            pass

    return result


async def handle_tool_call(name, arguments):
    """Execute a tool and return MCP result."""
    if name == "run_simulation":
        goal = arguments.get("goal", "")
        if not goal:
            return {"content": [{"type": "text", "text": "Error: No goal provided"}], "isError": True}
        try:
            result = await _run_simulation(
                goal=goal,
                constraints=arguments.get("constraints", ""),
                timeline=arguments.get("timeline", ""),
                risk_tolerance=arguments.get("risk_tolerance", "medium"),
            )
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Simulation failed: {e}"}], "isError": True}

    elif name == "list_runs":
        from memory import list_runs, load_json, RUNS_DIR
        limit = arguments.get("limit", 20)
        runs = []
        for run_id in list_runs()[:limit]:
            verdict = load_json(RUNS_DIR / run_id, "verdict.json") or {}
            runs.append({
                "id": run_id,
                "goal": verdict.get("goal", "")[:80],
                "probability": verdict.get("overall_success_probability"),
                "decision": verdict.get("decision"),
                "confidence": verdict.get("confidence_level"),
            })
        return {"content": [{"type": "text", "text": json.dumps(runs, indent=2)}]}

    elif name == "get_run":
        run_id = arguments.get("run_id", "")
        from memory import load_json, RUNS_DIR
        run_dir = RUNS_DIR / run_id
        if not run_dir.exists():
            return {"content": [{"type": "text", "text": f"Run '{run_id}' not found"}], "isError": True}
        data = {
            "verdict": load_json(run_dir, "verdict.json"),
            "agents": load_json(run_dir, "agents.json"),
            "debate": load_json(run_dir, "debate.json"),
            "simulation": load_json(run_dir, "simulation.json"),
        }
        return {"content": [{"type": "text", "text": json.dumps(data, indent=2, default=str)}]}

    elif name == "get_report":
        from memory import RUNS_DIR
        run_id = arguments.get("run_id", "")
        report_path = RUNS_DIR / run_id / "report.md"
        if not report_path.exists():
            return {"content": [{"type": "text", "text": f"Report for '{run_id}' not found"}], "isError": True}
        return {"content": [{"type": "text", "text": report_path.read_text()}]}

    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}


async def serve_stdio():
    """Serve over stdin/stdout JSON-RPC (newline-delimited JSON)."""
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.buffer.readline)
        if not line:
            break
        raw = line.decode().strip()
        if not raw:
            continue

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})
        resp = {"jsonrpc": "2.0", "id": msg_id}

        if method == "initialize":
            resp["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hive", "version": "1.0.0"},
            }
        elif method == "tools/list":
            resp["result"] = {"tools": TOOL_DEFINITIONS}
        elif method == "tools/call":
            resp["result"] = await handle_tool_call(params.get("name", ""), params.get("arguments", {}))
        elif method == "notifications/initialized":
            continue
        elif method == "ping":
            resp["result"] = {}
        else:
            resp["error"] = {"code": -32601, "message": f"Method not found: {method}"}

        body = json.dumps(resp, default=str)
        sys.stdout.buffer.write((body + "\n").encode())
        await sys.stdout.buffer.drain()


def serve_sse(host="127.0.0.1", port=8932):
    """Start an SSE-based MCP server over HTTP."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    import uvicorn

    app = FastAPI(title="HIVE MCP (SSE)")

    _sessions = {}

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        sid = f"sess_{id(request)}"
        _sessions[sid] = asyncio.Queue()

        async def gen():
            yield f"event: endpoint\ndata: /messages?session_id={sid}\n\n"
            try:
                while True:
                    msg = await _sessions[sid].get()
                    yield f"data: {msg}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                _sessions.pop(sid, None)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/messages")
    async def messages(data: dict, request: Request):
        method = data.get("method", "")
        params = data.get("params", {})
        msg_id = data.get("id")
        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "hive", "version": "1.0.0"}},
            }
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOL_DEFINITIONS}}
        elif method == "tools/call":
            result = await handle_tool_call(params.get("name", ""), params.get("arguments", {}))
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        else:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Not found"}},
                status_code=404,
            )

    print(f"\n  HIVE MCP (SSE) at http://{host}:{port}/sse")
    print(f"  Press Ctrl+C to stop\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="HIVE MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--port", type=int, default=8932)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    if args.transport == "sse":
        serve_sse(host=args.host, port=args.port)
    else:
        asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()

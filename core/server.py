"""
FastAPI server with SSE streaming for the RealWorld Simulator desktop UI.
"""

import os
import json
import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .events import bus
from .orchestrator import run_orchestration_stream
from .search import search_web, init_browser, close_browser
from .memory import list_runs, load_json, RUNS_DIR
from .llm import call_llm
from .tools import ToolRegistry, BaseTool, create_default_registry

app = FastAPI(title="ÆTHERION RWS")

# Global tool registry — cloned per-run for isolation
_tool_registry = create_default_registry()

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup():
    """Initialize browser on startup."""
    try:
        await init_browser()
    except Exception as e:
        print(f"[server] Browser init skipped: {e}")


@app.on_event("shutdown")
async def shutdown():
    await close_browser()


@app.get("/")
async def root():
    """Serve the main UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>RealWorld Simulator</h1><p>UI not found</p>")


@app.get("/api/events")
async def event_stream(request: Request):
    """SSE endpoint for real-time streaming."""
    q = bus.subscribe()

    async def event_generator():
        try:
            async for msg in bus.stream(q):
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "complete":
                    break
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(q)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/run")
async def start_run(data: dict):
    """Start a new simulation run."""
    goal = data.get("goal", "")
    constraints = data.get("constraints", "")
    timeline = data.get("timeline", "")
    risk = data.get("risk", "medium")
    model = data.get("model", None)
    tools_config = data.get("tools", None)
    enabled_tools = data.get("enabled_tools", None)

    if not goal:
        return JSONResponse({"error": "No goal provided"}, status_code=400)

    # Create per-run tool registry (clone of global)
    run_registry = _tool_registry.clone()

    # Apply custom tools from request
    if tools_config:
        custom = ToolRegistry.from_config(tools_config)
        for t in custom.list_tools():
            ct = custom.get(t["name"])
            if ct and ct.name not in ("search_web", "search_news"):
                try:
                    run_registry.register(ct)
                except ValueError:
                    pass  # Skip if already exists

    # Apply enabled/disabled toggles
    if enabled_tools:
        for name, enabled in enabled_tools.items():
            t = run_registry.get(name)
            if t:
                t.enabled = bool(enabled)

    async def run_with_errors():
        try:
            await run_orchestration_stream(
                goal=goal,
                constraints=constraints,
                timeline=timeline,
                risk_tolerance=risk,
                model=model or None,
                tool_registry=run_registry,
            )
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"[server] Orchestration error: {e}\n{err}")
            await bus.publish("status", {"message": f"Error: {str(e)[:100]}", "pct": 0})
            await bus.publish("complete", {})

    # Start orchestration in background
    asyncio.create_task(run_with_errors())

    return JSONResponse({"status": "started", "goal": goal})


@app.get("/api/runs")
async def get_runs():
    """List all past runs."""
    runs = []
    for run_id in list_runs()[:20]:
        verdict = load_json(RUNS_DIR / run_id, "verdict.json") or {}
        runs.append({
            "id": run_id,
            "goal": verdict.get("goal", "")[:80],
            "probability": verdict.get("overall_success_probability"),
        })
    return JSONResponse(runs)


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get full data for a specific run."""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        return JSONResponse({"error": "Run not found"}, status_code=404)
    return JSONResponse({
        "verdict": load_json(run_dir, "verdict.json"),
        "agents": load_json(run_dir, "agents.json"),
        "debate": load_json(run_dir, "debate.json"),
        "simulation": load_json(run_dir, "simulation.json"),
    })


@app.get("/api/runs/{run_id}/report")
async def get_report(run_id: str):
    """Get the markdown report for a run."""
    report_path = RUNS_DIR / run_id / "report.md"
    if not report_path.exists():
        return JSONResponse({"error": "Report not found"}, status_code=404)
    return FileResponse(str(report_path), media_type="text/markdown")


@app.get("/api/tools")
async def list_tools():
    """List all registered tools with their schemas and types."""
    return JSONResponse(_tool_registry.list_tools())


@app.post("/api/tools/configure")
async def configure_tools(data: dict):
    """Register custom tools for the session."""
    configs = data.get("tools", [])
    env = data.get("env", {})
    added = []
    for cfg in configs:
        from tools import _build_tool_from_config
        tool = _build_tool_from_config(cfg, env)
        if tool:
            # Don't override builtins
            existing = _tool_registry.get(tool.name)
            if existing and isinstance(existing, BaseTool):
                # Update existing non-builtin tool
                if not getattr(existing, 'type', None) == 'python':
                    continue
            try:
                _tool_registry.register(tool)
                added.append(tool.name)
            except ValueError:
                pass
    return JSONResponse({"status": "ok", "added": added, "tools": _tool_registry.list_tools()})


@app.get("/api/tools/usage")
async def get_tool_usage():
    """Get tool usage log from recent runs."""
    return JSONResponse(_tool_registry.get_usage()[:200])


@app.post("/api/agent/chat")
async def agent_chat(data: dict):
    """Chat with a specific agent in-character."""
    message = data.get("message", "").strip()
    if not message:
        return JSONResponse({"error": "No message"}, status_code=400)

    agent_context = data.get("agent_context", {})
    history = data.get("history", [])

    evidence_text = ""
    if agent_context.get("evidence"):
        evidence_text = "\n".join(f"- {e}" for e in agent_context["evidence"][:8])

    system_prompt = (
        f"You are an AI research agent named \"{agent_context.get('label', 'Agent')}\" "
        f"in the ÆTHERION swarm intelligence prediction simulation.\n\n"
        f"Your assigned domain / hypothesis:\n{agent_context.get('hypothesis', 'N/A')}\n\n"
        f"Your research findings:\n{agent_context.get('findings', 'N/A')}\n\n"
        f"Your reasoning process:\n{agent_context.get('reasoning', 'N/A')}\n\n"
        f"Evidence you gathered:\n{evidence_text or 'N/A'}\n\n"
        f"Risk score: {agent_context.get('score', 'N/A')} | "
        f"Confidence: {agent_context.get('confidence', 'N/A')}\n\n"
        f"You are in conversation with a user who wants to explore your research. "
        f"Stay in character as this specific agent — speak with the authority of your "
        f"domain expertise. Reference your actual research findings and evidence. "
        f"Be insightful but conversational. Keep responses under 300 words."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for h in (history or [])[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = call_llm(messages, temperature=0.7, max_tokens=1024)
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse({"error": str(e)[:200]}, status_code=500)


def serve(host="127.0.0.1", port=8765):
    """Start the server."""
    print(f"\n  ÆTHERION RWS running at http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    serve()

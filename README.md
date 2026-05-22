<div align="center">
  <h1>🐝 HIVE</h1>
  <h3>Autonomous Swarm Intelligence Engine</h3>
  <p><b>Predict. Analyze. Decide.</b></p>

  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22AA55" alt="MIT License"></a>
  <a href="./hive_mcp_server.py"><img src="https://img.shields.io/badge/MCP-Ready-7C3AED" alt="MCP Ready"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://playwright.dev"><img src="https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white" alt="Playwright"></a>
  <a href="./core/agents.py"><img src="https://img.shields.io/badge/Swarm-Multi--Agent-FF6B35" alt="Multi-Agent Swarm"></a>

  <br><br>

  <p>
    <b>Desktop UI</b> •
    <b>CLI</b> •
    <b>MCP Server</b> •
    <b>REST API</b> •
    <b>Python Library</b>
  </p>
</div>

---

## Overview

**HIVE** deploys a swarm of autonomous AI agents to research, debate, and forecast any scenario. Describe your question in natural language — HIVE handles the rest: spinning up specialized agents, giving them tool access, running cross-examination debates, simulating probabilistic outcomes, and delivering a comprehensive intelligence forecast.

```bash
pip install -r requirements.txt && playwright install chromium
echo "LLM_API_KEY=your-key" > .env
python main.py --serve
```

Open **http://127.0.0.1:8765** and start simulating.

---

## Quick Start

<details>
<summary><b>🐍 Source</b></summary>

```bash
git clone https://github.com/mdayan8/hive.git
cd hive

pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # Add your LLM_API_KEY

python main.py --serve
```

</details>

<details>
<summary><b>🤖 MCP — AI Host Integration</b></summary>

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "hive": {
      "command": "python",
      "args": ["/path/to/hive/hive_mcp_server.py"]
    }
  }
}
```

Then ask Claude: *"Run a simulation on AI chip market trends for 2026-2027"*

</details>

<details>
<summary><b>🐳 Docker</b></summary>

*Coming soon*

</details>

---

## Core Interfaces

### Desktop UI
```bash
python main.py --serve
```
Live graph visualization, real-time SSE streaming, full control over agents and tools.

### CLI
```bash
python main.py --goal "Will this startup succeed?" --timeline "18 months"
```

### MCP Server
```bash
python hive_mcp_server.py
```
Plug into Claude, VS Code, Cursor, or any MCP host. Exposes `run_simulation`, `list_runs`, `get_run`, `get_report`.

### REST API
```bash
curl -X POST http://localhost:8765/api/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze AI chip market trends"}'
```

### Python Library
```python
from core.orchestrator import run_orchestration_stream
await run_orchestration_stream(goal="Evaluate this trading strategy")
```

---

## Workflow

```
User Input
    │
    ▼
Seed Extraction & Domain Decomposition
    │
    ▼
Swarm Generation — Autonomous Agent Spawning
    │
    ▼
Parallel Research & Tool Use (Web, APIs, MCP, CLI)
    │
    ▼
Multi-Agent Debate & Consensus Building
    │
    ▼
Probabilistic Simulation (3 scenarios)
    │
    ▼
Final Synthesis — Verdict, Forecast, Action Plan
```

| Step | Description |
|------|-------------|
| **Seed Extraction** | Goal → research domains & agent personas |
| **Swarm Generation** | Root agents spawn sub-agents autonomously |
| **Research** | Agents use tools (search, APIs, MCP, CLI) in parallel |
| **Debate** | Cross-examination, blind spot identification, consensus |
| **Simulation** | Optimistic, realistic, catastrophic outcomes with probabilities |
| **Synthesis** | GO/NO-GO verdict, risk matrix, narrative forecast, action plan |

---

## Architecture

### Components

| Module | Responsibility |
|--------|---------------|
| `core/seed.py` | Goal decomposition into research domains |
| `core/agents.py` | Swarm agent lifecycle & tool-calling loop |
| `core/orchestrator.py` | End-to-end pipeline orchestration |
| `core/debate.py` | Multi-agent cross-examination & consensus |
| `core/simulation.py` | Probabilistic scenario generation |
| `core/report.py` | Markdown report synthesis |
| `core/tools.py` | Pluggable tool registry (HTTP, MCP, CLI, Python) |
| `core/search.py` | Web search via Playwright |
| `core/llm.py` | OpenAI-compatible LLM abstraction |
| `core/server.py` | FastAPI + SSE streaming server |
| `core/memory.py` | Run persistence |
| `core/blackboard.py` | Cross-agent citation graph |
| `core/events.py` | Pub/sub event bus |
| `hive_mcp_server.py` | MCP server — plug into any AI host |

### Tool System

Agents can use any tool during research via the pluggable registry:

| Type | Configuration | Example Use Case |
|------|--------------|-----------------|
| **http** | URL, method, headers, path template | REST APIs, crypto exchanges, threat intel |
| **mcp** | command, args, env | Databases, file systems, any MCP server |
| **cli** | command template | Shell scripts, local analysis tools |
| **python** | inline code | Custom functions evaluated at runtime |
| **builtin** | system-level | `search_web`, `search_news` (always available) |

```json
{
  "type": "http",
  "name": "dexscreener",
  "config": {
    "url": "https://api.dexscreener.com/latest/dex/search",
    "method": "GET",
    "path_template": "?q={token}"
  }
}
```

---

## MCP Server

HIVE exposes itself as a **Model Context Protocol** server for integration with any MCP-compatible host.

```bash
# stdio transport (desktop AI tools)
python hive_mcp_server.py

# SSE transport (web apps)
python hive_mcp_server.py --transport sse --port 8932
```

| Tool | Description |
|------|-------------|
| `run_simulation` | Full swarm forecast — verdict, probabilities, risks, narrative |
| `list_runs` | List all previous simulations |
| `get_run` | Full details (agents, debate, scenarios) for a run |
| `get_report` | Markdown report for a run |

```python
import json, subprocess

proc = subprocess.Popen(
    ["python", "hive_mcp_server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
)

def mcp(method, params={}):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    proc.stdin.write(req + "\n"); proc.stdin.flush()
    return json.loads(proc.stdout.readline())

mcp("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "my-app"}})
result = mcp("tools/call", {"name": "run_simulation", "arguments": {"goal": "Analyze quantum computing market"}})
print(result["result"]["content"][0]["text"])
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | LLM API key (required) |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1/chat/completions` | OpenAI-compatible endpoint |
| `LLM_MODEL_NAME` | `deepseek-v4-flash` | Default LLM model |
| `ORCHESTRATOR_MODEL` | `LLM_MODEL_NAME` | Orchestration & synthesis model |
| `AGENT_MODEL` | `LLM_MODEL_NAME` | Agent research model |

### Provider Examples

```env
# DeepSeek
LLM_API_KEY=sk-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1/chat/completions
LLM_MODEL_NAME=deepseek-v4-flash

# Alibaba Qwen
LLM_API_KEY=sk-qwen-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# OpenAI
LLM_API_KEY=sk-openai-key
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL_NAME=gpt-4o
```

---

## Use Cases

### Startup Validation
```
Goal: "Should I launch a B2B SaaS for dental clinics?"
→ 8 agents research market size, competition, regulations, sales cycles
→ Debate reveals 3 blind spots in founder's assumptions
→ 68% success probability — CONDITIONAL-GO with specific pivots
```

### Threat Assessment
```
Goal: "Top cyber threats to cloud infrastructure in 2026"
→ Agents map attack surfaces, zero-day trends, actor motivations
→ Cross-reference CVE databases, threat intel feeds
→ Prioritized threat matrix with mitigation playbooks
```

### Trading Strategy
```
Goal: "Evaluate a market-neutral crypto trading strategy"
→ Agents connect CoinGecko API, on-chain data, sentiment feeds
→ Analyze correlations, drawdowns, regime changes
→ CONDITIONAL-GO with position-sizing rules — 72% confidence
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Desktop UI |
| GET | `/api/events` | SSE event stream — real-time swarm feed |
| POST | `/api/run` | Start a simulation |
| GET | `/api/runs` | List past runs |
| GET | `/api/runs/{id}` | Run details (verdict, agents, debate, scenarios) |
| GET | `/api/runs/{id}/report` | Markdown report |
| GET | `/api/tools` | List registered tools with schemas |
| POST | `/api/tools/configure` | Register custom tools |
| GET | `/api/tools/usage` | Tool call log |
| POST | `/api/agent/chat` | Chat with an individual agent |

---

## Project Structure

```
hive/
├── main.py                  # CLI & desktop server
├── hive_mcp_server.py       # MCP server
│
├── core/                    # Python package
│   ├── agents.py            # Swarm lifecycle
│   ├── orchestrator.py      # Pipeline orchestration
│   ├── tools.py             # Tool registry
│   ├── server.py            # FastAPI + SSE
│   ├── search.py            # Web search
│   ├── llm.py               # LLM abstraction
│   ├── seed.py              # Goal decomposition
│   ├── debate.py            # Debate engine
│   ├── simulation.py        # Scenario engine
│   ├── report.py            # Report generator
│   ├── memory.py            # Run persistence
│   ├── events.py            # Event bus
│   ├── blackboard.py        # Citation graph
│   ├── prompts.py           # Prompt loader
│   ├── prompts/             # Agent system prompts
│   └── static/              # Desktop UI
│
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

---

## License

[MIT](LICENSE)

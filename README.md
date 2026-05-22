<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-22AA55" alt="MIT">
  <img src="https://img.shields.io/badge/MCP-Ready-7C3AED" alt="MCP">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/github/stars/mdayan8/hive?style=social" alt="Stars">
</p>

<div align="center">
  <h1>🐝 HIVE</h1>
  <h3>Swarm Intelligence That Predicts Anything</h3>
  <p><b>Drop any scenario in. Get an intelligence brief back.</b></p>
  <br>
  <p>
    <a href="#-quick-start"><kbd>🚀 Quick Start</kbd></a>
    <a href="#-mcp-server"><kbd>🔌 MCP Server</kbd></a>
    <a href="#-use-cases"><kbd>📖 Use Cases</kbd></a>
    <a href="#-api-reference"><kbd>📋 API</kbd></a>
  </p>
</div>

<br>

**HIVE deploys a swarm of AI agents that autonomously research, debate, and forecast any scenario.** Plug it into Claude, VS Code, or Cursor as an MCP tool — or run it as a desktop app, CLI, REST API, or Python library.

One config line and your AI can run swarm simulations on demand.

---

## 🔌 MCP Server — One Line, Instant Intelligence

Add this to your **Claude Desktop** config:

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

Then just **ask Claude**:

> *"Run a simulation on whether I should pivot my startup to AI agents"*
> *"What are the top cyber threats to cloud infrastructure in 2026?"*
> *"Analyze this trading strategy risk"*

HIVE spins up agents, researches, debates, runs simulations, and hands you a full forecast. Same setup works for **VS Code, Cursor, and any MCP host**.

```
python hive_mcp_server.py
```

| MCP Tool | What You Get |
|----------|-------------|
| `run_simulation` | Full verdict: probabilities, risks, narrative forecast |
| `list_runs` | All previous simulations |
| `get_run` | Full details (agents, debate, scenarios) |
| `get_report` | Complete markdown report |

---

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt
playwright install chromium

# Configure
echo "LLM_API_KEY=your-api-key" > .env
echo "LLM_BASE_URL=https://api.deepseek.com/v1/chat/completions" >> .env

# Launch desktop UI
python main.py --serve
```

That's it. Open **http://127.0.0.1:8765**, type a goal, watch the swarm unfold live.

### Also works as...

```bash
# CLI
python main.py --goal "Will Web3 gaming take off in 2026?" --timeline "12 months"

# REST API
curl -X POST http://localhost:8765/api/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze NVIDIA competitors"}'

# Python lib
from core.orchestrator import run_orchestration_stream
await run_orchestration_stream(goal="Evaluate this startup")
```

---

## 🧠 How It Works

```
Your Goal → Seed Extraction → Swarm of AI Agents → Parallel Research & Tools
    → Multi-Agent Debate → Probabilistic Simulation → Intelligence Forecast
```

| Phase | What Happens |
|-------|-------------|
| **Seed** | HIVE decomposes your goal into research domains and agent roles |
| **Swarm** | Specialized agents spawn autonomously — market, risk, strategy, finance, trend |
| **Research** | Agents use tools in parallel: web search, APIs, MCP servers, CLI |
| **Debate** | Agents cross-examine findings, challenge assumptions, find blind spots |
| **Simulate** | 3 probabilistic scenarios: optimistic, realistic, catastrophic |
| **Forecast** | GO/NO-GO verdict with probability breakdown, risks, mitigations, narrative |

Agents publish everything live via SSE — you watch the swarm think in real time on the graph UI.

---

## 🛠️ What Agents Can Use

Any tool you connect. The pluggable registry supports 5 types:

```json
{"type": "http", "name": "dexscreener", "config": {"url": "https://api.dexscreener.com/latest/dex/search", "method": "GET", "path_template": "?q={token}"}}
```

```json
{"type": "mcp", "name": "db_analyst", "config": {"command": "npx", "args": ["-y", "@mcp/postgres", "postgresql://..."]}}
```

| Type | What You Can Connect |
|------|---------------------|
| `http` | Any REST API — exchanges, threat intel, news, on-chain data |
| `mcp` | Any MCP server — databases, file systems, APIs |
| `cli` | Shell scripts, python scripts, local tools |
| `python` | Inline functions evaluated at runtime |
| `builtin` | `search_web`, `search_news` (always on) |

Configure via the UI tool manager or API:

```bash
curl -X POST http://localhost:8765/api/tools/configure \
  -H "Content-Type: application/json" \
  -d '{"tools": [{"type": "http", "name": "my_api", "config": {"url": "https://api.example.com"}}]}'
```

---

## 📖 Use Cases

**Startup Validation** → "Should I launch a B2B SaaS for dental clinics?"  
8 agents research market, competition, regulations, sales. Debate reveals 3 blind spots. Verdict: **68% — CONDITIONAL-GO** with pivots.

**Cyber Threat Assessment** → "Top cloud threats in 2026?"  
Agents map attack surfaces, zero-day trends, actor motivations. Cross-reference CVE databases. Returns: **prioritized threat matrix with mitigations**.

**Trading Strategy** → "Evaluate a market-neutral crypto strategy"  
Agents connect CoinGecko, on-chain data, sentiment feeds. Analyze correlations and drawdowns. Verdict: **CONDITIONAL-GO at 72% confidence**.

---

## ⚙️ Config

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.deepseek.com/v1/chat/completions  # or Qwen, OpenAI, etc.
LLM_MODEL_NAME=deepseek-v4-flash
```

Works with any OpenAI-compatible API — DeepSeek, Qwen, OpenAI, Groq, Together, etc.

---

## 📁 Structure

```
hive/
├── main.py                  # CLI & server
├── hive_mcp_server.py       # MCP server ← start here for AI integration
├── core/                    # Engine
│   ├── agents.py            # Swarm lifecycle
│   ├── orchestrator.py      # Pipeline
│   ├── tools.py             # Tool registry
│   ├── server.py            # FastAPI + SSE
│   ├── search.py            # Web search
│   ├── llm.py               # LLM abstraction
│   ├── seed.py / debate.py  # Core logic
│   ├── simulation.py        # Scenarios
│   ├── report.py            # Reports
│   ├── prompts/             # Agent prompts
│   └── static/              # Desktop UI
├── requirements.txt
└── .env.example
```

---

## 📋 API

| Endpoint | What It Does |
|----------|-------------|
| `GET /` | Desktop UI |
| `GET /api/events` | Live SSE stream |
| `POST /api/run` | Start simulation |
| `GET /api/runs` | List past runs |
| `GET /api/runs/{id}` | Run details |
| `GET /api/runs/{id}/report` | Markdown report |
| `GET /api/tools` | List tools |
| `POST /api/tools/configure` | Add custom tools |
| `POST /api/agent/chat` | Talk to an agent |

---

<p align="center">
  <b>HIVE</b> — <a href="https://github.com/mdayan8/hive">GitHub</a> • <a href="LICENSE">MIT License</a>
</p>

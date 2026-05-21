<p align="center">
  <pre style="font-size: 18px; line-height: 1.4; text-align: center; background: linear-gradient(135deg, #7C3AED, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗  ██╗██╗██╗   ██╗███████╗                              ║
║   ██║  ██║██║██║   ██║██╔════╝                              ║
║   ███████║██║╚██╗ ██╔╝█████╗                                ║
║   ██╔══██║██║ ╚████╔╝ ██╔══╝                                ║
║   ██║  ██║██║  ╚██╔╝  ███████╗                              ║
║   ╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝                              ║
║                                                              ║
║   Autonomous Swarm Intelligence Engine                       ║
║   Predict. Analyze. Decide.                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
  </pre>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22AA55" alt="MIT License"></a>
  <a href="./hive_mcp_server.py"><img src="https://img.shields.io/badge/MCP-Ready-7C3AED" alt="MCP Ready"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi" alt="FastAPI"></a>
  <a href="./agents.py"><img src="https://img.shields.io/badge/Agents-Multi--Swarm-FF6B35" alt="Multi-Agent"></a>
</p>

<p align="center">
  <b>English</b>
  ·
  <a href="#">中文文档</a>
</p>

---

## ⚡ Overview

**HIVE** is a next-generation swarm intelligence prediction engine powered by multi-agent AI. Feed it a goal — a market trend, a threat scenario, a strategic bet — and HIVE automatically spins up a swarm of specialized AI agents. Each agent researches independently, then they debate findings, run probabilistic simulations, and converge on a comprehensive intelligence forecast.

You only need to: **Describe your scenario in natural language**

HIVE will return: **A detailed forecast report with probability scores, risk matrix, predicted developments, and an interactive agent graph**

> Think of it as a board of domain experts with full internet access, debating your question 24/7 — then handing you a written brief.

### Our Vision

HIVE democratizes strategic foresight. We believe every decision — personal, business, or geopolitical — deserves the same analytical rigor that intelligence agencies apply to their forecasts:

- **For Builders**: Stress-test your startup idea, trading strategy, or product launch before committing resources
- **For Analysts**: Get a swarm of domain-specific researchers on any threat, trend, or opportunity
- **For Curious Minds**: Explore "what if" scenarios — from novel plotlines to geopolitical shifts
- **For Developers**: Plug HIVE into your stack as an MCP server, REST API, Python library, or CLI tool

From serious intelligence briefs to playful simulations — every "what if" deserves an answer.

---

## 🎯 All-in-One — Use It Your Way

<p align="center">
  <table>
    <tr>
      <td align="center"><b>🖥️ Desktop UI</b></td>
      <td align="center"><b>⌨️ CLI</b></td>
      <td align="center"><b>🔌 MCP Server</b></td>
      <td align="center"><b>🌐 REST API</b></td>
      <td align="center"><b>📦 Python Lib</b></td>
      <td align="center"><b>🧩 Tool Consumer</b></td>
    </tr>
  </table>
</p>

```bash
# Desktop UI — interactive graph, live streaming
python main.py --serve

# CLI — one-shot forecast
python main.py --goal "Will this startup succeed?" --timeline "18 months"

# MCP Server — plug into Claude, VS Code, Cursor
python hive_mcp_server.py

# REST API — integrate anywhere
curl -X POST http://localhost:8765/api/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze AI chip market trends"}'

# Python Library — embed in your code
from orchestrator import run_orchestration_stream
await run_orchestration_stream(goal="Evaluate this trading strategy")
```

---

## 🔄 Workflow

```
                      ┌─────────────────────────┐
                      │   🎯 User Goal / Input   │
                      └────────────┬────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              SEED EXTRACTION & DOMAIN DECOMPOSITION              │
│  • Parse goal into research domains                             │
│  • Identify required agent personas                             │
│  • Configure tools per domain                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SWARM GENERATION & SELF-ORGANIZATION                │
│  • Spawn root agents (market, strategy, risk, finance, trend)   │
│  • Agents autonomously spawn sub-agents                         │
│  • Agents discover and connect to relevant tools                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PARALLEL RESEARCH & TOOL USE                         │
│  • Each agent researches its domain independently                │
│  • Agents call tools (web search, APIs, MCP servers, CLI)       │
│  • Cross-agent citations via blackboard                          │
│  • Real-time SSE streaming to UI                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-AGENT DEBATE & CONSENSUS                       │
│  • Agents cross-examine each other's findings                    │
│  • Challenge assumptions, identify blind spots                   │
│  • Converge on consensus probabilities                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PROBABILISTIC SIMULATION                             │
│  • Generate optimistic / realistic / catastrophic scenarios     │
│  • Monte Carlo-style probability weighting                      │
│  • Risk & opportunity identification                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              FINAL SYNTHESIS & INTELLIGENCE FORECAST              │
│  • Comprehensive verdict (GO / NO-GO / CONDITIONAL-GO)          │
│  • Probability breakdown with confidence level                   │
│  • Predicted developments with timeframes & evidence             │
│  • Key actors & their influence/stance                           │
│  • Evidence lines (for/against each major claim)                 │
│  • Risk matrix with mitigations                                 │
│  • Action plan with milestones                                  │
│  • Narrative forecast (intelligence brief format)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Source

```bash
# Clone
git clone https://github.com/your-org/hive.git
cd hive

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser engine (for web search)
playwright install chromium

# Configure your LLM
cp .env.example .env
# Edit .env with your LLM_API_KEY

# Launch the desktop UI
python main.py --serve
```

Open **http://127.0.0.1:8765** and start simulating.

### Option 2: Docker

*(Coming soon)*

### Option 3: MCP — One-Line Integration

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

Restart Claude and ask: *"Run a simulation on AI chip market trends for 2026-2027"*

---

## 🔌 MCP Server — Plug Into Any Host

HIVE exposes itself as a **Model Context Protocol** server. Any MCP-compatible host (Claude Desktop, VS Code, Cursor, custom agents) can connect and use it as a tool.

```bash
# stdio transport (default — for desktop AI tools)
python hive_mcp_server.py

# SSE transport (HTTP — for web apps)
python hive_mcp_server.py --transport sse --port 8932
```

### Available MCP Tools

| Tool | Input | Returns |
|------|-------|---------|
| `run_simulation` | `goal`, `constraints?`, `timeline?`, `risk_tolerance?` | Full verdict with probabilities, risks, narrative |
| `list_runs` | `limit?` | Past runs with goal snippets & scores |
| `get_run` | `run_id` | Full run data (agents, debate, scenarios, verdict) |
| `get_report` | `run_id` | Complete markdown report |

### From Any Language

```python
import json, subprocess

proc = subprocess.Popen(
    ["python", "hive_mcp_server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
)

def mcpcall(method, params={}):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    proc.stdin.write(req + "\n"); proc.stdin.flush()
    return json.loads(proc.stdout.readline())

mcpcall("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "my-app"}})
result = mcpcall("tools/call", {"name": "run_simulation", "arguments": {"goal": "Analyze quantum computing market"}})
print(result["result"]["content"][0]["text"])
```

Works from any language — just JSON-RPC over stdin/stdout.

---

## 🛠️ Tool System

HIVE's agents can use **any tool** during research. The pluggable tool registry supports:

| Type | Config | Examples |
|------|--------|----------|
| **http** | URL, method, headers, path template | REST APIs, crypto exchanges, threat intel feeds, news APIs |
| **mcp** | command, args, env | Databases (Postgres, SQLite), file systems, any MCP server |
| **cli** | command template | Shell scripts, local analysis tools, python scripts |
| **python** | inline code | Custom functions evaluated at runtime |
| **builtin** | system-level | `search_web`, `search_news` (always available) |

```json
{
  "type": "http",
  "name": "coingecko_price",
  "config": {
    "url": "https://api.coingecko.com/api/v3/simple/price",
    "method": "GET",
    "path_template": "?ids={coin}&vs_currencies=usd"
  }
}
```

```json
{
  "type": "mcp",
  "name": "database_analyst",
  "config": {
    "command": "npx",
    "args": ["-y", "@mcp/postgres", "postgresql://..."]
  }
}
```

Configure via the **UI tool manager** (launch overlay → tool chips) or via API:

```bash
curl -X POST http://127.0.0.1:8765/api/tools/configure \
  -H "Content-Type: application/json" \
  -d '{"tools": [{"type": "http", "name": "my_api", "config": {"url": "https://api.example.com"}}]}'
```

---

## 📸 Screenshots

*(Screenshots coming soon — run `python main.py --serve` to see the live UI)*

---

## 🧠 Core Architecture

### Components

| Module | Responsibility |
|--------|---------------|
| `seed.py` | Goal decomposition into research domains |
| `agents.py` | Swarm agent lifecycle & tool-calling loop |
| `orchestrator.py` | End-to-end pipeline orchestration |
| `debate.py` | Multi-agent cross-examination & consensus |
| `simulation.py` | Probabilistic scenario generation |
| `report.py` | Markdown report synthesis |
| `tools.py` | Pluggable tool registry (HTTP, MCP, CLI, Python) |
| `search.py` | Web search via Playwright |
| `llm.py` | OpenAI-compatible LLM abstraction |
| `server.py` | FastAPI + SSE streaming server |
| `memory.py` | Run persistence (local file system) |
| `blackboard.py` | Cross-agent citation graph |
| `events.py` | Pub/sub event bus |
| `hive_mcp_server.py` | MCP server (plug into any host) |

### Data Flow

```
User Goal → Seed Extractor → Swarm Factory → Root Agents → Sub-Agents
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │  Tool Registry    │
                                                    │  (HTTP/MCP/CLI/…) │
                                                    └─────────┬─────────┘
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │  Debate Engine    │
                                                    └─────────┬─────────┘
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │  Simulation       │
                                                    └─────────┬─────────┘
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │  Final Synthesis  │
                                                    │  → Verdict        │
                                                    │  → Report         │
                                                    └───────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | LLM API key (required — DeepSeek, Qwen, OpenAI, etc.) |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1/chat/completions` | OpenAI-compatible endpoint |
| `LLM_MODEL_NAME` | `deepseek-v4-flash` | Default model for all LLM calls |
| `ORCHESTRATOR_MODEL` | `LLM_MODEL_NAME` | Model for orchestration & synthesis |
| `AGENT_MODEL` | `LLM_MODEL_NAME` | Model for agent research |
| `DEEPSEEK_API_KEY` | `LLM_API_KEY` | Backward compat alias |

### Provider Examples

```env
# DeepSeek
LLM_API_KEY=sk-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1/chat/completions
LLM_MODEL_NAME=deepseek-v4-flash

# Alibaba Qwen (Bailian)
LLM_API_KEY=sk-qwen-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# OpenAI
LLM_API_KEY=sk-openai-key
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL_NAME=gpt-4o
```

---

## 📖 Examples

### Startup Evaluation
```
Goal: "Should I launch a B2B SaaS for dental clinics?"
→ 8 agents research market size, competition, regulations, sales cycles
→ Debate reveals 3 blind spots in founder's assumptions
→ 68% success probability with conditional recommendations
→ Verdict: CONDITIONAL-GO with specific pivots
```

### Cybersecurity Threat Assessment
```
Goal: "What are the top cyber threats to cloud infrastructure in 2026?"
→ Agents map attack surfaces, zero-day trends, actor motivations
→ Cross-reference CVE databases, threat intel feeds
→ Prioritized threat matrix with mitigation playbooks
→ Verdict: NO-GO on current stack, recommends migration
```

### Trading Strategy Analysis
```
Goal: "Evaluate a market-neutral crypto trading strategy"
→ Connect CoinGecko API, on-chain data, sentiment feeds
→ Agents analyze correlations, drawdowns, regime changes
→ Conditional-GO with specific position-sizing rules
→ Verdict: CONDITIONAL-GO with 72% confidence
```

---

## 📋 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Desktop UI (index.html) |
| GET | `/api/events` | SSE event stream — real-time swarm feed |
| POST | `/api/run` | Start a new simulation |
| GET | `/api/runs` | List all past runs |
| GET | `/api/runs/{id}` | Full run details (verdict, agents, debate, scenarios) |
| GET | `/api/runs/{id}/report` | Markdown report download |
| GET | `/api/tools` | List registered tools with JSON schemas |
| POST | `/api/tools/configure` | Register custom tools |
| GET | `/api/tools/usage` | Tool call log from recent runs |
| POST | `/api/agent/chat` | Chat with a specific agent in-character |

---

## 📁 Project Structure

```
hive/
├── main.py                  # CLI & desktop server entry point
├── hive_mcp_server.py       # MCP server — plug into any AI host
│
├── core/                    # Python package
│   ├── agents.py            # Swarm agent lifecycle & tool loop
│   ├── orchestrator.py      # Pipeline orchestration
│   ├── tools.py             # Pluggable tool registry
│   ├── server.py            # FastAPI + SSE streaming
│   ├── search.py            # Web search via Playwright
│   ├── llm.py               # LLM abstraction (OpenAI-compatible)
│   ├── seed.py              # Goal decomposition
│   ├── debate.py            # Multi-agent debate engine
│   ├── simulation.py        # Probabilistic scenario engine
│   ├── report.py            # Markdown report generator
│   ├── memory.py            # Run persistence
│   ├── events.py            # Pub/sub event bus
│   ├── blackboard.py        # Cross-agent citation graph
│   ├── prompts.py           # Prompt loader
│   ├── prompts/             # Agent system prompts
│   └── static/              # Desktop UI
│
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

---

## 🤝 Join the Community

- **GitHub Issues** — Report bugs, request features
- **Discussions** — Share scenarios, ask questions
- **Contributions** — PRs welcome! See open issues.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com), [Playwright](https://playwright.dev), and [DeepSeek](https://deepseek.com)
- Swarm intelligence paradigm inspired by biological hive minds and prediction markets
- MCP protocol by [Anthropic](https://modelcontextprotocol.io)

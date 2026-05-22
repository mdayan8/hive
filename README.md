<div align="center">
  <br>
  <h1>🐝 HIVE</h1>
  <h3>Swarm Intelligence That Predicts Anything</h3>
  <p><i>Drop any scenario in. Get an intelligence brief back.</i></p>

  <br>

  <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-🚀-000?style=for-the-badge" alt="Quick Start"></a>
  <a href="#-mcp-server"><img src="https://img.shields.io/badge/MCP_Server-🔌-7C3AED?style=for-the-badge" alt="MCP"></a>
  <a href="#-how-it-works"><img src="https://img.shields.io/badge/How_It_Works-🧠-00ADD8?style=for-the-badge" alt="Architecture"></a>
  <a href="#-use-cases"><img src="https://img.shields.io/badge/Use_Cases-📖-FF6B35?style=for-the-badge" alt="Use Cases"></a>

  <br><br>

  <table>
    <tr>
      <td align="center"><b>⭐ Stars</b></td>
      <td align="center"><b>🐍 Python</b></td>
      <td align="center"><b>📜 License</b></td>
      <td align="center"><b>🔌 MCP</b></td>
      <td align="center"><b>⚡ API</b></td>
    </tr>
    <tr>
      <td align="center"><a href="https://github.com/mdayan8/hive"><img src="https://img.shields.io/github/stars/mdayan8/hive?style=social" alt="Stars"></a></td>
      <td align="center"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></td>
      <td align="center"><img src="https://img.shields.io/badge/License-MIT-22AA55" alt="MIT"></td>
      <td align="center"><img src="https://img.shields.io/badge/MCP-Ready-7C3AED" alt="MCP"></td>
      <td align="center"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"></td>
    </tr>
  </table>

  <br>

  <p>
    <b>Desktop UI</b> ⁝ <b>CLI</b> ⁝ <b>MCP Server</b> ⁝ <b>REST API</b> ⁝ <b>Python Library</b>
  </p>
</div>

<br>

---

###### What is HIVE?

**HIVE deploys a swarm of autonomous AI agents that research, debate, and forecast any scenario.** Plug it into Claude Desktop, VS Code, or Cursor as an MCP tool — or run it as a standalone desktop app. One config line and your AI can run full swarm simulations on demand.

```bash
pip install -r requirements.txt && playwright install chromium && echo "LLM_API_KEY=sk-..." > .env
python main.py --serve    # ← Desktop UI at http://localhost:8765
python hive_mcp_server.py # ← MCP server for Claude/Cursor/VS Code
```

<br>

---

## 🔌 MCP Server

**Add this to Claude Desktop → instantly get swarm intelligence.**

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

Then ask Claude:

> *"Run a simulation on AI chip market trends for 2026-2027"*  
> *"Should I pivot my startup to AI agents?"*  
> *"What are the top cyber threats to cloud infrastructure?"*

Same one-line config works for **VS Code**, **Cursor**, and any MCP-compatible host.

<br>

| Tool | What You Get |
|------|-------------|
| `run_simulation` | Full intelligence verdict — probabilities, risks, narrative |
| `list_runs` | All past simulations |
| `get_run` | Agents, debate, scenarios, verdict — full detail |
| `get_report` | Complete markdown report |

```
# Or run standalone:
python hive_mcp_server.py
python hive_mcp_server.py --transport sse --port 8932
```

<br>

---

## 🚀 Quick Start

<details open>
<summary><b>🐍 Source Install — 30 seconds</b></summary>

```bash
git clone https://github.com/mdayan8/hive.git
cd hive
pip install -r requirements.txt
playwright install chromium
cp .env.example .env    # Add your LLM_API_KEY
python main.py --serve  # Open http://localhost:8765
```

</details>
<br>
<details>
<summary><b>🤖 MCP Integration — 10 seconds</b></summary>

See [🔌 MCP Server](#-mcp-server) above. One JSON config. Done.

</details>
<br>
<details>
<summary><b>🖥️ All Interfaces</b></summary>

```bash
# CLI — one-shot forecast
python main.py --goal "Will Web3 gaming take off?" --timeline "12 months"

# REST API — integrate anywhere
curl -X POST http://localhost:8765/api/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Analyze NVIDIA competitors"}'

# Python Library
from core.orchestrator import run_orchestration_stream
await run_orchestration_stream(goal="Evaluate this startup")
```

</details>

<br>

---

## 🧠 How It Works

```
        ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐
        │  SEED    │   │  SWARM   │   │ RESEARCH │   │  DEBATE  │   │SIMULATE  │   │ FORECAST  │
        │ EXTRACT  │ → │ GENERATE │ → │ + TOOLS  │ → │ CONSENSUS│ → │ SCENARIOS│ → │ + VERDICT │
        └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └───────────┘
```

| Phase | What Happens |
|-------|-------------|
| **🥇 Seed** | Decompose goal → research domains → agent personas |
| **🥈 Swarm** | Spawn specialized agents (market, risk, strategy, finance, trend) |
| **🥉 Research** | Each agent uses tools in parallel — search, APIs, MCP, CLI |
| **🤝 Debate** | Agents cross-examine findings, challenge assumptions, converge |
| **📊 Simulate** | 3 probabilistic scenarios: optimistic → realistic → catastrophic |
| **🎯 Forecast** | GO/NO-GO verdict + probability breakdown + risks + narrative |

All live-streamed via SSE — watch agents think in real-time on the graph UI.

<br>

---

## 🛠️ Tool System

| Type | What It Connects | Example |
|------|-----------------|---------|
| `http` | Any REST API | DexScreener, CoinGecko, threat intel, news |
| `mcp` | Any MCP server | PostgreSQL, filesystem, browser, APIs |
| `cli` | Shell commands | `curl`, `python analyze.py`, custom scripts |
| `python` | Inline functions | Custom logic evaluated at runtime |
| `builtin` | Always available | `search_web`, `search_news` |

<br>

Connect a DexScreener API — agents automatically discover and use it:

<pre>
{
  "type": "http",
  "name": "dexscreener",
  "config": {
    "url": "https://api.dexscreener.com/latest/dex/search",
    "method": "GET",
    "path_template": "?q={token}"
  }
}
</pre>

Or a PostgreSQL database via MCP:

<pre>
{
  "type": "mcp",
  "name": "db_analyst",
  "config": {
    "command": "npx",
    "args": ["-y", "@mcp/postgres", "postgresql://..."]
  }
}
</pre>

Configure via the UI or API:

```bash
curl -X POST http://localhost:8765/api/tools/configure \
  -H "Content-Type: application/json" \
  -d '{"tools": [{"type": "http", "name": "coin_price", "config": {"url": "https://api.coingecko.com/api/v3/simple/price", "method": "GET", "path_template": "?ids={coin}&vs_currencies=usd"}}]}'
```

<br>

---

## 📖 Use Cases

<table>
  <tr>
    <th width="25%">Scenario</th>
    <th width="50%">What HIVE Does</th>
    <th width="25%">Outcome</th>
  </tr>
  <tr>
    <td><b>🚀 Startup Validation</b></td>
    <td>"Should I launch a B2B SaaS for dental clinics?"<br>8 agents research market size, competition, regulations, sales cycles. Debate reveals 3 blind spots.</td>
    <td><b>68%</b><br>CONDITIONAL-GO</td>
  </tr>
  <tr>
    <td><b>🛡️ Threat Assessment</b></td>
    <td>"Top cloud threats in 2026?"<br>Agents map attack surfaces, zero-day trends, actor motivations. Cross-reference CVE databases.</td>
    <td><b>Threat matrix</b><br>+ mitigations</td>
  </tr>
  <tr>
    <td><b>📈 Trading Strategy</b></td>
    <td>"Evaluate a market-neutral crypto strategy"<br>Connect CoinGecko, on-chain data, sentiment. Analyze correlations & drawdowns.</td>
    <td><b>72%</b><br>CONDITIONAL-GO</td>
  </tr>
</table>

<br>

---

## ⚙️ Configuration

<details>
<summary><b>Environment Variables</b></summary>

<br>

| Variable | Default | Required |
|----------|---------|----------|
| `LLM_API_KEY` | — | ✅ Yes |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1/chat/completions` | ❌ No |
| `LLM_MODEL_NAME` | `deepseek-v4-flash` | ❌ No |
| `ORCHESTRATOR_MODEL` | `LLM_MODEL_NAME` | ❌ No |
| `AGENT_MODEL` | `LLM_MODEL_NAME` | ❌ No |

</details>

<details>
<summary><b>Provider Examples</b></summary>

<br>

```env
# DeepSeek (default)
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

</details>

<br>

---

## 📋 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | 🖥️ Desktop UI |
| `GET` | `/api/events` | 📡 Live SSE stream — real-time swarm feed |
| `POST` | `/api/run` | 🎯 Start a new simulation |
| `GET` | `/api/runs` | 📂 List past runs |
| `GET` | `/api/runs/{id}` | 🔍 Full run details (agents, debate, scenarios, verdict) |
| `GET` | `/api/runs/{id}/report` | 📄 Download markdown report |
| `GET` | `/api/tools` | 🔧 List registered tools with schemas |
| `POST` | `/api/tools/configure` | ➕ Register custom tools |
| `GET` | `/api/tools/usage` | 📊 Tool call log |
| `POST` | `/api/agent/chat` | 💬 Chat with an agent |

<br>

---

## 📁 Project Structure

```
hive/
├── main.py                    # CLI & desktop server entry point
├── hive_mcp_server.py         # 🔌 MCP server — start here for AI integration
│
├── core/                      # 🧠 Swarm engine
│   ├── agents.py              # Agent lifecycle & tool-calling
│   ├── orchestrator.py        # Pipeline orchestration
│   ├── tools.py               # Pluggable tool registry
│   ├── server.py              # FastAPI + SSE streaming
│   ├── search.py              # Web search
│   ├── llm.py                 # LLM abstraction
│   ├── seed.py                # Goal decomposition
│   ├── debate.py              # Multi-agent debate
│   ├── simulation.py          # Scenario engine
│   ├── report.py              # Report generator
│   ├── memory.py              # Run persistence
│   ├── events.py              # Event bus
│   ├── blackboard.py          # Citation graph
│   ├── prompts.py             # Prompt loader
│   ├── prompts/               # Agent system prompts
│   └── static/                # Desktop UI
│
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

<br>

---

<div align="center">
  <p>
    <a href="https://github.com/mdayan8/hive"><img src="https://img.shields.io/badge/GitHub-mdayan8/hive-181717?logo=github" alt="GitHub"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22AA55" alt="MIT"></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  </p>
  <p><i>Built with FastAPI, Playwright, and DeepSeek. MCP protocol by Anthropic.</i></p>
</div>

"""
True autonomous swarm agents — each agent decides how to research, how many sub-agents to spawn,
and when to complete. No fixed types, no hardcoded limits.
"""

import json
import asyncio
from uuid import uuid4
from .llm import call_llm
from .events import bus
from .blackboard import board
from .tools import ToolRegistry, BuiltinTool, extract_tool_calls

AGENT_COLORS = [
    "#7F77DD", "#1D9E75", "#D85A30", "#378ADD", "#BA7517",
    "#D4537E", "#639922", "#534AB7", "#E8693C", "#0F8B8D",
    "#F4A261", "#2A9D8F", "#E76F51", "#264653", "#8ECAE6",
    "#FFB703", "#FB8500", "#6F42C1", "#20C997", "#FD7E14",
]

MAX_AGENTS = 2000
MAX_DEPTH = 5
CONCURRENCY_LIMIT = 25  # max concurrent LLM calls

# Global concurrency semaphore to avoid overwhelming the API
_llm_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
_agent_counter = 0

SWARM_PROMPT = """You are an autonomous research agent in a swarm intelligence engine.
You have been assigned a mission. You must research it with DEEP REASONING.

YOUR PROCESS:
1. **Analyze** — Break down the mission into sub-questions
2. **Review other agents' findings** (provided in context) — cite them as evidence
3. **Reason step-by-step** — Think through each aspect carefully
4. **Provide proof** — Every claim needs evidence: data points, citations, reasoning chains
5. **Cross-reference** — If other agents found relevant data, build on it
6. **Evaluate** — Score confidence based on evidence strength
7. **Decide on sub-agents** — Spawn specialized sub-agents for deep investigation

PROOF REQUIREMENTS:
- Every major claim must have supporting evidence (data points, sources, logic)
- Include specific numbers, percentages, or factual references where possible
- Cite other agents' findings when they support your analysis
- Acknowledge counter-evidence — don't just cherry-pick supporting data
- Distinguish between: confirmed facts, strong evidence, weak signals, and speculation

Your response must be valid JSON with these keys:
- reasoning (string): Your step-by-step reasoning process with evidence at each step
- findings (string): Your key findings and analysis
- evidence_points (array of strings): Specific proof items — data, facts, citations, sources
- score (float 0-1): How favorable/successful this looks
- confidence (float 0-1): How confident you are (based on evidence quality, not guesswork)
- risks (array of strings): Key risks with specific reasoning
- opportunities (array of strings): Key opportunities with specific reasoning
- cited_agents (array of strings OR null): IDs of any other agents you referenced (from the cross-reference section)
  IMPORTANT: If you used findings from other agents, list their IDs here
- sub_agent_missions (array of objects OR null): Sub-agents to spawn for deeper dives
  Each: { "name": "...", "mission": "specific focused research question" }
  Set to null if no sub-agents needed
"""

# Ultra-light prompt for deep sub-agents (depth 3+)
MICRO_AGENT_PROMPT = """You are a micro research agent. Answer a single focused question.

Output valid JSON with these keys:
- finding (string): One-sentence key finding
- evidence_points (array of strings): Up to 2 brief proof items
- score (float 0-1): How favorable/successful this looks
- confidence (float 0-1): How confident you are
- risks (array of strings): Up to 2 key risks (or [])
- opportunities (array of strings): Up to 2 key opportunities (or [])
"""


class SwarmAgent:
    """A fully autonomous swarm agent. Decides everything itself."""

    def __init__(self, name: str, mission: str, scenario: str,
                 parent_id: str = None, depth: int = 0, model: str = None,
                 factory: "SwarmFactory" = None, search_fn=None, news_fn=None,
                 tool_registry: ToolRegistry = None, micro: bool = False):
        self.id = uuid4().hex[:8]
        self.name = name
        self.mission = mission
        self.scenario = scenario
        self.parent_id = parent_id
        self.depth = depth
        self.model = model or "deepseek-v4-flash"
        self.factory = factory
        self.search_fn = search_fn
        self.news_fn = news_fn
        self.tool_registry = tool_registry
        self.tool_calls = []  # track tool calls for UI detail panel
        self.micro = micro or depth >= 3
        self.children: list["SwarmAgent"] = []
        self.status = "spawned"
        self.findings = ""
        self.reasoning = ""
        self.evidence_points = []
        self.score = 0.5
        self.confidence = 0.5
        self.risks = []
        self.opportunities = []
        self.searches = []  # track search queries and results

    async def run(self):
        """Execute the agent's mission autonomously."""
        global _agent_counter
        _agent_counter += 1

        # Check global cap
        if _agent_counter > MAX_AGENTS:
            self.status = "complete"
            return

        color = AGENT_COLORS[self.depth % len(AGENT_COLORS)]

        await bus.publish("agent_spawned", {
            "id": self.id,
            "type": "agent",
            "label": self.name,
            "hypothesis": self.mission[:80],
            "parent_id": self.parent_id,
            "depth": self.depth,
            "color": color,
            "micro": self.micro,
        })

        self.status = "researching"
        await bus.publish("agent_update", {
            "id": self.id, "status": "researching", "label": self.name
        })

        # === MICRO-AGENT MODE (depth 3+) ===
        if self.micro:
            messages = [
                {"role": "system", "content": MICRO_AGENT_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Context: {self.scenario[:300]}\n\n"
                        f"Question: {self.mission}\n\n"
                        "Provide key finding and score."
                    ),
                },
            ]

            async with _llm_semaphore:
                raw = await asyncio.to_thread(
                    call_llm, messages, model="deepseek-v4-flash",
                    temperature=0, max_tokens=512, use_cache=True,
                )
            parsed = self._parse_micro(raw)

            self.findings = parsed.get("finding", raw[:200])
            self.reasoning = ""
            self.evidence_points = parsed.get("evidence_points", [])
            self.score = self._safe_score(parsed.get("score", 0.5))
            self.confidence = self._safe_score(parsed.get("confidence", 0.5))
            self.risks = parsed.get("risks", [])
            self.opportunities = parsed.get("opportunities", [])
            # No sub-agents in micro mode
        else:
            # === FULL AGENT MODE (depth 1-2) ===
            # Gather research context — blackboard + tools
            context = self.mission

            # Read from shared blackboard (other agents' findings)
            memory = board.get_memory_context(self.mission, exclude_id=self.id, max_chars=1500)
            if memory:
                context += memory

            # Build tool registry from old-style search_fn/news_fn if no registry provided
            if not self.tool_registry and (self.search_fn or self.news_fn):
                self.tool_registry = ToolRegistry()
                if self.search_fn:
                    self.tool_registry.register(BuiltinTool(
                        fn=self.search_fn, name="search_web",
                        description="Search the live web for current information.",
                        input_schema={
                            "type": "object",
                            "properties": {"query": {"type": "string", "description": "Search query"}},
                            "required": ["query"],
                        },
                    ))
                if self.news_fn:
                    self.tool_registry.register(BuiltinTool(
                        fn=self.news_fn, name="search_news",
                        description="Search recent news articles.",
                        input_schema={
                            "type": "object",
                            "properties": {"query": {"type": "string", "description": "News query"}},
                            "required": ["query"],
                        },
                    ))

            # Build tool manifest for the agent's system prompt
            tool_manifest = ""
            if self.tool_registry:
                tool_manifest = self.tool_registry.get_manifest()

            # Build initial messages
            messages = [
                {"role": "system", "content": SWARM_PROMPT + tool_manifest},
                {
                    "role": "user",
                    "content": (
                        f"Overall Scenario: {self.scenario}\n\n"
                        f"Your Mission: {self.mission}\n\n"
                        f"Depth Level: {self.depth}\n"
                        f"{'Research Context:' + context if context != self.mission else ''}\n\n"
                        "Research this mission deeply. Use available tools to gather real-world data. "
                        "When you have enough evidence, produce your final JSON analysis."
                    ),
                },
            ]

            # === TOOL-CALLING LOOP ===
            MAX_TOOL_CALLS = 5
            tool_call_count = 0
            raw = ""

            while tool_call_count < MAX_TOOL_CALLS:
                async with _llm_semaphore:
                    raw = await asyncio.to_thread(
                        call_llm, messages, model=self.model, temperature=0.4,
                    )

                # Check for tool calls in the response
                tool_calls = extract_tool_calls(raw)

                if not tool_calls:
                    # No tool calls — this is the final analysis, break out
                    break

                # Execute each tool call
                results_text = ""
                for tc in tool_calls:
                    tool_name = tc.get("tool", "")
                    args = tc.get("args", {})

                    # Publish tool_call event
                    await bus.publish("tool_call", {
                        "agent_id": self.id,
                        "agent_name": self.name,
                        "tool_name": tool_name,
                        "args": args,
                    })

                    result = await self.tool_registry.execute(
                        tool_name, agent_id=self.id, **args,
                    )

                    # Publish tool_result event
                    await bus.publish("tool_result", {
                        "agent_id": self.id,
                        "agent_name": self.name,
                        "tool_name": tool_name,
                        "success": result.success,
                        "output_preview": result.output[:200],
                        "duration_ms": result.duration_ms,
                        "error": result.error,
                    })

                    # Track for UI detail panel
                    self.tool_calls.append({
                        "tool_name": tool_name,
                        "args": args,
                        "success": result.success,
                        "duration_ms": result.duration_ms,
                        "error": result.error,
                    })

                    # Track search queries for backward compat
                    if tool_name in ("search_web", "search_news"):
                        query_str = args.get("query", self.mission)[:100]
                        self.searches.append(f"🔧 {tool_name}: {query_str}")
                        if result.success:
                            line_count = len([l for l in result.output.split("\n") if l.strip()])
                            self.searches.append(f"  → {line_count} results found")
                        else:
                            self.searches.append(f"  → Failed: {(result.error or '')[:60]}")
                    else:
                        self.searches.append(f"🔧 {tool_name}({json.dumps(args)[:80]})")
                        status = "OK" if result.success else "FAIL"
                        self.searches.append(f"  → {status} ({result.duration_ms:.0f}ms)")

                    # Inject result into conversation
                    results_text += (
                        f"\n\n--- Tool Result: {tool_name} ---\n"
                        f"{result.output[:3000]}"
                        f"\n--- End Tool Result ---\n"
                    )

                # Add assistant response + tool results to conversation
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": (
                    f"Here are the results of your tool calls:\n{results_text}\n\n"
                    "Continue your analysis. Call more tools if needed, or produce "
                    "your final JSON analysis if you have enough information."
                )})
                tool_call_count += 1

            # Parse the final response (may contain tool_call blocks from last iteration)
            parsed = self._parse(raw)

            self.findings = parsed.get("findings", raw[:300])
            self.reasoning = parsed.get("reasoning", "")
            self.evidence_points = parsed.get("evidence_points", [])
            self.score = self._safe_score(parsed.get("score", 0.5))
            self.confidence = self._safe_score(parsed.get("confidence", 0.5))
            self.risks = parsed.get("risks", [])
            self.opportunities = parsed.get("opportunities", [])

            # Track citations to other agents
            cited = parsed.get("cited_agents", [])
            if cited and isinstance(cited, list):
                for cid in cited:
                    if isinstance(cid, str) and cid.strip():
                        board.cite(self.id, cid.strip())

            # Agent decides: does it need sub-agents? (max depth check)
            sub_missions = parsed.get("sub_agent_missions")
            can_spawn = (
                sub_missions and isinstance(sub_missions, list)
                and len(sub_missions) > 0
                and self.depth < MAX_DEPTH
                and _agent_counter < MAX_AGENTS
            )
            if can_spawn:
                tasks = []
                # Fewer sub-agents at deeper levels
                sub_cap = 4 if self.depth >= 2 else 8
                for sm in sub_missions[:sub_cap]:
                    sub_name = sm.get("name", f"Sub-{len(self.children)+1}")
                    sub_mission = sm.get("mission", sm.get("description", self.mission))
                    child = SwarmAgent(
                        name=sub_name,
                        mission=sub_mission,
                        scenario=self.scenario,
                        parent_id=self.id,
                        depth=self.depth + 1,
                        model=self.model,
                        factory=self.factory,
                        tool_registry=self.tool_registry,
                    )
                    self.children.append(child)
                    if self.factory:
                        self.factory.register(child)
                    tasks.append(child.run())

                if tasks:
                    await bus.publish("agent_update", {
                        "id": self.id,
                        "status": "spawning",
                        "label": self.name,
                        "detail": f"Spawning {len(tasks)} sub-agents",
                    })
                    await asyncio.gather(*tasks)

        # Publish to shared blackboard for other agents to cite
        board.publish(self.id, {
            "label": self.name,
            "mission": self.mission,
            "findings": self.findings,
            "reasoning": self.reasoning,
            "evidence_points": self.evidence_points,
            "score": self.score,
            "confidence": self.confidence,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "micro": self.micro,
        })

        self.status = "complete"
        await bus.publish("agent_complete", {
            "id": self.id,
            "label": self.name,
            "mission": self.mission[:100],
            "score": self.score,
            "confidence": self.confidence,
            "findings": str(self.findings)[:400],
            "reasoning": str(self.reasoning)[:500] if not self.micro else "",
            "evidence_points": self.evidence_points[:5],
            "risks": self.risks[:5],
            "opportunities": self.opportunities[:5],
            "children_count": len(self.children),
            "micro": self.micro,
            "searches": self.searches[:8],
            "tool_calls": self.tool_calls[:10],
        })

    def _parse(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"findings": raw[:300], "score": 0.5, "confidence": 0.3,
                    "risks": [], "opportunities": [], "sub_agent_missions": None}

    def _parse_micro(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"finding": raw[:200], "score": 0.5, "confidence": 0.3}

    def _safe_score(self, val):
        if isinstance(val, (int, float)):
            return min(1.0, max(0.0, float(val)))
        if isinstance(val, dict):
            vals = [v for v in val.values() if isinstance(v, (int, float))]
            return sum(vals) / len(vals) if vals else 0.5
        return 0.5

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "mission": self.mission,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "status": self.status,
            "score": self.score,
            "confidence": self.confidence,
            "findings": str(self.findings)[:400],
            "reasoning": str(self.reasoning)[:500],
            "evidence_points": self.evidence_points[:5],
            "risks": self.risks[:5],
            "opportunities": self.opportunities[:5],
            "children": [c.to_dict() for c in self.children],
            "micro": self.micro,
            "searches": self.searches[:8],
        }


class SwarmFactory:
    """Manages the entire swarm — tracks agents, metrics, and cleanup."""

    def __init__(self, model: str = None, search_fn=None, news_fn=None,
                 tool_registry: ToolRegistry = None, scenario: str = ""):
        self.model = model
        self.search_fn = search_fn
        self.news_fn = news_fn
        self.tool_registry = tool_registry
        self.scenario = scenario
        self.agents: dict[str, SwarmAgent] = {}
        self.total_spawned = 0

    def register(self, agent: SwarmAgent):
        """Register an agent with the factory."""
        self.agents[agent.id] = agent
        self.total_spawned += 1

    async def create_root_swarm(self, seed: dict) -> list[SwarmAgent]:
        """Create the root swarm from a seed. Returns root agents."""
        global _agent_counter
        _agent_counter = 0  # Reset counter for new run
        domains = seed.get("agent_domains", [])
        if not domains:
            domains = [{"name": "Analysis", "description": seed.get("summary", self.scenario), "priority": 1.0}]

        roots = []
        tasks = []

        for i, domain in enumerate(domains):
            name = domain.get("name", f"Agent-{i+1}")
            mission = domain.get("description", domain.get("mission", self.scenario))
            priority = domain.get("priority", 0.5)

            agent = SwarmAgent(
                name=name,
                mission=mission,
                scenario=self.scenario,
                depth=1,
                model=self.model,
                factory=self,
                tool_registry=self.tool_registry,
            )
            self.register(agent)
            roots.append(agent)

        # Publish all roots before starting
        await bus.publish("swarm_init", {
            "root_count": len(roots),
            "total_agents": len(self.agents),
            "domains": [d.get("name") for d in domains],
        })

        return roots

    def get_all_agents_flat(self) -> list[dict]:
        """Get all agents as a flat list for storage."""
        all_a = []
        def walk(agent):
            all_a.append(agent.to_dict())
            for c in agent.children:
                walk(c)
        for a in self.agents.values():
            if a.parent_id is None:  # only walk root agents
                walk(a)
        return all_a

    def get_swarm_stats(self) -> dict:
        """Get aggregate swarm statistics."""
        completed = sum(1 for a in self.agents.values() if a.status == "complete")
        researching = sum(1 for a in self.agents.values() if a.status == "researching")
        spawned = sum(1 for a in self.agents.values() if a.status == "spawned")
        return {
            "total": len(self.agents),
            "completed": completed,
            "researching": researching,
            "spawned": spawned,
        }

    def get_aggregate_scores(self) -> tuple[float, float, list[str], list[str]]:
        """Average scores and collect risks/opportunities from completed agents."""
        root_agents = [a for a in self.agents.values() if a.depth == 1]

        scores = [a.score for a in root_agents if a.status == "complete"]
        confs = [a.confidence for a in root_agents if a.status == "complete"]

        avg_score = sum(scores) / len(scores) if scores else 0.5
        avg_conf = sum(confs) / len(confs) if confs else 0.5

        all_risks = []
        all_opps = []
        for a in self.agents.values():
            all_risks.extend(a.risks or [])
            all_opps.extend(a.opportunities or [])

        return avg_score, avg_conf, all_risks[:10], all_opps[:10]

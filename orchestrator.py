"""
Minimal orchestrator — extracts seed, creates swarm, lets agents self-organize.
"""

import os
import json
import asyncio
from datetime import datetime, timezone

from llm import call_llm
from seed import extract_seed
from agents import SwarmFactory
from debate import run_debate
from simulation import generate_scenarios
from report import generate_report
from events import bus
from memory import init_run, save_json


async def run_orchestration_stream(
    goal: str,
    constraints: str = "",
    timeline: str = "",
    risk_tolerance: str = "medium",
    model: str = None,
    search_fn=None,
    tool_registry=None,
):
    """Full autonomous swarm orchestration with event streaming."""

    orch_model = model or os.getenv("ORCHESTRATOR_MODEL", "deepseek-v4-pro")
    agent_model = model or os.getenv("AGENT_MODEL", "deepseek-v4-flash")

    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")
    try:
        run_dir = init_run(run_id)
    except Exception as e:
        await bus.publish("status", {"message": f"Init failed: {e}", "pct": 0})
        await bus.publish("complete", {})
        return

    context = f"Risk Tolerance: {risk_tolerance}"
    if constraints:
        context += f" | Constraints: {constraints}"
    if timeline:
        context += f" | Timeline: {timeline}"

    await bus.publish("status", {"message": "Extracting seed from scenario...", "pct": 5})

    # Step 1: Extract seed — determines how many agents, what domains, etc.
    seed = await extract_seed(goal, orch_model)
    domain_count = len(seed.get("agent_domains", []))
    await bus.publish("status", {"message": f"Seed extracted — {domain_count} domains identified", "pct": 10})

    # Step 2: Create the swarm — agents self-organize from here
    from search import search_news
    swarm = SwarmFactory(
        model=agent_model,
        search_fn=search_fn if not tool_registry else None,
        news_fn=search_news if not tool_registry else None,
        tool_registry=tool_registry,
        scenario=goal,
    )
    roots = await swarm.create_root_swarm(seed)

    await bus.publish("status", {
        "message": f"Swarm initiated — {len(roots)} root agents spawning...",
        "pct": 15,
    })

    # Step 3: Run all root agents in parallel — they autonomously spawn sub-agents
    async def run_roots():
        tasks = [agent.run() for agent in roots]
        await asyncio.gather(*tasks)

    await run_roots()

    stats = swarm.get_swarm_stats()

    # Send graph edges (all interconnections) to UI
    from blackboard import board
    edges = board.get_all_edges()
    await bus.publish("graph_edges", {
        "edges": edges[:200],
        "total_agents": stats['total'],
        "edge_count": len(edges),
    })

    await bus.publish("status", {
        "message": f"Swarm complete — {stats['total']} total agents ({stats['completed']} completed, {len(edges)} connections)",
        "pct": 50,
    })

    # Step 4: Save all agent data
    all_agents = swarm.get_all_agents_flat()
    save_json(run_dir, "agents.json", all_agents)

    # Step 5: Prepare agent outputs for debate/simulation
    root_dicts = [a.to_dict() for a in roots]

    # Step 6: Run debate
    await bus.publish("status", {"message": "Agents debating findings...", "pct": 55})
    debate_result = await run_debate(root_dicts, goal, orch_model)
    save_json(run_dir, "debate.json", debate_result)

    await bus.publish("debate_done", {"result": debate_result})
    await bus.publish("status", {"message": "Running simulation engine...", "pct": 65})

    # Step 7: Simulation
    avg_score, avg_conf, top_risks, top_opps = swarm.get_aggregate_scores()
    try:
        scenarios = await generate_scenarios(root_dicts, goal, context, orch_model)
    except Exception:
        scenarios = {"scenarios": [
            {"scenario": "optimistic", "probability": min(0.9, avg_score + 0.15),
             "key_events": ["See full report"], "timeline": timeline or "Unknown",
             "success_probability": min(0.9, avg_score + 0.15),
             "failure_probability": min(0.9, 1 - avg_score),
             "pivot_probability": 0.15},
            {"scenario": "realistic", "probability": avg_score,
             "key_events": ["See full report"], "timeline": timeline or "Unknown",
             "success_probability": avg_score,
             "failure_probability": min(0.9, 1 - avg_score),
             "pivot_probability": 0.15},
            {"scenario": "catastrophic", "probability": min(0.9, 1 - avg_score - 0.15),
             "key_events": ["See full report"], "timeline": timeline or "Unknown",
             "success_probability": max(0.05, avg_score - 0.3),
             "failure_probability": min(0.9, 1 - avg_score + 0.3),
             "pivot_probability": 0.25},
        ]}
    save_json(run_dir, "simulation.json", scenarios)

    await bus.publish("simulation_done", {"scenarios": scenarios.get("scenarios", [])})
    await bus.publish("status", {"message": "Synthesizing final verdict...", "pct": 80})

    # Step 8: Final synthesis
    verdict = await _synthesize(
        goal, context, root_dicts, debate_result, scenarios,
        avg_score, avg_conf, top_risks, orch_model,
    )
    verdict["run_id"] = run_id
    verdict["goal"] = goal
    verdict["model_used"] = orch_model
    verdict["agent_model"] = agent_model
    verdict["swarm_stats"] = stats
    save_json(run_dir, "verdict.json", verdict)

    # Step 9: Generate report
    report_path = generate_report(verdict, root_dicts, debate_result, scenarios, run_dir)

    await bus.publish("verdict_ready", {"verdict": verdict, "report_path": report_path})
    await bus.publish("status", {"message": "Complete!", "pct": 100})
    await bus.publish("complete", {})
    await asyncio.sleep(0.1)


async def _synthesize(goal, context, agent_outputs, debate_result, scenarios,
                      avg_score, avg_conf, top_risks, model):
    agent_summary = json.dumps(agent_outputs, indent=2)[:4000]
    debate_summary = json.dumps(debate_result, indent=2)[:3000]
    scenarios_summary = json.dumps(scenarios, indent=2)[:3000]
    all_risks = "\n".join(f"- {r}" for r in top_risks[:5])
    all_opps = []
    for a in agent_outputs:
        all_opps.extend(a.get("opportunities", [])[:2])

    messages = [
        {
            "role": "system",
            "content": (
                "You are the Final Synthesis Engine for a swarm intelligence prediction system. "
                "Multiple autonomous agents have researched this scenario, debated findings, and "
                "run probabilistic simulations. Your job is to produce the definitive final forecast.\n\n"
                "Your verdict must be comprehensive, actionable, and brutally honest. "
                "Go beyond summary — produce a full intelligence forecast. Output valid JSON with:\n\n"
                "CORE VERDICT:\n"
                "- overall_success_probability (0.0-1.0)\n"
                "- decision: 'GO' | 'NO-GO' | 'CONDITIONAL-GO'\n"
                "- decision_rationale (string): 2-3 sentences\n"
                "- probability_breakdown (object: optimistic, realistic, pessimistic — each 0.0-1.0)\n"
                "- confidence_level: 'HIGH' | 'MEDIUM' | 'LOW'\n\n"
                "FORECAST:\n"
                "- predicted_developments (array of 5-8 objects): each with {timeframe (string), event (string), probability (0.0-1.0), evidence (string — what supports this), signals_to_watch (string — what would confirm or refute)}\n"
                "- key_actors (array of 4-8 objects): entities/forces with {name, type (string like 'competitor','regulator','market','technology','individual'), influence (0.0-1.0 — how much they shape outcomes), stance ('enabler'|'blocker'|'neutral'), summary (1-sentence role)}\n"
                "- evidence_lines (array of 5-10 objects): {claim (string), evidence_for (array of strings), evidence_against (array of strings), verdict ('supported'|'weak'|'contested')}\n"
                "- narrative_forecast (string): 400-800 word narrative — tell the story of what will most likely happen, from start to finish, weaving in agent findings, debate conclusions, and scenario analysis. Write like an intelligence brief, not a summary.\n\n"
                "RISKS & MITIGATION:\n"
                "- top_risks (list of 3-5 critical risks, each a detailed sentence)\n"
                "- risk_mitigation (object mapping each risk to a specific mitigation)\n\n"
                "ACTION PLAN:\n"
                "- recommended_path (string): specific step-by-step plan (300-500 chars)\n"
                "- key_milestones (list of 5 objects with {week, action, success_criteria})\n\n"
                "SYNTHESIS:\n"
                "- summary (string): executive summary paragraph\n"
                "- key_insights (list of 3-5 non-obvious insights)\n"
                "- critical_assumptions (list of 3-5 — if wrong, change the answer)\n"
                "- what_would_change_the_answer (string): single biggest factor that flips the decision\n\n"
                "Output valid JSON only. No markdown. No code fences."
            ),
        },
        {
            "role": "user",
            "content": (
                f"GOAL: {goal}\n\n"
                f"CONTEXT: {context}\n\n"
                f"=== AGENT RESEARCH ({len(agent_outputs)} agents) ===\n"
                f"{agent_summary}\n\n"
                f"=== DEBATE RESULTS ===\n"
                f"{debate_summary}\n\n"
                f"=== SCENARIO SIMULATIONS ===\n"
                f"{scenarios_summary}\n\n"
                f"=== AGGREGATE METRICS ===\n"
                f"Average Score: {avg_score:.2f}\n"
                f"Average Confidence: {avg_conf:.2f}\n"
                f"Top Risks Identified:\n{all_risks}\n\n"
                "Produce the definitive intelligence forecast. Be specific, evidence-based, "
                "and honest. Include predicted developments with timeframes, key actors, "
                "evidence lines showing what supports each major claim, and a compelling "
                "narrative forecast that tells the full story."
            ),
        },
    ]

    raw = await asyncio.to_thread(call_llm, messages, model, True, 16384, 0.3)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        result = json.loads(cleaned)
        result["goal"] = goal
        result["model_used"] = model
        return result
    except json.JSONDecodeError:
        return {
            "goal": goal,
            "overall_success_probability": avg_score,
            "decision": "CONDITIONAL-GO" if avg_score > 0.3 else "NO-GO",
            "decision_rationale": f"Based on aggregate agent score of {avg_score:.2f}",
            "probability_breakdown": {"optimistic": min(1.0, avg_score + 0.15), "realistic": avg_score, "pessimistic": max(0.05, avg_score - 0.15)},
            "top_risks": top_risks[:5],
            "risk_mitigation": {},
            "recommended_path": raw[:500] if raw else "See agent analyses for detailed recommendations.",
            "key_milestones": [],
            "summary": "Analysis complete. See full report for details.",
            "key_insights": [],
            "critical_assumptions": [],
            "what_would_change_the_answer": "Higher quality evidence and real-world data validation.",
            "confidence_level": "MEDIUM" if avg_conf > 0.4 else "LOW",
            "predicted_developments": [],
            "key_actors": [],
            "evidence_lines": [],
            "narrative_forecast": raw[:1000] if raw else "See agent analyses for forecast details.",
            "model_used": model,
        }

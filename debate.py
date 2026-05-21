"""
Debate engine — agents challenge each other's findings.
2-3 rounds of structured challenge. Short responses (max 200 tokens).
"""

import asyncio
import json
from llm import call_llm


DEBATE_PROMPT = """You are a Debate Moderator. You have agent analyses of a business goal.
Your job is to surface disagreements, challenge assumptions, and reach consensus.

Round rules:
- Risk Agent attacks optimism: "Your market timing assumption is wrong because..."
- Strategy Agent defends: "Here's why the timing works despite those risks..."
- Finance Agent provides reality check: "The math works/doesn't work because..."
- Trend Agent arbitrates: "The trend signal supports/contradicts because..."

After each challenge, the challenged agent responds with counter-arguments.

Output the agreed facts, unresolved disagreements, and final consensus confidence.

Keep everything SHORT. Max 200 tokens per response.
Return valid JSON with keys: agreed_facts, disagreements, final_confidence, model_used.
"""


async def run_debate(agent_outputs: list[dict], goal: str, model: str = None) -> dict:
    """Run a multi-round debate between agents with structured challenges."""

    findings_text = _format_for_debate(agent_outputs)

    messages = [
        {"role": "system", "content": DEBATE_PROMPT},
        {
            "role": "user",
            "content": f"Goal: {goal}\n\nAgent Analyses:\n{findings_text}\n\nRun the debate and reach consensus.",
        },
    ]

    raw = await asyncio.to_thread(call_llm, messages, model, False, 4096, 0.5)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]

    try:
        result = json.loads(cleaned)
        result["model_used"] = model
        return result
    except json.JSONDecodeError:
        return {
            "agreed_facts": [raw[:500]],
            "disagreements": [],
            "final_confidence": 0.5,
            "model_used": model,
            "raw_debate": raw,
        }


def _format_for_debate(agent_outputs: list[dict]) -> str:
    lines = []
    for a in agent_outputs:
        name = a.get("name", a.get("type", a.get("agent", "Agent")))
        mission = a.get("mission", a.get("hypothesis", ""))
        score = a.get("score", "N/A")
        conf = a.get("confidence", "N/A")
        risks = a.get("risks", [])
        opps = a.get("opportunities", [])
        line = f"{name}:\n  Score: {score} | Confidence: {conf}"
        if mission:
            line += f"\n  Mission: {str(mission)[:100]}"
        if risks:
            line += f"\n  Risks: {', '.join(str(r)[:80] for r in (risks or [])[:3])}"
        if opps:
            line += f"\n  Opportunities: {', '.join(str(o)[:80] for o in (opps or [])[:3])}"
        lines.append(line)
    return "\n\n".join(lines)

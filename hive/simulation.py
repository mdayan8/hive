"""
Scenario generation + probability scoring.
Generates 3 scenarios: optimistic, realistic, catastrophic.
"""

import asyncio
import json
import re
from .llm import call_llm
from .prompts import load_prompt


async def generate_scenarios(agent_outputs: list[dict], goal: str, context: str, model: str = None) -> dict:
    """Generate 3 probability-weighted scenarios from agent outputs."""
    scores = [_safe_float(a.get("score", 0.5)) for a in agent_outputs]
    confidences = [_safe_float(a.get("confidence", 0.5)) for a in agent_outputs]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    avg_score = sum(scores) / len(scores) if scores else 0.5

    findings_text = _summarize_findings(agent_outputs)

    prompt = load_prompt("simulation")
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Goal: {goal}\n\n"
                f"Context: {context}\n\n"
                f"Agent Findings:\n{findings_text}\n\n"
                f"Aggregate Score: {avg_score:.2f}\n"
                f"Average Confidence: {avg_confidence:.2f}\n\n"
                f"Generate 3 scenarios."
            ),
        },
    ]

    raw = await asyncio.to_thread(call_llm, messages, model, True, 4096, 0.7)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "scenarios": [
                {
                    "scenario": "optimistic",
                    "probability": _clamp(avg_score + 0.15, 0.1, 0.9),
                    "key_events": ["See full report"],
                    "timeline": context or "Unknown",
                    "success_probability": _clamp(avg_score + 0.15, 0.1, 0.9),
                    "failure_probability": _clamp(1 - avg_score - 0.15, 0.1, 0.9),
                    "pivot_probability": 0.15,
                },
                {
                    "scenario": "realistic",
                    "probability": _clamp(avg_score, 0.1, 0.9),
                    "key_events": ["See full report"],
                    "timeline": context or "Unknown",
                    "success_probability": _clamp(avg_score, 0.1, 0.9),
                    "failure_probability": _clamp(1 - avg_score, 0.1, 0.9),
                    "pivot_probability": 0.15,
                },
                {
                    "scenario": "catastrophic",
                    "probability": _clamp(1 - avg_score - 0.15, 0.1, 0.9),
                    "key_events": ["See full report"],
                    "timeline": context or "Unknown",
                    "success_probability": _clamp(avg_score - 0.3, 0.05, 0.5),
                    "failure_probability": _clamp(1 - avg_score + 0.3, 0.1, 0.9),
                    "pivot_probability": 0.25,
                },
            ],
        }


def _summarize_findings(agent_outputs: list[dict]) -> str:
    lines = []
    for a in agent_outputs:
        name = a.get("name", a.get("type", a.get("agent", "Unknown")))
        findings = str(a.get("findings") or a.get("mission") or a.get("hypothesis", a.get("status", "")))
        score = a.get("score", "N/A")
        confidence = a.get("confidence", "N/A")
        risks = a.get("risks", [])
        opportunities = a.get("opportunities", [])
        lines.append(
            f"--- {name} ---\n"
            f"Findings: {findings[:200]}\n"
            f"Score: {score} | Confidence: {confidence}\n"
            f"Risks: {_fmt_list(risks)}\n"
            f"Opportunities: {_fmt_list(opportunities)}"
        )
    return "\n\n".join(lines)


def _fmt_list(items):
    return ", ".join(str(i)[:60] for i in (items or [])[:3])


def _safe_float(val, default=0.5):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        vals = [v for v in val.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else default
    return default


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

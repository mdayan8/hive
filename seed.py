"""
Seed extractor — the entry point that analyzes a scenario and determines:
- Key entities (people, companies, concepts, factors)
- Critical variables (what could change)
- Relationships between entities
- The optimal number and type of agents to spawn

This replaces hardcoded agent types with dynamic determination.
"""

import asyncio
import json
from llm import call_llm
from prompts import load_prompt


async def extract_seed(scenario: str, model: str = None) -> dict:
    """
    Extract seed from a scenario. Returns:
    {
        "entities": [...],
        "variables": [...],
        "relationships": [...],
        "agent_domains": [...]  # dynamically determined
    }
    """
    prompt = load_prompt("seed_extractor")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Analyze this scenario and extract its seed: {scenario}"},
    ]

    raw = await asyncio.to_thread(call_llm, messages, model, False, 4096, 0.3)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]

    try:
        result = json.loads(cleaned)
        # Ensure we have the required fields
        if "agent_domains" not in result:
            result["agent_domains"] = result.get("research_domains", [])
        return result
    except json.JSONDecodeError:
        # Fallback: create seed from raw output
        return {
            "summary": scenario,
            "entities": [],
            "variables": [{"name": "outcome", "type": "binary", "description": "Success or failure"}],
            "relationships": [],
            "agent_domains": [
                {
                    "name": "Core Analysis",
                    "description": f"Analyze the core dynamics of: {scenario}",
                    "priority": 1.0,
                }
            ],
        }

"""
Shared blackboard — agents publish findings here for other agents to read.
Creates cross-references, evidence chains, and a living knowledge graph.
"""

import json
import time


class Blackboard:
    """Global shared memory where all agents read/write findings.
    Agents can cite each other's work, building a true interconnected knowledge graph."""

    def __init__(self):
        self.findings: dict[str, dict] = {}  # agent_id -> finding
        self.citations: dict[str, list[str]] = {}  # agent_id -> [cited_agent_ids]
        self.timeline: list[dict] = []  # ordered list of all findings

    def publish(self, agent_id: str, data: dict):
        """An agent publishes its finding to the shared blackboard."""
        entry = {
            "agent_id": agent_id,
            "agent_name": data.get("label", agent_id[:8]),
            "mission": data.get("mission", ""),
            "findings": data.get("findings", ""),
            "reasoning": data.get("reasoning", ""),
            "evidence_points": data.get("evidence_points", []),
            "score": data.get("score", 0.5),
            "confidence": data.get("confidence", 0.5),
            "risks": data.get("risks", []),
            "opportunities": data.get("opportunities", []),
            "depth": data.get("depth", 0),
            "parent_id": data.get("parent_id", ""),
            "timestamp": time.time(),
        }
        self.findings[agent_id] = entry
        self.timeline.append(entry)

    def get_finding(self, agent_id: str) -> dict | None:
        return self.findings.get(agent_id)

    def get_timeline(self, limit: int = 20) -> list[dict]:
        """Get most recent findings across all agents."""
        return self.timeline[-limit:]

    def get_related(self, mission_keywords: str, exclude_id: str = "", limit: int = 10) -> list[dict]:
        """Find findings related to a mission by keyword matching."""
        keywords = mission_keywords.lower().split()[:10]
        scored = []
        for aid, entry in self.findings.items():
            if aid == exclude_id:
                continue
            text = (entry.get("mission", "") + " " + entry.get("findings", "")).lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:limit]]

    def cite(self, agent_id: str, cited_id: str):
        """Record that one agent cited another's finding."""
        if agent_id not in self.citations:
            self.citations[agent_id] = []
        if cited_id not in self.citations[agent_id]:
            self.citations[agent_id].append(cited_id)

    def get_all_edges(self) -> list[tuple[str, str, str]]:
        """Get all graph edges: parent-child + citation links.
        Returns list of (source_id, target_id, type)."""
        edges = set()

        # Parent-child edges from findings
        for aid, entry in self.findings.items():
            parent = entry.get("parent_id", "")
            if parent and parent in self.findings:
                edges.add((parent, aid, "parent"))

        # Citation edges
        for agent_id, cited_list in self.citations.items():
            for cited_id in cited_list:
                if cited_id in self.findings:
                    edges.add((agent_id, cited_id, "cite"))

        # Sibling edges (share a parent)
        by_parent: dict[str, list[str]] = {}
        for aid, entry in self.findings.items():
            parent = entry.get("parent_id", "")
            if parent:
                if parent not in by_parent:
                    by_parent[parent] = []
                by_parent[parent].append(aid)
        for parent, siblings in by_parent.items():
            for i in range(len(siblings)):
                for j in range(i + 1, len(siblings)):
                    edges.add((siblings[i], siblings[j], "sibling"))

        return list(edges)

    def get_memory_context(self, agent_mission: str, exclude_id: str = "", max_chars: int = 2000) -> str:
        """Generate context from related findings for an agent's prompt."""
        related = self.get_related(agent_mission, exclude_id, limit=8)
        if not related:
            return ""

        parts = ["\n\n--- Other Agents' Findings (cross-reference) ---"]
        for entry in related:
            name = entry.get("agent_name", "Unknown")
            findings = str(entry.get("findings", ""))[:200]
            evidence = entry.get("evidence_points", [])
            ev_str = "; ".join(str(e)[:80] for e in evidence[:2])
            parts.append(f"📌 {name}: {findings}")
            if ev_str:
                parts.append(f"   Evidence: {ev_str}")

        context = "\n".join(parts)
        return context[:max_chars]


# Global singleton
board = Blackboard()

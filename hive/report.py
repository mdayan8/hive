"""
Report generation — produces comprehensive markdown report from run data.
"""
from pathlib import Path


def generate_report(verdict: dict, agent_outputs: list, debate: dict, scenarios: dict, run_dir: Path) -> str:
    """Generate markdown report in the run directory. Returns report path."""
    md = _build_markdown(verdict, agent_outputs, debate, scenarios)
    report_path = run_dir / "report.md"
    report_path.write_text(md)
    print(f"[report] Saved: {report_path}")
    return str(report_path)


def _build_markdown(verdict, agent_outputs, debate, scenarios):
    goal = verdict.get("goal", "Unknown goal")
    prob = verdict.get("overall_success_probability", 0.5)
    if isinstance(prob, (int, float)):
        prob_pct = f"{prob * 100:.0f}%"
    else:
        prob_pct = str(prob)
    decision = verdict.get("decision", "N/A")
    decision_emoji = {"GO": "🟢", "NO-GO": "🔴", "CONDITIONAL-GO": "🟡"}.get(decision, "")
    decision_rationale = verdict.get("decision_rationale", "")
    summary = verdict.get("summary", "")
    risks = verdict.get("top_risks", [])
    mitigation = verdict.get("risk_mitigation", {})
    path = verdict.get("recommended_path", "")
    milestones = verdict.get("key_milestones", [])
    insights = verdict.get("key_insights", [])
    assumptions = verdict.get("critical_assumptions", [])
    change_factor = verdict.get("what_would_change_the_answer", "")
    confidence = verdict.get("confidence_level", "MEDIUM")
    model_used = verdict.get("model_used", "unknown")
    swarm_stats = verdict.get("swarm_stats", {})
    pb = verdict.get("probability_breakdown", {})

    lines = [
        "# RealWorld Simulator — Comprehensive Analysis Report",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Goal:** {goal}",
        f"**Model:** {model_used}",
        f"**Run ID:** {verdict.get('run_id', 'N/A')}",
        f"**Swarm:** {swarm_stats.get('total', '?')} agents | {swarm_stats.get('completed', '?')} completed",
        "",
        f"### Decision: {decision_emoji} {decision}",
        f"> {decision_rationale}" if decision_rationale else "",
        "",
        f"**Overall Success Probability:** `{prob_pct}`",
        f"**Confidence Level:** `{confidence}`",
        "",
        f"**Summary:** {summary}",
        "",
    ]

    # Probability breakdown
    if pb:
        lines.append("### Probability Distribution")
        lines.append("")
        for label, val in pb.items():
            bar = _make_bar(val)
            lines.append(f"| {label.title():<15} | {bar} | `{val*100:.0f}%` |")
        lines.append("")

    # Decision & path
    if path:
        lines.append("### Recommended Action Plan")
        lines.append("")
        lines.append(f"> {path}")
        lines.append("")

    # Milestones
    if milestones:
        lines.append("### Key Milestones")
        lines.append("")
        if isinstance(milestones[0], dict):
            lines.append("| Week | Action | Success Criteria |")
            lines.append("|------|--------|------------------|")
            for m in milestones:
                week = m.get("week", "?")
                action = m.get("action", str(m))
                criteria = m.get("success_criteria", "-")
                lines.append(f"| {week} | {action} | {criteria} |")
        else:
            for i, m in enumerate(milestones, 1):
                lines.append(f"{i}. {m}")
        lines.append("")

    # Risk matrix with mitigation
    if risks:
        lines.append("---")
        lines.append("")
        lines.append("## Risk Matrix")
        lines.append("")
        lines.append("| # | Risk | Mitigation |")
        lines.append("|---|------|------------|")
        for i, r in enumerate(risks, 1):
            mit = mitigation.get(r, mitigation.get(str(i - 1), "-"))
            lines.append(f"| {i} | {str(r)[:120]} | {str(mit)[:120]} |")
        lines.append("")

    # Critical assumptions
    if assumptions:
        lines.append("### Critical Assumptions")
        lines.append("")
        lines.append("These assumptions, if wrong, could invalidate the analysis:")
        lines.append("")
        for a in assumptions:
            lines.append(f"- **{a}**")
        lines.append("")

    # What would change the answer
    if change_factor:
        lines.append("### Tipping Point")
        lines.append("")
        lines.append(f"> **What would most likely change this verdict:** {change_factor}")
        lines.append("")

    # Narrative forecast
    narrative = verdict.get("narrative_forecast", "")
    if narrative:
        lines.append("---")
        lines.append("")
        lines.append("## Intelligence Forecast")
        lines.append("")
        lines.append(narrative)
        lines.append("")

    # Predicted developments
    developments = verdict.get("predicted_developments", [])
    if developments:
        lines.append("### Predicted Developments Timeline")
        lines.append("")
        lines.append("| Timeframe | Event | Probability | Evidence |")
        lines.append("|-----------|-------|-------------|----------|")
        for d in developments:
            tf = d.get("timeframe", "?")
            ev = d.get("event", "?")
            pr = d.get("probability", 0.5)
            evid = d.get("evidence", "-")
            lines.append(f"| {tf} | {ev} | `{pr*100:.0f}%` | {evid[:120]} |")
        lines.append("")

    # Key actors
    actors = verdict.get("key_actors", [])
    if actors:
        lines.append("### Key Actors & Forces")
        lines.append("")
        lines.append("| Actor | Type | Influence | Stance | Role |")
        lines.append("|-------|------|-----------|--------|------|")
        for a in actors:
            name = a.get("name", "?")
            atype = a.get("type", "?")
            inf = a.get("influence", 0.5)
            stance = a.get("stance", "neutral")
            summary = a.get("summary", "-")
            lines.append(f"| {name} | {atype} | `{inf*100:.0f}%` | {stance} | {summary[:100]} |")
        lines.append("")

    # Evidence lines
    evidence_lines = verdict.get("evidence_lines", [])
    if evidence_lines:
        lines.append("### Evidence Assessment")
        lines.append("")
        for el in evidence_lines:
            claim = el.get("claim", "")
            verdict_e = el.get("verdict", "?")
            ef = el.get("evidence_for", [])
            ea = el.get("evidence_against", [])
            lines.append(f"**Claim:** {claim}")
            lines.append(f"- Verdict: **{verdict_e}**")
            if ef:
                lines.append(f"- Supporting: {'; '.join(str(e)[:100] for e in ef[:3])}")
            if ea:
                lines.append(f"- Contradicting: {'; '.join(str(e)[:100] for e in ea[:3])}")
            lines.append("")

    # Key insights
    if insights:
        lines.append("---")
        lines.append("")
        lines.append("## Key Insights")
        lines.append("")
        for i, insight in enumerate(insights, 1):
            lines.append(f"{i}. **{insight}**")
        lines.append("")

    # Scenario comparison
    lines.append("---")
    lines.append("")
    lines.append("## Scenario Comparison")
    lines.append("")
    lines.append("| Scenario | Probability | Success Rate | Failure Rate | Key Events |")
    lines.append("|----------|-------------|--------------|--------------|------------|")
    for s in scenarios.get("scenarios", []):
        name = s.get("scenario", "?").title()
        sp = s.get("probability", 0)
        ss = s.get("success_probability", sp)
        sf = s.get("failure_probability", 1 - sp)
        events = " → ".join((s.get("key_events") or [])[:3])
        lines.append(f"| {name} | `{sp*100:.0f}%` | `{ss*100:.0f}%` | `{sf*100:.0f}%` | {events[:150]} |")
    lines.append("")

    # Scenario details
    for s in scenarios.get("scenarios", []):
        name = s.get("scenario", "Scenario").title()
        lines.append(f"### {name}")
        lines.append(f"- **Probability:** `{s.get('probability', '?')*100:.0f}%`")
        lines.append(f"- **Timeline:** {s.get('timeline', 'Unknown')}")
        for e in (s.get("key_events", []) or []):
            lines.append(f"  - {e}")
        lines.append("")

    # Debate
    lines.append("---")
    lines.append("")
    lines.append("## Debate Summary")
    lines.append("")
    agreed = debate.get("agreed_facts", [])
    disagreements = debate.get("disagreements", [])
    final_conf = debate.get("final_confidence", "N/A")
    lines.append(f"**Consensus Confidence:** {final_conf}")
    lines.append("")
    if agreed:
        lines.append("### Points of Agreement")
        lines.append("")
        for f in agreed:
            lines.append(f"- {f}")
        lines.append("")
    if disagreements:
        lines.append("### Unresolved Disagreements")
        lines.append("")
        for d in disagreements:
            lines.append(f"- {d}")
        lines.append("")

    # Agent analyses
    lines.append("---")
    lines.append("")
    lines.append(f"## Agent Research ({len(agent_outputs)} agents)")
    lines.append("")
    for a in agent_outputs:
        name = a.get("name", "Agent").title()
        score = a.get("score", "?")
        conf = a.get("confidence", "?")
        mission = a.get("mission", a.get("hypothesis", ""))
        findings = a.get("findings", "")
        evidence = a.get("evidence_points", [])
        risks_a = a.get("risks", [])
        opps = a.get("opportunities", [])
        searches = a.get("searches", [])

        lines.append(f"### {name}")
        lines.append(f"| | |")
        lines.append(f"|---|---|")
        lines.append(f"| Score | {score} |")
        lines.append(f"| Confidence | {conf} |")
        lines.append(f"| Mission | {str(mission)[:200]} |")
        if findings:
            lines.append(f"| Findings | {str(findings)[:300]} |")
        if evidence:
            lines.append(f"| Evidence | {', '.join(str(e)[:100] for e in evidence[:3])} |")
        if risks_a:
            lines.append(f"| Risks | {', '.join(str(r)[:80] for r in risks_a[:3])} |")
        if opps:
            lines.append(f"| Opportunities | {', '.join(str(o)[:80] for o in opps[:3])} |")
        if searches:
            lines.append(f"| Searches | {', '.join(str(s)[:100] for s in searches[:4])} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by RealWorld Simulator — ÆTHERION Swarm Intelligence Engine*")
    return "\n".join(lines)


def _make_bar(prob, width=20):
    """ASCII bar for visual probability display."""
    filled = int(prob * width)
    empty = width - filled
    if prob >= 0.7:
        bar_char, color = "█", "🟢"
    elif prob >= 0.4:
        bar_char, color = "▓", "🟡"
    else:
        bar_char, color = "░", "🔴"
    return f"{bar_char * filled}{'·' * empty}"

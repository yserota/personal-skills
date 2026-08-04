"""Build AI-vs-manual DCI impact summaries from scored writer rows."""

from __future__ import annotations

from typing import Any


def _sum(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row.get(key) or 0) for row in rows)


def _weighted_dci(started: float, finished: float) -> float | None:
    if finished == 0:
        return None
    return started / finished


def _weighted_mean(rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float | None:
    total_weight = sum(float(row.get(weight_key) or 0) for row in rows)
    if total_weight == 0:
        return None
    weighted_sum = sum(
        float(row.get(value_key) or 0) * float(row.get(weight_key) or 0)
        for row in rows
        if float(row.get(weight_key) or 0) > 0
    )
    return weighted_sum / total_weight


def aggregate_ai_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ai_started = _sum(rows, "ai_started_count")
    manual_started = _sum(rows, "manual_started_count")
    ai_finished = _sum(rows, "ai_finished_count")
    manual_finished = _sum(rows, "manual_finished_count")
    untagged_finished = _sum(rows, "untagged_finished_count")
    total_finished = _sum(rows, "active_capacity_realized")
    total_started = _sum(rows, "incoming_demand")

    return {
        "writers": len(rows),
        "total_started": total_started,
        "total_finished": total_finished,
        "ai_started": ai_started,
        "manual_started": manual_started,
        "ai_finished": ai_finished,
        "manual_finished": manual_finished,
        "untagged_finished": untagged_finished,
        "operational_dci": _weighted_dci(total_started, total_finished),
        "operational_dci_ai": _weighted_dci(ai_started, ai_finished),
        "operational_dci_manual": _weighted_dci(manual_started, manual_finished),
        "ai_adoption_pct": (ai_finished / total_finished * 100) if total_finished else None,
        "ai_adoption_tagged_pct": (ai_finished / (ai_finished + manual_finished) * 100)
        if (ai_finished + manual_finished)
        else None,
        "ai_field_coverage_pct": ((ai_finished + manual_finished) / total_finished * 100)
        if total_finished
        else None,
        "avg_cycle_days_ai": _weighted_mean(rows, "active_cycle_days_ai", "ai_finished_count"),
        "avg_cycle_days_manual": _weighted_mean(rows, "active_cycle_days_manual", "manual_finished_count"),
    }


def build_ai_impact_csv_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    csv_rows: list[dict[str, Any]] = []
    for row in rows:
        csv_rows.append(
            {
                "writer_name": row.get("writer_name", ""),
                "pod": row.get("pod", ""),
                "manager_name": row.get("manager_name", ""),
                "operational_dci": row.get("operational_dci", ""),
                "operational_dci_ai": row.get("operational_dci_ai", ""),
                "operational_dci_manual": row.get("operational_dci_manual", ""),
                "dci_ai_vs_manual_delta": row.get("dci_ai_vs_manual_delta", ""),
                "ai_finished_count": row.get("ai_finished_count", ""),
                "manual_finished_count": row.get("manual_finished_count", ""),
                "ai_adoption_pct": row.get("ai_adoption_pct", ""),
                "ai_adoption_tagged_pct": row.get("ai_adoption_tagged_pct", ""),
                "active_cycle_days": row.get("active_cycle_days", ""),
                "active_cycle_days_ai": row.get("active_cycle_days_ai", ""),
                "active_cycle_days_manual": row.get("active_cycle_days_manual", ""),
                "cycle_ai_vs_manual_delta": row.get("cycle_ai_vs_manual_delta", ""),
            }
        )
    return csv_rows


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"


def _fmt_num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def build_ai_impact_markdown(rows: list[dict[str, Any]], period_label: str = "Q1-26") -> str:
    org = aggregate_ai_metrics(rows)
    dci_delta: float | None = None
    if org["operational_dci_ai"] is not None and org["operational_dci_manual"] is not None:
        dci_delta = org["operational_dci_ai"] - org["operational_dci_manual"]

    cycle_delta: float | None = None
    if org["avg_cycle_days_ai"] is not None and org["avg_cycle_days_manual"] is not None:
        cycle_delta = org["avg_cycle_days_ai"] - org["avg_cycle_days_manual"]

    comparable = [
        row
        for row in rows
        if row.get("operational_dci_ai") not in (None, "")
        and row.get("operational_dci_manual") not in (None, "")
        and float(row.get("ai_finished_count") or 0) >= 5
        and float(row.get("manual_finished_count") or 0) >= 5
    ]
    comparable.sort(
        key=lambda row: float(row.get("dci_ai_vs_manual_delta") or 0),
        reverse=True,
    )

    lines = [
        f"# DCI × AI Usage Impact — {period_label}",
        "",
        "Segmented view of operational DCI and cycle time for **AI-assisted** vs **explicit no-usage** tickets.",
        "Source: Jira `TW-AI Usage` field (multi-select values merged at export).",
        "",
        "## Organization summary",
        "",
        "| Metric | All work | AI-assisted | Manual (No usage) |",
        "|--------|----------|-------------|---------------------|",
        f"| Finished tickets | {int(org['total_finished'])} | {int(org['ai_finished'])} | {int(org['manual_finished'])} |",
        f"| Started tickets | {int(org['total_started'])} | {int(org['ai_started'])} | {int(org['manual_started'])} |",
        f"| **Operational DCI** | **{_fmt_num(org['operational_dci'])}** | **{_fmt_num(org['operational_dci_ai'])}** | **{_fmt_num(org['operational_dci_manual'])}** |",
        f"| Avg cycle (days) | — | {_fmt_num(org['avg_cycle_days_ai'], 1)} | {_fmt_num(org['avg_cycle_days_manual'], 1)} |",
        "",
        f"- **AI adoption (all finishes):** {_fmt_pct(org['ai_adoption_pct'])}",
        f"- **AI adoption (tagged only):** {_fmt_pct(org['ai_adoption_tagged_pct'])}",
        f"- **Field coverage (tagged finishes):** {_fmt_pct(org['ai_field_coverage_pct'])}",
        f"- **Untagged finishes:** {int(org['untagged_finished'])} ({_fmt_pct(org['untagged_finished'] / org['total_finished'] * 100 if org['total_finished'] else None)})",
        "",
        "## What the org numbers suggest",
        "",
    ]

    if dci_delta is not None:
        if dci_delta > 0.05:
            lines.append(
                f"- AI-assisted work shows a **higher operational DCI** ({_fmt_num(org['operational_dci_ai'])}) "
                f"than manual ({_fmt_num(org['operational_dci_manual'])}). "
                "Teams are starting more AI-tagged work relative to what they finish — possible experimentation, "
                "or AI tickets staying open longer."
            )
        elif dci_delta < -0.05:
            lines.append(
                f"- AI-assisted work shows a **lower operational DCI** ({_fmt_num(org['operational_dci_ai'])}) "
                f"than manual ({_fmt_num(org['operational_dci_manual'])}). "
                "AI-tagged tickets are finishing faster than they are being started — backlog drain on AI work."
            )
        else:
            lines.append(
                f"- AI and manual operational DCI are **similar** ({_fmt_num(org['operational_dci_ai'])} vs "
                f"{_fmt_num(org['operational_dci_manual'])}). AI usage does not appear to materially shift "
                "execution load balance at the org level in this quarter."
            )
    else:
        lines.append("- Insufficient tagged start/finish volume to compare org-level segmented DCI.")

    if cycle_delta is not None:
        if cycle_delta < -1:
            lines.append(
                f"- AI-assisted tickets average **{_fmt_num(abs(cycle_delta), 1)} fewer days** "
                f"start-to-finish ({_fmt_num(org['avg_cycle_days_ai'], 1)} vs {_fmt_num(org['avg_cycle_days_manual'], 1)})."
            )
        elif cycle_delta > 1:
            lines.append(
                f"- AI-assisted tickets average **{_fmt_num(cycle_delta, 1)} more days** "
                f"start-to-finish ({_fmt_num(org['avg_cycle_days_ai'], 1)} vs {_fmt_num(org['avg_cycle_days_manual'], 1)})."
            )
        else:
            lines.append(
                f"- Cycle times are comparable between AI ({_fmt_num(org['avg_cycle_days_ai'], 1)} days) "
                f"and manual ({_fmt_num(org['avg_cycle_days_manual'], 1)} days)."
            )

    lines.extend(
        [
            "",
            "## Writer comparison (≥5 AI and ≥5 manual finishes)",
            "",
            "| Writer | Overall DCI | AI DCI | Manual DCI | Δ (AI−Manual) | AI finishes | Manual finishes | AI adoption | Cycle Δ (days) |",
            "|--------|-------------|--------|------------|---------------|-------------|-----------------|-------------|----------------|",
        ]
    )

    if not comparable:
        lines.append("| — | — | — | — | — | — | — | — | — |")
        lines.append("")
        lines.append("_No writers met the minimum sample threshold for side-by-side DCI comparison._")
    else:
        for row in comparable:
            lines.append(
                f"| {row['writer_name']} | {_fmt_num(float(row['operational_dci'])) if row.get('operational_dci') not in (None, '') else 'n/a'} "
                f"| {_fmt_num(float(row['operational_dci_ai'])) if row.get('operational_dci_ai') not in (None, '') else 'n/a'} "
                f"| {_fmt_num(float(row['operational_dci_manual'])) if row.get('operational_dci_manual') not in (None, '') else 'n/a'} "
                f"| {_fmt_num(float(row['dci_ai_vs_manual_delta'])) if row.get('dci_ai_vs_manual_delta') not in (None, '') else 'n/a'} "
                f"| {int(float(row.get('ai_finished_count') or 0))} "
                f"| {int(float(row.get('manual_finished_count') or 0))} "
                f"| {_fmt_pct(float(row['ai_adoption_pct'])) if row.get('ai_adoption_pct') not in (None, '') else 'n/a'} "
                f"| {_fmt_num(float(row['cycle_ai_vs_manual_delta'])) if row.get('cycle_ai_vs_manual_delta') not in (None, '') else 'n/a'} |"
            )

    lines.extend(
        [
            "",
            "## How to read segmented DCI",
            "",
            "- **Operational DCI** = started ÷ finished in the quarter (same formula, split by TW-AI Usage).",
            "- **AI-assisted** = any ticket with a TW-AI Usage value other than `No usage` / blank.",
            "- **Manual** = tickets explicitly tagged `No usage`.",
            "- **Untagged** = blank field; excluded from AI vs manual DCI but included in overall DCI.",
            "- Compare writers only when both segments have enough volume (default ≥5 finishes each).",
            "- DCI measures load balance, not quality — a higher AI DCI means more AI work in flight vs closed.",
            "",
            "## Data notes",
            "",
            "- Multi-select TW-AI values are merged (e.g. `Generate first draft; Improve wording`).",
            "- Overall DCI can differ from a blend of AI/manual DCI because untagged tickets are included only in overall.",
        ]
    )

    return "\n".join(lines) + "\n"

"""Build Google Sheets dashboard tab CSVs from scored DCI writer rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .ai_analysis import aggregate_ai_metrics


def _dci_zone(dci: float | None) -> str:
    if dci is None:
        return "n/a"
    if dci > 1.0:
        return "Backlog building"
    if 0.80 <= dci <= 0.95:
        return "Healthy runway"
    if dci < 0.75:
        return "Backlog drain"
    return "Watch band"


def _fmt(value: float | None | str, digits: int = 2) -> str | float:
    if value is None or value == "":
        return ""
    return round(float(value), digits)


def _float(row: dict[str, Any], key: str) -> float:
    raw = row.get(key)
    if raw in (None, ""):
        return 0.0
    return float(raw)


def _writer_flag(row: dict[str, Any]) -> str:
    flags: list[str] = []
    dci = row.get("operational_dci")
    if dci not in (None, "") and float(dci) < 0.75:
        flags.append("Low DCI")
    if dci not in (None, "") and float(dci) > 1.0:
        flags.append("High inflow")
    backlog = _float(row, "backlog_pressure")
    if backlog >= 40:
        flags.append("Intake pressure")
    delta = row.get("dci_ai_vs_manual_delta")
    if delta not in (None, "") and abs(float(delta)) >= 0.15:
        flags.append("AI/manual DCI gap")
    cycle_delta = row.get("cycle_ai_vs_manual_delta")
    if cycle_delta not in (None, "") and abs(float(cycle_delta)) >= 10:
        flags.append("AI/manual cycle gap")
    return "; ".join(flags)


def _ai_comparable(row: dict[str, Any], min_each: int = 5) -> bool:
    return (
        _float(row, "ai_finished_count") >= min_each
        and _float(row, "manual_finished_count") >= min_each
        and row.get("operational_dci_ai") not in (None, "")
        and row.get("operational_dci_manual") not in (None, "")
    )


def _aggregate_pod(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        pod = (row.get("pod") or "Unknown").strip() or "Unknown"
        grouped[pod].append(row)

    pod_rows: list[dict[str, Any]] = []
    for pod in sorted(grouped):
        pod_group = grouped[pod]
        metrics = aggregate_ai_metrics(pod_group)
        manager = next((r.get("manager_name", "") for r in pod_group if r.get("manager_name")), "")
        pod_rows.append(
            {
                "pod": pod,
                "manager": manager,
                "writers": len(pod_group),
                "work_started": int(metrics["total_started"]),
                "work_finished": int(metrics["total_finished"]),
                "tickets_created": int(_sum_rows(pod_group, "intake_count")),
                "operational_dci": _fmt(metrics["operational_dci"]),
                "intake_dci": _fmt(
                    _sum_rows(pod_group, "intake_count") / metrics["total_finished"]
                    if metrics["total_finished"]
                    else None
                ),
                "backlog_pressure": int(_sum_rows(pod_group, "backlog_pressure")),
                "avg_cycle_days": _fmt(
                    _weighted_mean_rows(pod_group, "active_cycle_days", "active_capacity_realized")
                ),
                "avg_queue_lag_days": _fmt(
                    _weighted_mean_rows(pod_group, "avg_queue_lag_days", "active_capacity_realized")
                ),
                "ai_finished": int(metrics["ai_finished"]),
                "manual_finished": int(metrics["manual_finished"]),
                "ai_adoption_pct": _fmt(metrics["ai_adoption_pct"], 1),
                "operational_dci_ai": _fmt(metrics["operational_dci_ai"]),
                "operational_dci_manual": _fmt(metrics["operational_dci_manual"]),
                "avg_cycle_days_ai": _fmt(metrics["avg_cycle_days_ai"], 1),
                "avg_cycle_days_manual": _fmt(metrics["avg_cycle_days_manual"], 1),
                "dci_zone": _dci_zone(metrics["operational_dci"]),
            }
        )
    return pod_rows


def _sum_rows(rows: list[dict[str, Any]], key: str) -> float:
    return sum(_float(row, key) for row in rows)


def _weighted_mean_rows(
    rows: list[dict[str, Any]], value_key: str, weight_key: str
) -> float | None:
    total_weight = sum(_float(row, weight_key) for row in rows)
    if total_weight == 0:
        return None
    return sum(_float(row, value_key) * _float(row, weight_key) for row in rows) / total_weight


def build_tab0_cover(rows: list[dict[str, Any]], period_label: str) -> list[dict[str, Any]]:
    org = aggregate_ai_metrics(rows)
    insights: list[str] = []
    if org["operational_dci_ai"] is not None and org["operational_dci_manual"] is not None:
        delta = org["operational_dci_ai"] - org["operational_dci_manual"]
        if abs(delta) <= 0.05:
            insights.append(
                "AI and manual operational DCI are similar at org level — AI usage does not "
                "materially shift execution load balance this quarter."
            )
        elif delta > 0.05:
            insights.append(
                "AI-assisted work shows higher operational DCI than manual — more AI work in "
                "flight relative to closes."
            )
        else:
            insights.append(
                "AI-assisted work shows lower operational DCI than manual — AI tickets closing "
                "faster than they are being started."
            )
    if org["avg_cycle_days_ai"] is not None and org["avg_cycle_days_manual"] is not None:
        cycle_delta = org["avg_cycle_days_ai"] - org["avg_cycle_days_manual"]
        if abs(cycle_delta) >= 1:
            direction = "more" if cycle_delta > 0 else "fewer"
            insights.append(
                f"AI-assisted tickets average {abs(cycle_delta):.1f} {direction} days start-to-finish "
                f"than manual ({org['avg_cycle_days_ai']:.1f} vs {org['avg_cycle_days_manual']:.1f})."
            )

    cover: list[dict[str, Any]] = [
        {"section": "Report", "metric": "Title", "value": f"TW DCI + AI Dashboard — {period_label}"},
        {"section": "Report", "metric": "Audience", "value": "Ofrit (exec) · Pod TLs (filtered views)"},
        {"section": "Report", "metric": "Source", "value": "Jira StartWork / FinishWork / Created / TW-AI Usage / Story Points"},
        {"section": "Organization", "metric": "Writers scored", "value": org["writers"]},
        {"section": "Organization", "metric": "Work started (tickets)", "value": int(org["total_started"])},
        {"section": "Organization", "metric": "Work finished (tickets)", "value": int(org["total_finished"])},
        {
            "section": "Organization",
            "metric": "Story points finished",
            "value": _fmt(_sum_rows(rows, "story_points_finished"), 1),
        },
        {
            "section": "Organization",
            "metric": "Operational DCI (points)",
            "value": _fmt(
                _sum_rows(rows, "story_points_started") / _sum_rows(rows, "story_points_finished")
                if _sum_rows(rows, "story_points_finished")
                else None
            ),
        },
        {
            "section": "Organization",
            "metric": "Operational DCI (all)",
            "value": _fmt(org["operational_dci"]),
        },
        {
            "section": "Organization",
            "metric": "Operational DCI (AI-assisted)",
            "value": _fmt(org["operational_dci_ai"]),
        },
        {
            "section": "Organization",
            "metric": "Operational DCI (manual)",
            "value": _fmt(org["operational_dci_manual"]),
        },
        {
            "section": "Organization",
            "metric": "AI adoption (all finishes)",
            "value": f"{_fmt(org['ai_adoption_pct'], 1)}%",
        },
        {
            "section": "Organization",
            "metric": "AI adoption (tagged only)",
            "value": f"{_fmt(org['ai_adoption_tagged_pct'], 1)}%",
        },
        {
            "section": "Organization",
            "metric": "TW-AI field coverage",
            "value": f"{_fmt(org['ai_field_coverage_pct'], 1)}%",
        },
        {
            "section": "Organization",
            "metric": "Avg cycle days (AI / manual)",
            "value": f"{_fmt(org['avg_cycle_days_ai'], 1)} / {_fmt(org['avg_cycle_days_manual'], 1)}",
        },
    ]
    for index, insight in enumerate(insights, start=1):
        cover.append({"section": "Insight", "metric": f"#{index}", "value": insight})
    return cover


def build_tab1_executive_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    org = aggregate_ai_metrics(rows)
    org_row = {
        "level": "Organization",
        "pod": "All",
        "manager": "All managers",
        "writers": org["writers"],
        "work_started": int(org["total_started"]),
        "work_finished": int(org["total_finished"]),
        "tickets_created": int(_sum_rows(rows, "intake_count")),
        "ai_finished": int(org["ai_finished"]),
        "manual_finished": int(org["manual_finished"]),
        "untagged_finished": int(org["untagged_finished"]),
        "operational_dci": _fmt(org["operational_dci"]),
        "operational_dci_ai": _fmt(org["operational_dci_ai"]),
        "operational_dci_manual": _fmt(org["operational_dci_manual"]),
        "intake_dci": _fmt(_sum_rows(rows, "intake_count") / org["total_finished"] if org["total_finished"] else None),
        "ai_adoption_pct": _fmt(org["ai_adoption_pct"], 1),
        "avg_cycle_days_ai": _fmt(org["avg_cycle_days_ai"], 1),
        "avg_cycle_days_manual": _fmt(org["avg_cycle_days_manual"], 1),
        "dci_zone": _dci_zone(org["operational_dci"]),
        "headline": "See Cover tab for narrative insights",
    }

    pod_rows: list[dict[str, Any]] = []
    for pod_row in _aggregate_pod(rows):
        finished = pod_row["work_finished"]
        pod_rows.append(
            {
                "level": "Pod",
                "pod": pod_row["pod"],
                "manager": pod_row["manager"],
                "writers": pod_row["writers"],
                "work_started": pod_row["work_started"],
                "work_finished": pod_row["work_finished"],
                "tickets_created": pod_row.get("tickets_created", ""),
                "ai_finished": pod_row["ai_finished"],
                "manual_finished": pod_row["manual_finished"],
                "untagged_finished": int(finished - pod_row["ai_finished"] - pod_row["manual_finished"]),
                "operational_dci": pod_row["operational_dci"],
                "operational_dci_ai": pod_row["operational_dci_ai"],
                "operational_dci_manual": pod_row["operational_dci_manual"],
                "intake_dci": pod_row["intake_dci"],
                "ai_adoption_pct": pod_row["ai_adoption_pct"],
                "avg_cycle_days_ai": pod_row["avg_cycle_days_ai"],
                "avg_cycle_days_manual": pod_row["avg_cycle_days_manual"],
                "dci_zone": pod_row["dci_zone"],
                "headline": "",
            }
        )
    return [org_row, *pod_rows]


def build_tab2_writer_scorecard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scorecard: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: (_float(r, "operational_dci")), reverse=True):
        dci = row.get("operational_dci")
        scorecard.append(
            {
                "writer_name": row.get("writer_name", ""),
                "manager": row.get("manager_name", ""),
                "pod": row.get("pod", ""),
                "work_started": int(_float(row, "incoming_demand")),
                "work_finished": int(_float(row, "active_capacity_realized")),
                "story_points_started": _fmt(row.get("story_points_started"), 1),
                "story_points_finished": _fmt(row.get("story_points_finished"), 1),
                "story_points_intake": _fmt(row.get("story_points_intake"), 1),
                "operational_dci_points": _fmt(row.get("operational_dci_points")),
                "intake_dci_points": _fmt(row.get("intake_dci_points")),
                "avg_story_points_per_finish": _fmt(row.get("avg_story_points_per_finish"), 2),
                "story_points_coverage_pct": _fmt(row.get("story_points_coverage_pct"), 1),
                "tickets_created": int(_float(row, "intake_count")),
                "operational_dci": _fmt(dci),
                "intake_dci": _fmt(row.get("intake_dci")),
                "backlog_pressure": int(_float(row, "backlog_pressure")),
                "avg_cycle_days": _fmt(row.get("active_cycle_days"), 1),
                "avg_queue_lag_days": _fmt(row.get("avg_queue_lag_days"), 1),
                "ai_adoption_pct": _fmt(row.get("ai_adoption_pct"), 1),
                "ai_finished": int(_float(row, "ai_finished_count")),
                "manual_finished": int(_float(row, "manual_finished_count")),
                "operational_dci_ai": _fmt(row.get("operational_dci_ai")),
                "operational_dci_manual": _fmt(row.get("operational_dci_manual")),
                "dci_ai_vs_manual_delta": _fmt(row.get("dci_ai_vs_manual_delta")),
                "avg_cycle_days_ai": _fmt(row.get("active_cycle_days_ai"), 1),
                "avg_cycle_days_manual": _fmt(row.get("active_cycle_days_manual"), 1),
                "cycle_ai_vs_manual_delta": _fmt(row.get("cycle_ai_vs_manual_delta"), 1),
                "dci_zone": _dci_zone(float(dci) if dci not in (None, "") else None),
                "flag": _writer_flag(row),
            }
        )
    return scorecard


def build_tab3_ai_impact(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    impact: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: r.get("writer_name", "")):
        impact.append(
            {
                "writer_name": row.get("writer_name", ""),
                "pod": row.get("pod", ""),
                "manager": row.get("manager_name", ""),
                "comparable_sample": "yes" if _ai_comparable(row) else "low volume",
                "operational_dci": _fmt(row.get("operational_dci")),
                "operational_dci_ai": _fmt(row.get("operational_dci_ai")),
                "operational_dci_manual": _fmt(row.get("operational_dci_manual")),
                "dci_ai_vs_manual_delta": _fmt(row.get("dci_ai_vs_manual_delta")),
                "ai_finished": int(_float(row, "ai_finished_count")),
                "manual_finished": int(_float(row, "manual_finished_count")),
                "untagged_finished": int(_float(row, "untagged_finished_count")),
                "ai_adoption_pct": _fmt(row.get("ai_adoption_pct"), 1),
                "ai_adoption_tagged_pct": _fmt(row.get("ai_adoption_tagged_pct"), 1),
                "ai_field_coverage_pct": _fmt(row.get("ai_field_coverage_pct"), 1),
                "avg_cycle_days_ai": _fmt(row.get("active_cycle_days_ai"), 1),
                "avg_cycle_days_manual": _fmt(row.get("active_cycle_days_manual"), 1),
                "cycle_ai_vs_manual_delta": _fmt(row.get("cycle_ai_vs_manual_delta"), 1),
            }
        )
    return impact


def build_tab4_chart_data(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pre-shaped rows for common Google Sheets / Looker Studio charts."""
    chart_rows: list[dict[str, Any]] = []

    org = aggregate_ai_metrics(rows)
    for label, count in (
        ("AI-assisted", org["ai_finished"]),
        ("Manual (No usage)", org["manual_finished"]),
        ("Untagged", org["untagged_finished"]),
    ):
        chart_rows.append(
            {
                "chart": "Org finish mix",
                "category": label,
                "writer_name": "",
                "pod": "",
                "value": int(count),
                "operational_dci": "",
                "operational_dci_ai": "",
                "operational_dci_manual": "",
                "ai_adoption_pct": "",
            }
        )

    for row in rows:
        chart_rows.append(
            {
                "chart": "AI adoption by writer",
                "category": "",
                "writer_name": row.get("writer_name", ""),
                "pod": row.get("pod", ""),
                "value": _fmt(row.get("ai_adoption_pct"), 1),
                "operational_dci": _fmt(row.get("operational_dci")),
                "operational_dci_ai": _fmt(row.get("operational_dci_ai")),
                "operational_dci_manual": _fmt(row.get("operational_dci_manual")),
                "ai_adoption_pct": _fmt(row.get("ai_adoption_pct"), 1),
            }
        )

    for row in rows:
        if not _ai_comparable(row):
            continue
        for segment, dci_value in (
            ("Overall", row.get("operational_dci")),
            ("AI-assisted", row.get("operational_dci_ai")),
            ("Manual", row.get("operational_dci_manual")),
        ):
            chart_rows.append(
                {
                    "chart": "DCI by segment (comparable writers)",
                    "category": segment,
                    "writer_name": row.get("writer_name", ""),
                    "pod": row.get("pod", ""),
                    "value": _fmt(dci_value),
                    "operational_dci": _fmt(row.get("operational_dci")),
                    "operational_dci_ai": _fmt(row.get("operational_dci_ai")),
                    "operational_dci_manual": _fmt(row.get("operational_dci_manual")),
                    "ai_adoption_pct": _fmt(row.get("ai_adoption_pct"), 1),
                }
            )

    return chart_rows


def build_tab5_metric_definitions() -> list[dict[str, Any]]:
    return [
        {
            "metric": "Operational DCI",
            "definition": "Execution load vs completed work in the quarter",
            "formula": "Work started / Work finished",
            "how_to_read": ">1.0 backlog building | 0.80–0.95 healthy | <0.75 backlog drain",
        },
        {
            "metric": "Operational DCI (AI / manual)",
            "definition": "Same formula split by Jira TW-AI Usage",
            "formula": "AI or manual starts / AI or manual finishes",
            "how_to_read": "Compare segments only when each has enough volume (≥5 finishes)",
        },
        {
            "metric": "AI adoption %",
            "definition": "Share of finished tickets with AI usage tagged",
            "formula": "AI finishes / all finishes",
            "how_to_read": "Higher = more AI-assisted completions in the quarter",
        },
        {
            "metric": "AI adoption (tagged only)",
            "definition": "AI share excluding blank TW-AI Usage",
            "formula": "AI finishes / (AI + manual finishes)",
            "how_to_read": "Use when field coverage is high",
        },
        {
            "metric": "TW-AI field coverage",
            "definition": "Share of finishes with AI or explicit No usage",
            "formula": "(AI + manual finishes) / all finishes",
            "how_to_read": "Low coverage = interpret AI metrics cautiously",
        },
        {
            "metric": "dci_ai_vs_manual_delta",
            "definition": "Difference in segmented operational DCI",
            "formula": "operational_dci_ai - operational_dci_manual",
            "how_to_read": "Positive = more AI work in flight vs closes relative to manual",
        },
        {
            "metric": "cycle_ai_vs_manual_delta",
            "definition": "Difference in average start-to-finish days",
            "formula": "active_cycle_days_ai - active_cycle_days_manual",
            "how_to_read": "Positive = AI-tagged tickets take longer on average",
        },
        {
            "metric": "Intake DCI",
            "definition": "Intake pressure vs completed work",
            "formula": "Tickets created / Work finished",
            "how_to_read": ">1.0 = more tickets entering than closing",
        },
        {
            "metric": "Backlog pressure",
            "definition": "Queue buildup signal",
            "formula": "Tickets created - Work started",
            "how_to_read": "Higher = more tickets waiting to be started",
        },
        {
            "metric": "Avg cycle days",
            "definition": "Active work duration",
            "formula": "FinishWork - StartWork (average)",
            "how_to_read": "Lower = faster delivery",
        },
        {
            "metric": "Operational DCI (points)",
            "definition": "Execution load weighted by Jira Story Points",
            "formula": "Story points started / Story points finished",
            "how_to_read": "Same zones as ticket DCI; compare to operational_dci to see complexity mix",
        },
        {
            "metric": "Intake DCI (points)",
            "definition": "Intake pressure weighted by Story Points on created tickets",
            "formula": "Story points intake / Story points finished",
            "how_to_read": ">1.0 = heavier incoming work than closes in the quarter",
        },
        {
            "metric": "Avg story points per finish",
            "definition": "Average Story Points on finished tickets",
            "formula": "Story points finished / Work finished",
            "how_to_read": "Higher = heavier typical ticket size (complexity proxy)",
        },
        {
            "metric": "Story points coverage %",
            "definition": "Share of counted tickets with a non-empty Story Points field",
            "formula": "Tickets with SP / tickets in DCI numerator",
            "how_to_read": "Low coverage = points DCI relies on 1.0 default weight for missing SP",
        },
        {
            "metric": "Avg queue lag days",
            "definition": "Wait time before work begins",
            "formula": "StartWork - Created (average)",
            "how_to_read": "Higher = tickets sitting before pickup",
        },
    ]


def _build_group_rollup(
    rows: list[dict[str, Any]], group_key: str, level_label: str
) -> list[dict[str, Any]]:
    """Build an SP-weighted DCI rollup grouped by *group_key*."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group = (row.get(group_key) or "Unknown").strip() or "Unknown"
        grouped[group].append(row)

    result: list[dict[str, Any]] = []
    for group_name in sorted(grouped):
        group = grouped[group_name]
        sp_started = _sum_rows(group, "story_points_started")
        sp_finished = _sum_rows(group, "story_points_finished")
        sp_dci = sp_started / sp_finished if sp_finished else None
        metrics = aggregate_ai_metrics(group)
        result.append(
            {
                "level": level_label,
                "group": group_name,
                "writers": len(group),
                "story_points_started": _fmt(sp_started, 1),
                "story_points_finished": _fmt(sp_finished, 1),
                "story_points_dci": _fmt(sp_dci),
                "operational_dci": _fmt(metrics["operational_dci"]),
                "tickets_started": int(metrics["total_started"]),
                "tickets_finished": int(metrics["total_finished"]),
                "ai_finished": int(metrics["ai_finished"]),
                "ai_adoption_pct": _fmt(metrics["ai_adoption_pct"], 1),
                "dci_zone": _dci_zone(metrics["operational_dci"]),
            }
        )
    return result


def build_tab6_team_rollup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _build_group_rollup(rows, "team", "Team")


def build_tab7_manager_rollup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _build_group_rollup(rows, "manager_name", "Manager")


def build_dashboard_exports(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    period_label = "Q1-26"
    if rows:
        period_label = f"{rows[0].get('period_start', '')} to {rows[0].get('period_end', '')}"
    return {
        "Tab0_Cover": build_tab0_cover(rows, period_label),
        "Tab1_Executive_Summary": build_tab1_executive_summary(rows),
        "Tab2_Writer_Scorecard": build_tab2_writer_scorecard(rows),
        "Tab3_AI_Impact": build_tab3_ai_impact(rows),
        "Tab4_Chart_Data": build_tab4_chart_data(rows),
        "Tab5_Metric_Definitions": build_tab5_metric_definitions(),
        "Tab6_Team_Rollup": build_tab6_team_rollup(rows),
        "Tab7_Manager_Rollup": build_tab7_manager_rollup(rows),
    }

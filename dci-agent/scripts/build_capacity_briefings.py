"""Generate per-writer Capacity & Throughput briefings from DCI scorecard output."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fnum(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{suffix}"


def dci_emoji(dci: float | None) -> str:
    if dci is None:
        return ""
    if dci > 1.0:
        return " ⚠️"
    if dci >= 0.80:
        return " 🟡"
    return " 🟢"


def manager_first_name(manager: str) -> str:
    return manager.split()[0] if manager else "Manager"


def build_tldr(row: dict[str, str], score: dict[str, str]) -> str:
    name = row["writer_name"]
    finishes = int(fnum(row.get("work_finished")) or 0)
    starts = int(fnum(row.get("work_started")) or 0)
    dci = fnum(row.get("operational_dci"))
    intake_dci = fnum(row.get("intake_dci"))
    backlog = fnum(row.get("backlog_pressure"))
    queue_lag = fnum(row.get("avg_queue_lag_days"))
    cycle = fnum(row.get("avg_cycle_days"))
    ai_pct = fnum(row.get("ai_adoption_pct"))
    zone = row.get("dci_zone", "")
    flags = row.get("flag", "") or "None"
    team = score.get("team", "")

    parts: list[str] = []
    parts.append(
        f"{name} resolved **{finishes}** tickets in Q2 2026 against **{starts}** started "
        f"(operational DCI **{fmt(dci, 2)}**, zone: {zone})."
    )
    if intake_dci is not None and intake_dci > 1.0:
        parts.append(
            f"Intake DCI is **{fmt(intake_dci, 2)}** — new tickets are arriving faster than throughput."
        )
    elif intake_dci is not None and intake_dci < 1.0:
        parts.append(f"Intake DCI is **{fmt(intake_dci, 2)}** — intake is below resolved capacity.")
    if backlog is not None and backlog > 15:
        parts.append(f"Backlog pressure is **+{int(backlog)}** tickets.")
    elif backlog is not None and backlog <= 0:
        parts.append("Backlog pressure is flat or negative — queue is not growing from new intake.")
    if queue_lag is not None and queue_lag >= 60:
        parts.append(
            f"**Queue lag is elevated at {fmt(queue_lag)} days** — work started in Q2 sat in the queue a long time."
        )
    if cycle is not None and cycle >= 30:
        parts.append(f"Average cycle time is **{fmt(cycle)} days**, above typical Execution peers.")
    if ai_pct is not None:
        parts.append(f"AI adoption on resolved work: **{fmt(ai_pct)}%**.")
    if team == "Standards":
        parts.append(
            "Benchmark cycle times and throughput against SOH Standards peers, not Execution writers."
        )
    if flags != "None":
        parts.append(f"Flags: {flags}.")
    return " ".join(parts)


def talking_points(row: dict[str, str], score: dict[str, str]) -> list[tuple[str, str, str]]:
    points: list[tuple[str, str, str]] = []
    dci = fnum(row.get("operational_dci"))
    intake_dci = fnum(row.get("intake_dci"))
    queue_lag = fnum(row.get("avg_queue_lag_days"))
    cycle = fnum(row.get("avg_cycle_days"))
    ai_pct = fnum(row.get("ai_adoption_pct"))
    ai_dci = fnum(row.get("operational_dci_ai"))
    manual_dci = fnum(row.get("operational_dci_manual"))
    cycle_ai = fnum(row.get("avg_cycle_days_ai"))
    cycle_manual = fnum(row.get("avg_cycle_days_manual"))
    untagged = int(fnum(score.get("untagged_finished_count")) or 0)
    finishes = int(fnum(row.get("work_finished")) or 0)

    if dci is not None and dci < 0.65:
        points.append(
            (
                "Low DCI",
                f"DCI {fmt(dci, 2)} — finishing well above starts ({row['work_finished']} vs {row['work_started']}).",
                "Is this backlog burn-down or sustainable in-period throughput? What mix of old vs new work drove Q2 closes?",
            )
        )
    elif dci is not None and dci >= 0.85:
        points.append(
            (
                "Tight capacity",
                f"DCI {fmt(dci, 2)} — demand is close to or above capacity.",
                "Is there headroom for more intake, or should incoming demand be throttled?",
            )
        )

    if intake_dci is not None and intake_dci > 1.1:
        points.append(
            (
                "Intake pressure",
                f"Intake DCI {fmt(intake_dci, 2)} with backlog pressure +{int(fnum(row.get('backlog_pressure')) or 0)}.",
                "What intake controls or prioritization changes would keep the queue healthy?",
            )
        )

    if queue_lag is not None and queue_lag >= 50:
        points.append(
            (
                "Queue lag",
                f"Avg queue lag {fmt(queue_lag)} days.",
                "Which ticket types are aging in the queue? Prioritization issue or capacity constraint?",
            )
        )

    if cycle is not None and cycle >= 25:
        points.append(
            (
                "Cycle time",
                f"Avg cycle {fmt(cycle)} days in Q2.",
                "Is this complexity, concurrent WIP, or closure hygiene on long-running tickets?",
            )
        )

    if ai_pct is not None and ai_pct < 35:
        points.append(
            (
                "AI adoption",
                f"AI adoption {fmt(ai_pct)}% on resolved work.",
                "What would help shift more work to AI-assisted workflows?",
            )
        )

    if (
        ai_dci is not None
        and manual_dci is not None
        and abs(ai_dci - manual_dci) >= 0.15
    ):
        points.append(
            (
                "AI vs manual DCI",
                f"AI DCI {fmt(ai_dci, 2)} vs manual {fmt(manual_dci, 2)}.",
                "Are AI-tagged tickets structurally different (scope/complexity), or is tagging inconsistent?",
            )
        )

    if (
        cycle_ai is not None
        and cycle_manual is not None
        and abs(cycle_ai - cycle_manual) >= 10
    ):
        direction = "faster" if cycle_ai < cycle_manual else "slower"
        points.append(
            (
                "AI vs manual cycle",
                f"AI cycle {fmt(cycle_ai)} days vs manual {fmt(cycle_manual)} days — AI is {direction}.",
                "Does tagging reflect ticket difficulty, or is there friction in one workflow?",
            )
        )

    if untagged > 0 and finishes > 0 and untagged / finishes >= 0.25:
        points.append(
            (
                "Untagged work",
                f"{untagged} of {finishes} resolved tickets ({fmt(100 * untagged / finishes)}%) untagged.",
                "Can TW-AI Usage tagging be improved for cleaner AI metrics next quarter?",
            )
        )

    if not points:
        points.append(
            (
                "Balanced profile",
                "No major operational red flags in Q2 metrics.",
                "Confirm qualitative goals and collaboration alongside these throughput numbers.",
            )
        )

    return points[:6]


def render_briefing(row: dict[str, str], score: dict[str, str], period_label: str) -> str:
    manager = row.get("manager", score.get("manager_name", ""))
    pod = row.get("pod", score.get("pod", ""))
    team = score.get("team", "")
    today = date.today().isoformat()
    fname = manager_first_name(manager)

    lines = [
        f"# {row['writer_name']} — Capacity & Throughput Briefing",
        f"**{pod} · {team} · Manager: {manager}**",
        f"**Period: {period_label}**",
        f"**Prepared: {today}**",
        "",
        "---",
        "",
        "## TL;DR",
        "",
        build_tldr(row, score),
        "",
        "---",
        "",
        "## Q2 2026 Snapshot",
        "",
        "| | |",
        "|---|---|",
        f"| **Tickets resolved** | {row['work_finished']} |",
        f"| **Tickets started** | {row['work_started']} |",
        f"| **New intake (created)** | {row['tickets_created']} |",
        f"| **DCI (demand ÷ capacity)** | {fmt(fnum(row.get('operational_dci')), 2)}{dci_emoji(fnum(row.get('operational_dci')))} |",
        f"| **Intake DCI** | {fmt(fnum(row.get('intake_dci')), 2)} |",
        f"| **Backlog pressure** | {int(fnum(row.get('backlog_pressure')) or 0):+d} |",
        f"| **DCI zone** | {row.get('dci_zone', 'n/a')} |",
        f"| **AI adoption** | {fmt(fnum(row.get('ai_adoption_pct')))}% |",
        f"| **Avg cycle time** | {fmt(fnum(row.get('avg_cycle_days')))} days |",
        f"| **Avg queue lag** | {fmt(fnum(row.get('avg_queue_lag_days')))} days |",
        "",
        "---",
        "",
        "## Detailed Metrics",
        "",
        "| Metric | Q2 2026 |",
        "|---|---|",
        f"| Demand (tickets started) | {row['work_started']} |",
        f"| Tickets resolved | {row['work_finished']} |",
        f"| New intake (tickets created) | {row['tickets_created']} |",
        f"| **DCI (demand ÷ capacity)** | {fmt(fnum(row.get('operational_dci')), 2)}{dci_emoji(fnum(row.get('operational_dci')))} |",
        f"| Intake DCI | {fmt(fnum(row.get('intake_dci')), 2)} |",
        f"| Backlog pressure | {int(fnum(row.get('backlog_pressure')) or 0):+d} |",
        f"| **Avg queue lag (days)** | {fmt(fnum(row.get('avg_queue_lag_days')))} |",
        f"| **Avg cycle time (days)** | {fmt(fnum(row.get('avg_cycle_days')))} |",
        f"| Cycle time — AI-assisted (days) | {fmt(fnum(row.get('avg_cycle_days_ai')))} |",
        f"| Cycle time — manual (days) | {fmt(fnum(row.get('avg_cycle_days_manual')))} |",
        f"| **AI adoption %** | {fmt(fnum(row.get('ai_adoption_pct')))}% |",
        f"| AI field coverage % | {fmt(fnum(score.get('ai_field_coverage_pct')))}% |",
        f"| AI-assisted resolved | {int(fnum(row.get('ai_finished')) or 0)} |",
        f"| Manual resolved | {int(fnum(row.get('manual_finished')) or 0)} |",
        f"| Untagged resolved | {int(fnum(score.get('untagged_finished_count')) or 0)} |",
        f"| DCI (AI work type) | {fmt(fnum(row.get('operational_dci_ai')), 2)} |",
        f"| DCI (manual work type) | {fmt(fnum(row.get('operational_dci_manual')), 2)} |",
        f"| Predictability proxy | {fmt(fnum(score.get('predictability_proxy')), 2)} |",
        "",
        "---",
        "",
        "## Suggested Talking Points",
        "",
        "| Area | Observation | Suggested question |",
        "|---|---|---|",
    ]

    for area, obs, question in talking_points(row, score):
        lines.append(f"| **{area}** | {obs} | {question} |")

    lines.extend(
        [
            "",
            "---",
            "",
            f"*Data source: DCI pipeline {score.get('formula_version', '1.2.0')} · "
            f"Jira MCP export Q2 2026 · Computed {score.get('computed_at_utc', today)}*",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build per-writer capacity briefings.")
    parser.add_argument(
        "--output-dir",
        default="out/q2-2026",
        help="DCI run output directory containing scorecard CSVs",
    )
    parser.add_argument(
        "--briefings-dir",
        help="Directory for briefing markdown files (default: <output-dir>/capacity_briefings)",
    )
    parser.add_argument("--period-label", default="Q2 2026 (Apr–Jun)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    briefings_dir = Path(args.briefings_dir or output_dir / "capacity_briefings")
    briefings_dir.mkdir(parents=True, exist_ok=True)

    scorecard_path = output_dir / "dashboard" / "Tab2_Writer_Scorecard.csv"
    scores_path = output_dir / "dci_writer_scores.csv"

    with scorecard_path.open(encoding="utf-8", newline="") as fh:
        scorecard = {row["writer_name"]: row for row in csv.DictReader(fh)}
    with scores_path.open(encoding="utf-8", newline="") as fh:
        scores = {row["writer_name"]: row for row in csv.DictReader(fh)}

    written: list[str] = []
    for writer_name, row in sorted(scorecard.items()):
        score = scores.get(writer_name, {})
        manager = row.get("manager", score.get("manager_name", "Manager"))
        fname = f"{writer_name.replace(' ', '_')}_Briefing_for_{manager_first_name(manager)}.md"
        content = render_briefing(row, score, args.period_label)
        out_path = briefings_dir / fname
        out_path.write_text(content, encoding="utf-8")
        written.append(str(out_path))

    summary = {
        "writers": len(written),
        "briefings_dir": str(briefings_dir),
        "files": written,
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

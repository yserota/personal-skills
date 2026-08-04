"""Build TW performance calibration pack from DCI scorecard outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_scorecard(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return {row["writer_name"]: row for row in csv.DictReader(f)}


def fnum(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def evidence_tier(row: dict[str, str]) -> str:
    dci = fnum(row.get("operational_dci"))
    finishes = fnum(row.get("work_finished")) or 0
    flags = row.get("flag", "") or ""
    zone = row.get("dci_zone", "") or ""

    if finishes < 5:
        return "Insufficient data"
    if dci is not None and dci < 0.40:
        return "Concern"
    flag_count = len([f for f in flags.split(";") if f.strip()])
    if dci is not None and dci < 0.65:
        return "Watch"
    if flag_count >= 2 or "Intake pressure" in flags:
        if dci is not None and dci >= 0.80:
            return "Solid"
        return "Watch"
    if dci is not None and dci >= 0.80 and zone in {"Healthy runway", "Watch band"}:
        return "Strong"
    if dci is not None and dci >= 0.65:
        return "Solid"
    return "Watch"


def trend_label(q1_dci: float | None, h1_dci: float | None) -> str:
    if q1_dci is None or h1_dci is None:
        return "n/a"
    delta = h1_dci - q1_dci
    if delta >= 0.15:
        return f"Improving (+{delta:.2f})"
    if delta <= -0.15:
        return f"Declining ({delta:.2f})"
    if abs(delta) < 0.05:
        return f"Stable ({delta:+.2f})"
    return f"Mixed ({delta:+.2f})"


def challenge_prompt(row: dict[str, str], tier: str, q1: dict[str, str] | None) -> str:
    name = row["writer_name"]
    dci = fnum(row.get("operational_dci"))
    finishes = int(fnum(row.get("work_finished")) or 0)
    flags = row.get("flag", "") or "None"
    prompts: list[str] = []

    if tier == "Strong":
        prompts.append(
            f"If rating below Exceeding: what challenging goals did {name} miss despite "
            f"strong throughput ({finishes} finishes, DCI {dci:.2f})?"
        )
    elif tier == "Solid":
        prompts.append(
            f"Solid operational profile (DCI {dci:.2f}, {finishes} finishes). "
            "What differentiates Achieving vs Exceeding for this person qualitatively?"
        )
    elif tier == "Watch":
        prompts.append(
            f"DCI {dci:.2f} with flags: {flags}. If proposing Exceeding/Exceptional, "
            "what evidence offsets operational inconsistency?"
        )
    elif tier == "Concern":
        prompts.append(
            f"Low DCI ({dci:.2f}) despite {finishes} finishes — likely backlog burn-down. "
            "If rating Achieving or above, how is sustained in-period performance demonstrated?"
        )
    elif tier == "Insufficient data":
        prompts.append(
            f"Only {finishes} finish(es) in H1 — rate on qualitative evidence only; "
            "confirm new-hire ramp status."
        )

    if q1:
        q1_dci = fnum(q1.get("operational_dci"))
        h1_dci = fnum(row.get("operational_dci"))
        if q1_dci is not None and h1_dci is not None:
            if h1_dci - q1_dci >= 0.20:
                prompts.append(
                    f"Q1 DCI was {q1_dci:.2f}; H1 is {h1_dci:.2f}. Confirm improvement is "
                    "sustained execution, not period-bound catch-up."
                )
            elif q1_dci - h1_dci >= 0.20:
                prompts.append(
                    f"Q1 DCI {q1_dci:.2f} vs H1 {h1_dci:.2f} — what caused the slip?"
                )

    if "avg_cycle_days" in row and fnum(row.get("avg_cycle_days")) and fnum(row["avg_cycle_days"]) > 100:
        prompts.append(
            f"Avg cycle {fnum(row['avg_cycle_days']):.0f} days — clarify if long-running tickets "
            "reflect standards work vs delivery delays."
        )

    return " ".join(prompts) if prompts else "No operational red flags; rely on qualitative goals and values."


def main() -> None:
    h1_path = ROOT / "out" / "h1-2026" / "dashboard" / "Tab2_Writer_Scorecard.csv"
    q1_path = ROOT / "out" / "q1-2026" / "dashboard" / "Tab2_Writer_Scorecard.csv"
    out_path = ROOT / "out" / "h1-2026" / "TW_Performance_Calibration_Pack.md"

    h1 = load_scorecard(h1_path)
    q1 = load_scorecard(q1_path) if q1_path.exists() else {}

    managers = {
        "Adam Christensen": [],
        "Danielle Biber": [],
        "Vita Gilin": [],
    }

    rows_analysis = []
    for name in sorted(h1.keys(), key=lambda n: fnum(h1[n].get("operational_dci")) or -1, reverse=True):
        row = h1[name]
        tier = evidence_tier(row)
        q1_row = q1.get(name)
        trend = trend_label(
            fnum(q1_row.get("operational_dci")) if q1_row else None,
            fnum(row.get("operational_dci")),
        )
        prompt = challenge_prompt(row, tier, q1_row)
        mgr = row.get("manager", "")
        if mgr in managers:
            managers[mgr].append((name, tier, row, trend, prompt))
        rows_analysis.append((name, tier, row, trend, prompt))

    tier_counts: dict[str, int] = {}
    for _, tier, _, _, _ in rows_analysis:
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    lines = [
        "# TW Performance Calibration Pack — H1 2026 (Jan 1 – Jun 30)",
        "",
        "**Purpose:** Org-level operational evidence to challenge or validate TL ratings from Adam, Danielle, and Vita.",
        "",
        "**Status:** TL proposed ratings not yet provided — operational evidence tier only.",
        "",
        "**Data source:** Fresh Jira export (`jira-export-Q2-2026.csv`) via DCI pipeline.",
        "",
        "> DCI measures load balance and throughput, **not** writing quality, collaboration, or values. "
        "Use this pack as one input alongside qualitative review.",
        "",
        "---",
        "",
        "## Executive snapshot",
        "",
        "| Metric | H1 2026 |",
        "|--------|---------|",
        "| Writers scored | 17 |",
        "| Work started | 710 |",
        "| Work finished | 1,123 |",
        "| Org operational DCI | 0.63 (backlog drain) |",
        "| AI adoption | 43.6% |",
        "| TW-AI field coverage | 80.4% |",
        "",
        "### Pod rollup",
        "",
        "| Pod | Manager | Writers | DCI | Finishes | AI adoption | Zone |",
        "|-----|---------|---------|-----|----------|-------------|------|",
        "| Pod 1 | Adam Christensen | 6 | 0.87 | 332 | 60.2% | Healthy runway |",
        "| Pod 2 | Danielle Biber | 7 | 0.69 | 523 | 46.3% | Backlog drain |",
        "| SOH | Vita Gilin | 4 | 0.22 | 268 | 17.9% | Backlog drain |",
        "",
        "**Calibration note:** Pod 1 shows the strongest operational profile. Pod 2 and SOH show backlog-drain patterns "
        "at the pod level — high finish counts often reflect backlog clearance, not in-period demand balance. "
        "Challenge any uniformly high ratings in Pod 2/SOH without qualitative justification.",
        "",
        "### Evidence tier distribution (operational only)",
        "",
    ]
    for tier in ["Strong", "Solid", "Watch", "Concern", "Insufficient data"]:
        lines.append(f"- **{tier}:** {tier_counts.get(tier, 0)} writers")

    lines.extend(["", "---", "", "## Writer scorecard (H1, sorted by DCI)", ""])
    lines.append(
        "| Writer | Manager | Pod | DCI | Finishes | Cycle (days) | AI % | Zone | Flags | Q1→H1 | Evidence tier |"
    )
    lines.append("|--------|---------|-----|-----|----------|--------------|------|------|-------|-------|---------------|")
    for name, tier, row, trend, _ in rows_analysis:
        dci = row.get("operational_dci", "")
        lines.append(
            f"| {name} | {row.get('manager','')} | {row.get('pod','')} | {dci} | "
            f"{row.get('work_finished','')} | {row.get('avg_cycle_days','')} | "
            f"{row.get('ai_adoption_pct','')}% | {row.get('dci_zone','')} | "
            f"{row.get('flag','') or '—'} | {trend} | **{tier}** |"
        )

    lines.extend(["", "---", "", "## Per-writer evidence cards", ""])

    for name, tier, row, trend, prompt in rows_analysis:
        lines.extend([
            f"### {name} ({row.get('pod')}, {row.get('manager')})",
            "",
            f"- **Evidence tier:** {tier}",
            f"- **Operational DCI:** {row.get('operational_dci')} | **Finishes:** {row.get('work_finished')} | "
            f"**Started:** {row.get('work_started')} | **Created:** {row.get('tickets_created')}",
            f"- **Cycle:** {row.get('avg_cycle_days')} days | **Queue lag:** {row.get('avg_queue_lag_days')} days",
            f"- **AI adoption:** {row.get('ai_adoption_pct')}% ({row.get('ai_finished')} AI / {row.get('manual_finished')} manual finishes)",
            f"- **Zone / flags:** {row.get('dci_zone')} — {row.get('flag') or 'none'}",
            f"- **Q1→H1 trend:** {trend}",
            f"- **Challenge prompt:** {prompt}",
            "",
        ])

    lines.extend(["---", "", "## TL calibration worksheets", ""])
    lines.extend([
        "When TLs submit proposed ratings, add a column and check alignment:",
        "- **Aligned** — operational tier matches proposed rating",
        "- **Stretch** — proposed rating higher than operational evidence supports",
        "- **Needs justification** — proposed rating lower than operational evidence; ask for specific behavioral gaps",
        "",
    ])

    for mgr, members in managers.items():
        pod_label = members[0][2].get("pod", "") if members else ""
        lines.extend([f"### {mgr}", ""])
        lines.append("| Writer | H1 DCI | Finishes | Evidence tier | Proposed rating | Alignment |")
        lines.append("|--------|--------|----------|---------------|-----------------|-----------|")
        for name, tier, row, _, prompt in sorted(members, key=lambda x: fnum(x[2].get("operational_dci")) or -1, reverse=True):
            lines.append(
                f"| {name} | {row.get('operational_dci')} | {row.get('work_finished')} | {tier} | _pending_ | _pending_ |"
            )
        lines.append("")
        lines.append("**Pre-loaded challenge questions for this pod:**")
        lines.append("")
        for name, tier, row, _, prompt in members:
            if tier in {"Watch", "Concern", "Insufficient data"} or tier == "Strong":
                lines.append(f"- **{name}:** {prompt}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Rating challenge reference",
        "",
        "| If TL proposes… | And operational evidence is… | Ask… |",
        "|-----------------|------------------------------|------|",
        "| Exceptional | Strong/Solid only | What initiative redefined possible beyond volume? |",
        "| Exceeding | Watch or Concern | What challenging goals were exceeded despite DCI/flags? |",
        "| Achieving | Strong with high finishes | Why not Exceeding if metrics are top-tier? |",
        "| Approaching | Strong/Solid | What specific inconsistency or ramp applies? |",
        "| Unsatisfactory | Solid or Strong | What collaboration/values failure overrides throughput? |",
        "",
        "---",
        "",
        "## Data caveats",
        "",
        "- **SOH cycle times** are inflated by long-running standards tickets (Yonit, Rivka) — do not compare directly to Pod execution writers.",
        "- **Orna Kenet, Rick Fox, Yonit Bisk, Rivka Teller** show high finishes with low DCI — likely backlog burn-down; challenge ratings tied to \"volume\" alone.",
        "- **Mike Ford** — 1 finish; insufficient operational data.",
        "- **Kate Reuveny** — H1 DCI 1.0 but only 25 finishes; Q1 was 0.14 — confirm ramp, not sustained high bar.",
        "- **New hires (Nov 4 – Jan 31):** Flag any names you identify; default to Approaching consideration unless evidence shows faster ramp.",
        "",
        "---",
        "",
        "## Next steps",
        "",
        "1. Share this pack with Adam, Danielle, and Vita before they finalize ratings.",
        "2. Collect proposed ratings per writer.",
        "3. Re-run alignment check (add ratings to worksheet above).",
        "4. Use challenge prompts in calibration meetings.",
        "",
        f"_Generated from `{h1_path.relative_to(ROOT)}`. Pipeline output: `out/h1-2026/`._",
        "",
    ])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(out_path), "writers": len(rows_analysis), "tier_counts": tier_counts}, indent=2))


if __name__ == "__main__":
    main()

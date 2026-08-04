"""Generate per-writer Capacity & Throughput canvas (.canvas.tsx) files."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERIODS = ["Q4 2025", "Q1 2026", "Q2 2026"]
PERIOD_LABELS = ["Oct–Dec 2025", "Jan–Mar 2026", "Apr–Jun 2026"]


def fnum(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt_num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    rounded = round(value, digits)
    if digits == 0:
        return str(int(rounded))
    text = f"{rounded:.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value, 1)}%"


def fmt_signed(value: float | None) -> str:
    if value is None:
        return "n/a"
    iv = int(round(value))
    return f"+{iv}" if iv > 0 else str(iv)


def js_num(value: float | None) -> str:
    if value is None:
        return "null"
    return f"{round(value, 4)}".rstrip("0").rstrip(".")


def js_array(values: list[float | None]) -> str:
    return "[" + ", ".join(js_num(v) for v in values) + "]"


def js_int_array(values: list[int]) -> str:
    return "[" + ", ".join(str(v) for v in values) + "]"


def pascal_case(writer_id: str) -> str:
    return "".join(part.capitalize() for part in writer_id.split("_"))


def callout_tone(dci: float | None, zone: str) -> str:
    if zone == "Healthy runway":
        return "info"
    if dci is not None and dci < 0.5:
        return "warning"
    if dci is not None and dci > 1.0:
        return "danger"
    return "success"


def load_scores(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return {row["writer_id"]: row for row in csv.DictReader(fh)}


def extract_tldr(briefing_path: Path) -> str:
    if not briefing_path.exists():
        return ""
    text = briefing_path.read_text(encoding="utf-8")
    match = re.search(r"## TL;DR\s+(.+?)\s+---", text, re.S)
    if not match:
        return ""
    return re.sub(r"\*\*", "", match.group(1)).strip()


def build_callout_title(row_q2: dict[str, str], scorecard: dict[str, str]) -> str:
    finishes = int(fnum(row_q2.get("active_capacity_realized")) or 0)
    dci = fnum(row_q2.get("operational_dci"))
    zone = scorecard.get("dci_zone", "")
    if zone == "Healthy runway":
        return f"Healthy runway — {finishes} resolved, DCI {fmt_num(dci, 2)}"
    if dci is not None and dci < 0.5:
        return f"Backlog burn-down — {finishes} resolved vs {int(fnum(row_q2.get('incoming_demand')) or 0)} started"
    return f"Q2 capacity profile — DCI {fmt_num(dci, 2)}, {finishes} resolved"


def series(rows: list[dict[str, str]], field: str, as_int: bool = False) -> list[float | None]:
    out: list[float | None] = []
    for row in rows:
        value = fnum(row.get(field))
        if value is None:
            out.append(None)
        elif as_int:
            out.append(float(int(round(value))))
        else:
            out.append(value)
    return out


def render_canvas(
    writer_id: str,
    rows: list[dict[str, str]],
    scorecard: dict[str, str],
    tldr: str,
) -> str:
    row_q2 = rows[2]
    name = row_q2["writer_name"]
    pod = row_q2["pod"]
    team = row_q2["team"]
    manager = row_q2["manager_name"]
    component = pascal_case(writer_id)
    dci_q2 = fnum(row_q2.get("operational_dci"))
    zone = scorecard.get("dci_zone", "")
    tone = callout_tone(dci_q2, zone)

    throughput = [int(fnum(r.get("active_capacity_realized")) or 0) for r in rows]
    demand = [int(fnum(r.get("incoming_demand")) or 0) for r in rows]
    intake = [int(fnum(r.get("intake_count")) or 0) for r in rows]
    dci = series(rows, "operational_dci")
    intake_dci = series(rows, "intake_dci")
    backlog = [int(round(fnum(r.get("backlog_pressure")) or 0)) for r in rows]
    queue_lag = series(rows, "avg_queue_lag_days")
    cycle_days = series(rows, "active_cycle_days")
    cycle_ai = series(rows, "active_cycle_days_ai")
    cycle_manual = series(rows, "active_cycle_days_manual")
    ai_adoption = series(rows, "ai_adoption_pct")
    ai_coverage = series(rows, "ai_field_coverage_pct")
    ai_finished = [int(fnum(r.get("ai_finished_count")) or 0) for r in rows]
    manual_finished = [int(fnum(r.get("manual_finished_count")) or 0) for r in rows]
    untagged_finished = [int(fnum(r.get("untagged_finished_count")) or 0) for r in rows]
    dci_ai = series(rows, "operational_dci_ai")
    dci_manual = series(rows, "operational_dci_manual")
    predictability = series(rows, "predictability_proxy")

    q2_finishes = throughput[2]
    q2_dci = fmt_num(dci_q2, 2)
    q2_ai = fmt_pct(fnum(row_q2.get("ai_adoption_pct")))
    q2_cycle = f"{fmt_num(fnum(row_q2.get('active_cycle_days')))}d"
    q2_queue = f"{fmt_num(fnum(row_q2.get('avg_queue_lag_days')))}d"

    stat_tone_dci = "success" if dci_q2 and dci_q2 < 0.85 else "warning"
    stat_tone_queue = "warning" if (fnum(row_q2.get("avg_queue_lag_days")) or 0) >= 60 else "success"

    table_rows = [
        '["Period", "Oct–Dec 2025", "Jan–Mar 2026", "Apr–Jun 2026"],',
        f'["Throughput (resolved)", "{throughput[0]}", "{throughput[1]}", "{throughput[2]}"],',
        f'["Incoming demand (started)", "{demand[0]}", "{demand[1]}", "{demand[2]}"],',
        f'["New intake (created)", "{intake[0]}", "{intake[1]}", "{intake[2]}"],',
        f'["DCI (demand ÷ capacity)", "{fmt_num(dci[0], 2)}", "{fmt_num(dci[1], 2)}", "{fmt_num(dci[2], 2)}"],',
        f'["Intake DCI", "{fmt_num(intake_dci[0], 2)}", "{fmt_num(intake_dci[1], 2)}", "{fmt_num(intake_dci[2], 2)}"],',
        f'["Backlog pressure", "{fmt_signed(float(backlog[0]))}", "{fmt_signed(float(backlog[1]))}", "{fmt_signed(float(backlog[2]))}"],',
        f'["Avg queue lag (days)", "{fmt_num(queue_lag[0])}", "{fmt_num(queue_lag[1])}", "{fmt_num(queue_lag[2])}"],',
        f'["Avg cycle time (days)", "{fmt_num(cycle_days[0])}", "{fmt_num(cycle_days[1])}", "{fmt_num(cycle_days[2])}"],',
        f'["Cycle time — AI (days)", "{fmt_num(cycle_ai[0])}", "{fmt_num(cycle_ai[1])}", "{fmt_num(cycle_ai[2])}"],',
        f'["Cycle time — manual (days)", "{fmt_num(cycle_manual[0])}", "{fmt_num(cycle_manual[1])}", "{fmt_num(cycle_manual[2])}"],',
        f'["AI adoption %", "{fmt_pct(ai_adoption[0])}", "{fmt_pct(ai_adoption[1])}", "{fmt_pct(ai_adoption[2])}"],',
        f'["AI field coverage %", "{fmt_pct(ai_coverage[0])}", "{fmt_pct(ai_coverage[1])}", "{fmt_pct(ai_coverage[2])}"],',
        f'["AI-assisted resolved", "{ai_finished[0]}", "{ai_finished[1]}", "{ai_finished[2]}"],',
        f'["Manual resolved", "{manual_finished[0]}", "{manual_finished[1]}", "{manual_finished[2]}"],',
        f'["Untagged resolved", "{untagged_finished[0]}", "{untagged_finished[1]}", "{untagged_finished[2]}"],',
        f'["DCI (AI work type)", "{fmt_num(dci_ai[0], 2)}", "{fmt_num(dci_ai[1], 2)}", "{fmt_num(dci_ai[2], 2)}"],',
        f'["DCI (manual work type)", "{fmt_num(dci_manual[0], 2)}", "{fmt_num(dci_manual[1], 2)}", "{fmt_num(dci_manual[2], 2)}"],',
        f'["Predictability proxy", "{fmt_num(predictability[0], 2)}", "{fmt_num(predictability[1], 2)}", "{fmt_num(predictability[2], 2)}"],',
    ]

    callout_body = tldr or (
        f"{name} resolved {q2_finishes} tickets in Q2 with operational DCI {q2_dci} "
        f"({zone or 'n/a'}). AI adoption {q2_ai}; avg cycle {q2_cycle}; queue lag {q2_queue}."
    )
    callout_body = callout_body.replace('"', '\\"')

    return f"""import {{
  BarChart,
  LineChart,
  Stack,
  Grid,
  H1,
  H2,
  Text,
  Stat,
  Card,
  CardHeader,
  CardBody,
  Callout,
  Table,
  Divider,
}} from "cursor/canvas";

// DATA_VERSION: 2026-07-09-q2-mcp (regenerate via scripts/build_capacity_canvases.py)
const DATA_VERSION = "2026-07-09-q2-sp";

const PERIODS = {json.dumps(PERIODS)};

const data = {{
  throughput:        {js_int_array(throughput)},
  demand:            {js_int_array(demand)},
  intake:            {js_int_array(intake)},
  dci:               {js_array(dci)},
  intakeDci:         {js_array(intake_dci)},
  backlogPressure:   {js_int_array(backlog)},
  queueLag:          {js_array(queue_lag)},
  cycleDays:         {js_array(cycle_days)},
  cycleDaysAI:       {js_array(cycle_ai)},
  cycleDaysManual:   {js_array(cycle_manual)},
  aiAdoptionPct:     {js_array(ai_adoption)},
  aiCoveragePct:     {js_array(ai_coverage)},
  aiFinished:        {js_int_array(ai_finished)},
  manualFinished:    {js_int_array(manual_finished)},
  untaggedFinished:  {js_int_array(untagged_finished)},
  dciAI:             {js_array(dci_ai)},
  dciManual:         {js_array(dci_manual)},
}};

export default function {component}() {{
  return (
    <Stack gap={{24}} style={{{{ padding: 24, maxWidth: 960 }}}}>

      <Stack gap={{4}}>
        <H1>{name} — Capacity & Throughput Analysis</H1>
        <Text tone="secondary">{pod} · {team} · Manager: {manager} · Oct 2025 – Jun 2026</Text>
      </Stack>

      <Callout tone="{tone}" title="{build_callout_title(row_q2, scorecard)}">
        {callout_body}
      </Callout>

      <Stack gap={{8}}>
        <Text tone="secondary" size="small">Q2 2026 (latest quarter)</Text>
        <Grid columns={{5}} gap={{16}}>
          <Stat value={{{q2_finishes}}} label="Tickets resolved" tone="success" />
          <Stat value="{q2_dci}" label="DCI (demand ÷ capacity)" tone="{stat_tone_dci}" />
          <Stat value="{q2_ai}" label="AI adoption" tone="info" />
          <Stat value="{q2_cycle}" label="Avg cycle time" tone="success" />
          <Stat value="{q2_queue}" label="Avg queue lag" tone="{stat_tone_queue}" />
        </Grid>
      </Stack>

      <Divider />

      <H2>Capacity & Throughput</H2>

      <Card>
        <CardHeader>Ticket volume by quarter (count)</CardHeader>
        <CardBody>
          <BarChart
            categories={{PERIODS}}
            series={{[
              {{ name: "Resolved (throughput)", data: data.throughput, tone: "success" }},
              {{ name: "Started (demand)", data: data.demand }},
              {{ name: "New intake (created)", data: data.intake, tone: "warning" }},
            ]}}
            height={{220}}
            showValues
          />
          <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
            Source: DCI pipeline v1.2.0 · Jira MCP export · Q4 2025 – Q2 2026
          </Text>
        </CardBody>
      </Card>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Operational DCI by quarter</CardHeader>
          <CardBody>
            <LineChart
              categories={{PERIODS}}
              series={{[
                {{ name: "DCI (demand ÷ capacity)", data: data.dci, tone: "success" }},
                {{ name: "Intake DCI (intake ÷ capacity)", data: data.intakeDci, tone: "warning" }},
              ]}}
              height={{180}}
              showValues
              referenceLines={{[{{ value: 1.0, label: "Balanced", tone: "neutral" }}]}}
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              DCI &lt; 1.0 = capacity exceeds demand. Source: DCI pipeline · Q4 2025 – Q2 2026
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Backlog pressure by quarter (tickets)</CardHeader>
          <CardBody>
            <BarChart
              categories={{PERIODS}}
              series={{[{{ name: "Backlog pressure (intake − started)", data: data.backlogPressure }}]}}
              height={{180}}
              showValues
              referenceLines={{[{{ value: 0, label: "Balanced", tone: "neutral" }}]}}
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              Positive = new tickets arriving faster than work is started. Source: DCI pipeline
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>Speed & Flow</H2>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Avg cycle time by quarter (days)</CardHeader>
          <CardBody>
            <LineChart
              categories={{PERIODS}}
              series={{[
                {{ name: "Overall avg (days)", data: data.cycleDays, tone: "info" }},
                {{ name: "AI-assisted (days)", data: data.cycleDaysAI }},
                {{ name: "Manual (days)", data: data.cycleDaysManual, tone: "neutral" }},
              ]}}
              height={{180}}
              showValues
              beginAtZero
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              StartWork to FinishWork for tickets active in each quarter. Source: DCI pipeline
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Avg queue lag by quarter (days)</CardHeader>
          <CardBody>
            <LineChart
              categories={{PERIODS}}
              series={{[{{ name: "Avg queue lag (days)", data: data.queueLag }}]}}
              height={{180}}
              showValues
              beginAtZero
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              Created to StartWork for tickets started in each quarter. Source: DCI pipeline
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>AI Adoption</H2>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>AI adoption by quarter (% of resolved)</CardHeader>
          <CardBody>
            <LineChart
              categories={{PERIODS}}
              series={{[
                {{ name: "AI adoption %", data: data.aiAdoptionPct, tone: "info" }},
                {{ name: "AI field coverage %", data: data.aiCoveragePct }},
              ]}}
              height={{180}}
              showValues
              valueSuffix="%"
              beginAtZero
              yMax={{100}}
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              Based on TW-AI Usage field on resolved tickets. Source: DCI pipeline
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Resolved output by type (ticket count)</CardHeader>
          <CardBody>
            <BarChart
              categories={{PERIODS}}
              series={{[
                {{ name: "AI-assisted", data: data.aiFinished, tone: "info" }},
                {{ name: "Manual", data: data.manualFinished }},
                {{ name: "Untagged", data: data.untaggedFinished, tone: "neutral" }},
              ]}}
              height={{180}}
              stacked
              showValues
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              Resolved tickets segmented by TW-AI Usage tagging. Source: DCI pipeline
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>Full Metrics by Quarter</H2>

      <Table
        headers={{["Metric", "Q4 2025", "Q1 2026", "Q2 2026"]}}
        columnAlign={{["left", "right", "right", "right"]}}
        striped
        rows={{[
          {chr(10).join('          ' + line for line in table_rows)}
        ]}}
      />

      <Text tone="tertiary" size="small">
        Source: DCI pipeline v1.2.0 · Jira MCP export Q2 2026 · Q4/Q1 historical runs · {{DATA_VERSION}}
      </Text>

    </Stack>
  );
}}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build capacity analysis canvas files.")
    parser.add_argument(
        "--canvases-dir",
        default=str(
            Path.home()
            / ".cursor"
            / "projects"
            / "c-Users-yserota-Documents-Cursor-AI-dci-agent"
            / "canvases"
        ),
    )
    parser.add_argument("--q4-scores", default="out/q4-2025/dci_writer_scores.csv")
    parser.add_argument("--q1-scores", default="out/q1-2026/dci_writer_scores.csv")
    parser.add_argument("--q2-scores", default="out/q2-2026/dci_writer_scores.csv")
    parser.add_argument("--scorecard", default="out/q2-2026/dashboard/Tab2_Writer_Scorecard.csv")
    parser.add_argument("--briefings-dir", default="out/q2-2026/capacity_briefings")
    args = parser.parse_args()

    q4 = load_scores(ROOT / args.q4_scores)
    q1 = load_scores(ROOT / args.q1_scores)
    q2 = load_scores(ROOT / args.q2_scores)

    with (ROOT / args.scorecard).open(encoding="utf-8", newline="") as fh:
        scorecards = {row["writer_name"]: row for row in csv.DictReader(fh)}

    canvases_dir = Path(args.canvases_dir)
    canvases_dir.mkdir(parents=True, exist_ok=True)
    briefings_dir = ROOT / args.briefings_dir

    written: list[str] = []
    for writer_id in sorted(q2.keys()):
        rows = [q4[writer_id], q1[writer_id], q2[writer_id]]
        name = rows[2]["writer_name"]
        manager = rows[2]["manager_name"].split()[0]
        briefing_name = f"{name.replace(' ', '_')}_Briefing_for_{manager}.md"
        tldr = extract_tldr(briefings_dir / briefing_name)
        scorecard = scorecards.get(name, {})
        content = render_canvas(writer_id, rows, scorecard, tldr)
        out_path = canvases_dir / f"{writer_id.replace('_', '-')}-capacity-analysis.canvas.tsx"
        out_path.write_text(content, encoding="utf-8")
        written.append(str(out_path))

    print(json.dumps({"writers": len(written), "canvases_dir": str(canvases_dir), "files": written}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate the DCI SP-weighted dashboard canvas (.canvas.tsx)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANVASES_DIR = (
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-yserota-Documents-Cursor-AI-dci-agent"
    / "canvases"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fnum(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    rounded = round(value, digits)
    if digits == 0:
        return str(int(rounded))
    text = f"{rounded:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{round(value, digits)}%"


def js_str(value: str) -> str:
    return json.dumps(value)


def js_num(value: float | None) -> str:
    if value is None:
        return "null"
    return f"{round(value, 4)}".rstrip("0").rstrip(".")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def dci_zone_label(dci: float | None) -> str:
    if dci is None:
        return "n/a"
    if dci > 1.0:
        return "Backlog building"
    if 0.80 <= dci <= 0.95:
        return "Healthy runway"
    if dci < 0.75:
        return "Backlog drain"
    return "Watch band"


def dci_tone(dci: float | None) -> str:
    if dci is None:
        return "neutral"
    if 0.80 <= dci <= 0.95:
        return "success"
    if dci > 1.0:
        return "danger"
    if dci < 0.75:
        return "info"
    return "warning"


# ---------------------------------------------------------------------------
# Canvas renderer
# ---------------------------------------------------------------------------

def render_canvas(
    writer_rows: list[dict[str, str]],
    team_rows: list[dict[str, str]],
    manager_rows: list[dict[str, str]],
    period_override: str = "",
    scope_label: str = "",
) -> str:
    # Org-level aggregates from writer scores
    sp_started_total = sum(fnum(r.get("story_points_started")) or 0.0 for r in writer_rows)
    sp_finished_total = sum(fnum(r.get("story_points_finished")) or 0.0 for r in writer_rows)
    org_sp_dci = sp_started_total / sp_finished_total if sp_finished_total else None
    tickets_started_total = int(sum(fnum(r.get("incoming_demand")) or 0.0 for r in writer_rows))
    tickets_finished_total = int(sum(fnum(r.get("active_capacity_realized")) or 0.0 for r in writer_rows))
    org_ticket_dci = tickets_started_total / tickets_finished_total if tickets_finished_total else None
    ai_finished_total = int(sum(fnum(r.get("ai_finished_count")) or 0.0 for r in writer_rows))
    org_ai_adoption = (ai_finished_total / tickets_finished_total * 100) if tickets_finished_total else None

    # SP coverage — weighted average across writers
    coverages = [fnum(r.get("story_points_coverage_pct")) for r in writer_rows]
    valid_coverages = [c for c in coverages if c is not None]
    org_sp_coverage = sum(valid_coverages) / len(valid_coverages) if valid_coverages else None
    coverage_badge_tone = "success" if (org_sp_coverage or 0) >= 70 else "warning"

    period = period_override
    if not period and writer_rows:
        start = writer_rows[0].get("period_start", "")
        end = writer_rows[0].get("period_end", "")
        period = f"{start} to {end}" if start and end else (start or end)
    run_date = ""
    if writer_rows:
        run_date = (writer_rows[0].get("computed_at_utc") or "")[:10]

    subtitle_parts = [period]
    if scope_label:
        subtitle_parts.append(f"Scope: {scope_label}")
    subtitle_parts.append(f"Generated {run_date}")
    subtitle = " · ".join(p for p in subtitle_parts if p)

    # Per-writer table rows sorted by SP DCI descending
    sorted_writers = sorted(
        writer_rows,
        key=lambda r: fnum(r.get("operational_dci_points")) or 0.0,
        reverse=True,
    )
    writer_table_rows = _build_writer_table_rows(sorted_writers)

    # Team chart & table
    team_names = [r.get("group", "") for r in team_rows]
    team_sp_dci_values = [fnum(r.get("story_points_dci")) for r in team_rows]
    team_ticket_dci_values = [fnum(r.get("operational_dci")) for r in team_rows]
    team_table_rows = _build_group_table_rows(team_rows)

    # Manager chart & table
    manager_names = [r.get("group", "") for r in manager_rows]
    manager_sp_dci_values = [fnum(r.get("story_points_dci")) for r in manager_rows]
    manager_ticket_dci_values = [fnum(r.get("operational_dci")) for r in manager_rows]
    manager_table_rows = _build_group_table_rows(manager_rows)

    headline_tone = dci_tone(org_sp_dci)
    sp_dci_str = fmt(org_sp_dci)
    ticket_dci_str = fmt(org_ticket_dci)
    sp_coverage_str = fmt_pct(org_sp_coverage)

    return f"""\
import {{
  BarChart,
  Stack,
  Grid,
  H1,
  H2,
  H3,
  Text,
  Stat,
  Card,
  CardHeader,
  CardBody,
  Callout,
  Table,
  Divider,
}} from "cursor/canvas";

const PERIOD = {js_str(period)};
const RUN_DATE = {js_str(run_date)};

const teamData = {{
  names: {json.dumps(team_names)},
  spDci: {json.dumps([js_num(v) for v in team_sp_dci_values]).replace('"', '')},
  ticketDci: {json.dumps([js_num(v) for v in team_ticket_dci_values]).replace('"', '')},
}};

const managerData = {{
  names: {json.dumps(manager_names)},
  spDci: {json.dumps([js_num(v) for v in manager_sp_dci_values]).replace('"', '')},
  ticketDci: {json.dumps([js_num(v) for v in manager_ticket_dci_values]).replace('"', '')},
}};

export default function DciSpDashboard() {{
  return (
    <Stack gap={{24}} style={{{{ padding: 24, maxWidth: 1100 }}}}>

      <Stack gap={{4}}>
        <H1>TW DCI — Story-Point-Weighted Dashboard</H1>
        <Text tone="secondary">{subtitle}</Text>
      </Stack>

      <Callout tone="{headline_tone}" title="Org SP-Weighted DCI: {sp_dci_str}">
        Story-point DCI {sp_dci_str} (primary) · Ticket DCI {ticket_dci_str} · {len(writer_rows)} writers scored · {tickets_finished_total} tickets finished
      </Callout>

      <Grid columns={{5}} gap={{16}}>
        <Stat value="{sp_dci_str}" label="SP DCI — primary" tone="{headline_tone}" />
        <Stat value="{ticket_dci_str}" label="Ticket DCI" tone="{dci_tone(org_ticket_dci)}" />
        <Stat value="{fmt_pct(org_ai_adoption)}" label="AI adoption" tone="info" />
        <Stat value="{sp_coverage_str}" label="SP coverage" tone="{coverage_badge_tone}" />
        <Stat value={{{len(writer_rows)}}} label="Writers scored" tone="neutral" />
      </Grid>

      <Divider />

      <H2>Per Technical Writer</H2>
      <Text tone="secondary" size="small">
        Sorted by SP-weighted DCI descending. SP DCI = story_points_started ÷ story_points_finished.
        SP Coverage = % of tickets with explicit Story Points (≥70% = reliable SP DCI). n/a = no story points tagged.
      </Text>

      <Table
        headers={{["Writer", "Manager", "SP Started", "SP Finished", "SP DCI", "SP Cov%", "Ticket DCI", "AI Adoption", "Zone"]}}
        columnAlign={{["left", "left", "right", "right", "right", "right", "right", "right", "left"]}}
        striped
        rows={{[
{writer_table_rows}
        ]}}
      />

      <Divider />

      <H2>By Team</H2>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>SP-Weighted DCI by Team</CardHeader>
          <CardBody>
            <BarChart
              categories={{teamData.names}}
              series={{[
                {{ name: "SP-Weighted DCI", data: teamData.spDci, tone: "success" }},
                {{ name: "Ticket DCI", data: teamData.ticketDci }},
              ]}}
              height={{200}}
              showValues
              referenceLines={{[{{ value: 1.0, label: "Balanced", tone: "neutral" }}]}}
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              SP DCI = sum(SP started) ÷ sum(SP finished) for each team. Source: DCI pipeline · {{PERIOD}}
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Team Rollup Metrics</CardHeader>
          <CardBody>
            <Table
              headers={{["Team", "Writers", "SP DCI", "Ticket DCI", "AI Adoption", "Zone"]}}
              columnAlign={{["left", "right", "right", "right", "right", "left"]}}
              striped
              rows={{[
{team_table_rows}
              ]}}
            />
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>By Manager Group</H2>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>SP-Weighted DCI by Manager</CardHeader>
          <CardBody>
            <BarChart
              categories={{managerData.names}}
              series={{[
                {{ name: "SP-Weighted DCI", data: managerData.spDci, tone: "success" }},
                {{ name: "Ticket DCI", data: managerData.ticketDci }},
              ]}}
              height={{200}}
              showValues
              referenceLines={{[{{ value: 1.0, label: "Balanced", tone: "neutral" }}]}}
            />
            <Text tone="secondary" size="small" style={{{{ marginTop: 8 }}}}>
              SP DCI = sum(SP started) ÷ sum(SP finished) per manager group. Source: DCI pipeline · {{PERIOD}}
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Manager Group Rollup Metrics</CardHeader>
          <CardBody>
            <Table
              headers={{["Manager", "Writers", "SP DCI", "Ticket DCI", "AI Adoption", "Zone"]}}
              columnAlign={{["left", "right", "right", "right", "right", "left"]}}
              striped
              rows={{[
{manager_table_rows}
              ]}}
            />
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>Metrics Guide</H2>
      <Text tone="secondary" size="small">Definitions for every metric shown in this dashboard.</Text>

      <Grid columns={{2}} gap={{16}}>
        <Card>
          <CardHeader>Primary Metrics</CardHeader>
          <CardBody>
            <Stack gap={{12}}>
              <Stack gap={{4}}>
                <H3>SP DCI (Story-Point DCI) — primary</H3>
                <Text size="small"><strong>Formula:</strong> story_points_started ÷ story_points_finished</Text>
                <Text size="small">The complexity-adjusted throughput ratio. Accounts for ticket difficulty — a writer finishing high-complexity work at a sustainable pace scores correctly even if raw ticket counts look low. Use SP DCI as the primary signal when SP Coverage ≥ 70%.</Text>
              </Stack>
              <Stack gap={{4}}>
                <H3>Ticket DCI — secondary</H3>
                <Text size="small"><strong>Formula:</strong> tickets_started ÷ tickets_resolved</Text>
                <Text size="small">The raw ticket-count throughput ratio. Use as a cross-check when SP Coverage is below 70%, or to compare writers who consistently have untagged Story Points.</Text>
              </Stack>
              <Stack gap={{4}}>
                <H3>SP Coverage %</H3>
                <Text size="small"><strong>Formula:</strong> tickets_with_explicit_story_points ÷ total_tickets × 100</Text>
                <Text size="small">Reliability indicator for SP DCI. When coverage is below 70%, tickets without Story Points are weighted at the default of 1.0, which may skew SP DCI. Improve coverage by tagging Story Points in Jira.</Text>
              </Stack>
              <Stack gap={{4}}>
                <H3>Missing SP default</H3>
                <Text size="small">Tickets with no Story Points value in Jira are automatically assigned a weight of <strong>1.0</strong> in all SP DCI calculations. This is a neutral assumption — it neither inflates nor deflates SP DCI — but high proportions of untagged tickets reduce the metric's precision.</Text>
              </Stack>
            </Stack>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Supporting Metrics and DCI Zones</CardHeader>
          <CardBody>
            <Stack gap={{12}}>
              <Stack gap={{4}}>
                <H3>AI Adoption %</H3>
                <Text size="small"><strong>Formula:</strong> tickets_finished_with_TW_AI_usage ÷ total_tickets_finished × 100</Text>
                <Text size="small">Percentage of finished tickets where the writer used an AI tool (TW-AI Usage field in Jira ≠ "No usage" / "Manual"). Untagged tickets are counted as neither AI nor manual.</Text>
              </Stack>
              <Stack gap={{4}}>
                <H3>Confidence Score</H3>
                <Text size="small"><strong>Range:</strong> 0.0 – 1.0. Starts at 1.0 with penalties applied:</Text>
                <Text size="small">−0.2 for a partial reporting window · −0.1 for missing optional fields · −0.15 for missing intake fields. A score below 0.6 means the writer's metrics may be incomplete.</Text>
              </Stack>
              <Divider />
              <Stack gap={{4}}>
                <H3>DCI Zones</H3>
                <Text size="small">Applies to both SP DCI and Ticket DCI:</Text>
                <Table
                  headers={{["Zone", "SP DCI value", "Meaning"]}}
                  columnAlign={{["left", "right", "left"]}}
                  rows={{[
                    ["Backlog building", "> 1.0", "Starting more than finishing — backlog grows"],
                    ["Healthy runway", "0.80 – 0.95", "Sustainable throughput with a modest buffer"],
                    ["Watch band", "0.75 – 0.80", "Marginal — monitor closely"],
                    ["Backlog drain", "< 0.75", "Finishing more than starting — backlog shrinks"],
                  ]}}
                />
              </Stack>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Text tone="tertiary" size="small">
        Source: DCI pipeline · Jira MCP export · {{PERIOD}} · Generated {{RUN_DATE}}
      </Text>

    </Stack>
  );
}}
"""


def _build_writer_table_rows(rows: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for row in rows:
        name = row.get("writer_name", "")
        manager = (row.get("manager_name") or "").split()[0] if row.get("manager_name") else ""
        sp_started = fmt(fnum(row.get("story_points_started")), 1)
        sp_finished = fmt(fnum(row.get("story_points_finished")), 1)
        sp_dci_raw = fnum(row.get("operational_dci_points"))
        sp_dci = fmt(sp_dci_raw)
        sp_coverage = fmt_pct(fnum(row.get("story_points_coverage_pct")))
        ticket_dci_raw = fnum(row.get("operational_dci"))
        ticket_dci = fmt(ticket_dci_raw)
        ai_adoption = fmt_pct(fnum(row.get("ai_adoption_pct")))
        zone = dci_zone_label(sp_dci_raw if sp_dci_raw is not None else ticket_dci_raw)
        lines.append(
            f'          [{js_str(name)}, {js_str(manager)}, {js_str(sp_started)}, '
            f'{js_str(sp_finished)}, {js_str(sp_dci)}, {js_str(sp_coverage)}, '
            f'{js_str(ticket_dci)}, {js_str(ai_adoption)}, {js_str(zone)}],'
        )
    return "\n".join(lines)


def _build_group_table_rows(rows: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for row in rows:
        group = row.get("group", "")
        writers = str(row.get("writers", ""))
        sp_dci_raw = fnum(row.get("story_points_dci"))
        sp_dci = fmt(sp_dci_raw)
        ticket_dci_raw = fnum(row.get("operational_dci"))
        ticket_dci = fmt(ticket_dci_raw)
        ai_adoption = fmt_pct(fnum(row.get("ai_adoption_pct")))
        zone = dci_zone_label(sp_dci_raw if sp_dci_raw is not None else ticket_dci_raw)
        lines.append(
            f'                [{js_str(group)}, {js_str(writers)}, {js_str(sp_dci)}, '
            f'{js_str(ticket_dci)}, {js_str(ai_adoption)}, {js_str(zone)}],'
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _filter_rows_by_scope(
    rows: list[dict[str, str]],
    teams: list[str] | None,
    pods: list[str] | None,
    managers: list[str] | None,
) -> list[dict[str, str]]:
    """Filter writer score rows to the requested scope (OR logic across filter types)."""
    if not any([teams, pods, managers]):
        return rows
    result: list[dict[str, str]] = []
    for row in rows:
        if teams and row.get("team") in teams:
            result.append(row)
            continue
        if pods and row.get("pod") in pods:
            result.append(row)
            continue
        if managers and row.get("manager_name") in managers:
            result.append(row)
    return result


def _build_scope_label(teams: list[str] | None, pods: list[str] | None, managers: list[str] | None) -> str:
    parts: list[str] = []
    if teams:
        parts.append(", ".join(teams))
    if pods:
        parts.append(", ".join(pods))
    if managers:
        parts.append(", ".join(managers))
    return " · ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DCI SP-weighted dashboard canvas.")
    parser.add_argument(
        "--output-dir",
        default="out",
        help="Directory containing dci_writer_scores.csv and dashboard/ tabs",
    )
    parser.add_argument(
        "--canvases-dir",
        default=str(CANVASES_DIR),
        help="Target canvases directory (Cursor-managed)",
    )
    parser.add_argument(
        "--period-start",
        default=None,
        help="Reporting period start (YYYY-MM-DD) — overrides value read from scores CSV",
    )
    parser.add_argument(
        "--period-end",
        default=None,
        help="Reporting period end (YYYY-MM-DD) — overrides value read from scores CSV",
    )
    parser.add_argument(
        "--teams",
        default=None,
        help="Comma-separated team names to scope the canvas (e.g. 'Execution,Standards')",
    )
    parser.add_argument(
        "--pods",
        default=None,
        help="Comma-separated pod names to scope the canvas (e.g. 'Pod 1,Pod 2')",
    )
    parser.add_argument(
        "--managers",
        default=None,
        help="Comma-separated manager names to scope the canvas (e.g. 'Adam Christensen')",
    )
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    scores_path = output_dir / "dci_writer_scores.csv"
    tab6_path = output_dir / "dashboard" / "Tab6_Team_Rollup.csv"
    tab7_path = output_dir / "dashboard" / "Tab7_Manager_Rollup.csv"

    for path in (scores_path, tab6_path, tab7_path):
        if not path.exists():
            raise SystemExit(
                f"Required input not found: {path}\n"
                "Run 'python scripts/run_dci_dashboard.py' first to generate outputs."
            )

    teams = _parse_csv_list(args.teams)
    pods = _parse_csv_list(args.pods)
    managers = _parse_csv_list(args.managers)

    writer_rows = load_csv(scores_path)
    team_rows = load_csv(tab6_path)
    manager_rows = load_csv(tab7_path)

    if not writer_rows:
        raise SystemExit(f"No writer scores found in {scores_path}")

    # Apply scope filter to writer rows (team/manager rollup tabs remain unfiltered
    # so their aggregates stay consistent with what the pipeline produced)
    writer_rows = _filter_rows_by_scope(writer_rows, teams=teams, pods=pods, managers=managers)
    if not writer_rows:
        raise SystemExit(
            "No writers remain after applying scope filter. "
            "Check --teams/--pods/--managers values against writer_manager_map.csv."
        )

    # Build period string (CLI override takes precedence over values in CSV)
    period_override = ""
    if args.period_start or args.period_end:
        start = args.period_start or ""
        end = args.period_end or ""
        period_override = f"{start} to {end}" if start and end else (start or end)

    scope_label = _build_scope_label(teams, pods, managers)

    canvases_dir = Path(args.canvases_dir)
    canvases_dir.mkdir(parents=True, exist_ok=True)

    canvas_path = canvases_dir / "dci-sp-dashboard.canvas.tsx"
    content = render_canvas(
        writer_rows,
        team_rows,
        manager_rows,
        period_override=period_override,
        scope_label=scope_label,
    )
    canvas_path.write_text(content, encoding="utf-8")

    result = {
        "canvas": str(canvas_path),
        "writers": len(writer_rows),
        "teams": len(team_rows),
        "manager_groups": len(manager_rows),
        "period": period_override or None,
        "scope": scope_label or None,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

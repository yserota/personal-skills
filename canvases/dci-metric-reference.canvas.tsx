import {
  Stack,
  Row,
  H1,
  H2,
  Text,
  Code,
  Card,
  CardHeader,
  CardBody,
  Table,
  Divider,
  Pill,
  Callout,
  CollapsibleSection,
} from "cursor/canvas";

interface Metric {
  name: string;
  formula: string;
  definition: string;
  howToRead: string;
  note?: string;
}

const PRIMARY: Metric[] = [
  {
    name: "SP DCI — Story-Point-Weighted DCI (primary)",
    formula: "story_points_started ÷ story_points_finished",
    definition:
      "The primary DCI metric. Each ticket is weighted by its Jira Story Points value, so complex tickets count proportionally more than simple ones. Measures whether the complexity-weighted volume of work started is balanced with the complexity-weighted volume finished in the reporting window.",
    howToRead:
      "0.80–0.95 is the healthy runway. Above 1.0 means the backlog builds (more complexity entering than closing). Below 0.75 means the backlog is shrinking faster than new work arrives. SP DCI is most meaningful when SP Coverage % is ≥ 70%.",
    note:
      "Tickets without Story Points are assigned a default weight of 1.0. When SP Coverage % is below 70%, this default carries significant influence — switch to Ticket DCI as the primary metric and flag for Jira hygiene on the Story Points field.",
  },
  {
    name: "Ticket DCI — Unweighted DCI (secondary)",
    formula: "tickets_started ÷ tickets_resolved",
    definition:
      "The secondary, unweighted DCI metric. Every ticket counts equally regardless of complexity. Use this when Story Points coverage is low (< 70%) or as a cross-check alongside SP DCI.",
    howToRead:
      "Same four zones as SP DCI. Significant divergence between Ticket DCI and SP DCI signals a complexity-mix shift — the writer may be starting heavier tickets than they are finishing (or vice versa).",
  },
];

const AI_METRICS: Metric[] = [
  {
    name: "AI Adoption %",
    formula: "ai_finished_count ÷ all_finished",
    definition:
      "Share of all finished tickets in the reporting window that carry an AI usage tag in the Jira TW-AI Usage field. The broadest measure of AI-assisted output.",
    howToRead:
      "Higher = more AI-assisted completions. Track period-over-period to monitor adoption trends across the team.",
  },
  {
    name: "AI Adoption % (tagged only)",
    formula: "ai_finished_count ÷ (ai_finished + manual_finished)",
    definition:
      "AI share calculated only over tickets where the TW-AI Usage field is explicitly set to either AI or Manual. Excludes tickets with blank fields.",
    howToRead:
      "More precise than overall AI Adoption % when field coverage is high (≥ 80%). When coverage is low, the standard AI Adoption % is more conservative and appropriate.",
  },
  {
    name: "TW-AI Field Coverage",
    formula: "(ai_finished + manual_finished) ÷ all_finished",
    definition:
      "Share of finished tickets where the TW-AI Usage field has any explicit value (AI or Manual). This is the primary reliability indicator for all AI segmentation metrics.",
    howToRead:
      "Low coverage = interpret AI adoption metrics cautiously. Blank TW-AI fields are counted as neither AI nor manual, understating both segments.",
  },
  {
    name: "DCI AI and DCI Manual",
    formula: "ai_started ÷ ai_finished   ·   manual_started ÷ manual_finished",
    definition:
      "The DCI ratio computed separately for AI-tagged tickets and manually-worked tickets. Reveals whether load imbalance is concentrated in one segment.",
    howToRead:
      "Same zones as overall DCI. Only compare segments when each has ≥ 5 finishes in the period — small counts produce unreliable ratios.",
  },
  {
    name: "DCI AI vs Manual Delta",
    formula: "operational_dci_ai − operational_dci_manual",
    definition:
      "Difference between the AI-segment and manual-segment DCI ratios. Positive means AI-tagged work has a greater backlog-building pressure relative to manual work.",
    howToRead:
      "Positive = AI segment builds backlog faster than manual. Negative = AI segment closes more efficiently. Only meaningful when each segment has ≥ 5 finishes.",
  },
  {
    name: "Cycle AI vs Manual Delta",
    formula: "avg_cycle_days_ai − avg_cycle_days_manual",
    definition:
      "Difference in average start-to-finish duration between AI-tagged and manually-worked tickets.",
    howToRead:
      "Positive = AI tickets take longer on average. Negative = AI speeds up cycle time. Pair with AI Adoption % to contextualize the tradeoff.",
  },
];

const INTAKE_METRICS: Metric[] = [
  {
    name: "Intake DCI",
    formula: "tickets_created ÷ tickets_finished",
    definition:
      "Ratio of new tickets entering the queue in the period to tickets completed. Measures whether incoming demand is outpacing the team's throughput, independent of what was already in progress at the period start.",
    howToRead:
      "> 1.0 = more tickets entering than closing — the overall queue grows. Does not require knowing the prior backlog size.",
  },
  {
    name: "Intake DCI (points)",
    formula: "story_points_intake ÷ story_points_finished",
    definition:
      "Story-point-weighted version of Intake DCI. Accounts for the complexity of incoming tickets, not just the raw count.",
    howToRead:
      "> 1.0 = heavier incoming work than closes. Compare to Intake DCI (tickets) to detect complexity-mix shifts in new demand.",
  },
  {
    name: "Backlog Pressure",
    formula: "tickets_created − tickets_started",
    definition:
      "Direct measure of queue buildup: new tickets arriving minus tickets actually picked up in the same window. Measures the net accumulation of unstarted work.",
    howToRead:
      "Positive = tickets accumulating unstarted. Negative = more picked up than arrived (queue clearing). Rising pressure alongside Intake DCI > 1.0 signals compounding risk.",
  },
  {
    name: "Avg Queue Lag Days",
    formula: "average(StartWork − Created)",
    definition:
      "Average number of days between a ticket being created and a writer starting work on it. Measures responsiveness to incoming demand.",
    howToRead:
      "Higher = tickets sit longer before pickup. Combine with Backlog Pressure to distinguish between a slow-pickup pattern versus a large accumulated queue.",
  },
];

const RELIABILITY_METRICS: Metric[] = [
  {
    name: "SP Coverage %",
    formula: "tickets_with_SP ÷ tickets_in_DCI_numerator",
    definition:
      "Share of tickets counted in DCI that carry an explicit Jira Story Points value (not blank). The primary reliability indicator for SP DCI — it determines how much weight the 1.0 default carries.",
    howToRead:
      "≥ 70% = SP DCI is trustworthy as the primary metric. < 70% = the 1.0 default dominates; switch to Ticket DCI as primary and address Jira hygiene on the Story Points field.",
  },
  {
    name: "Confidence Score",
    formula: "1.0 minus penalties (floor 0.0)",
    definition:
      "A 0–1 score expressing overall calculation reliability for a given writer in a given period. Penalties are applied automatically based on data quality gaps.",
    howToRead:
      "Penalties: −0.20 partial window (writer joined or left mid-period), −0.10 missing optional fields, −0.15 missing intake fields. Scores below 0.6 warrant caution when interpreting that writer's metrics.",
  },
];

const THROUGHPUT_METRICS: Metric[] = [
  {
    name: "Avg Cycle Days",
    formula: "average(FinishWork − StartWork)",
    definition:
      "Average days from a writer starting a ticket to finishing it. Measures active in-progress duration only — excludes queue wait time before StartWork.",
    howToRead:
      "Lower = faster delivery. Pair with DCI: a high DCI with short cycle time indicates many tickets started quickly; a high DCI with long cycle time signals sustained overload where tickets finish slowly.",
  },
  {
    name: "Avg Story Points per Finish",
    formula: "story_points_finished ÷ tickets_finished",
    definition:
      "Average complexity weight of completed tickets. A proxy for the typical difficulty of work a writer handles in the period.",
    howToRead:
      "Higher = writer typically finishes heavier tickets. Contextualizes DCI — a healthy SP DCI with high SP/finish means complex work is absorbed sustainably.",
  },
];

const QUICK_REF_ROWS: [string, string, string][] = [
  ["SP DCI", "story_points_started ÷ story_points_finished", "0.80–0.95 healthy; > 1.0 backlog builds; < 0.75 drain"],
  ["Ticket DCI", "tickets_started ÷ tickets_resolved", "Same zones; use when SP coverage < 70%"],
  ["AI Adoption %", "ai_finished ÷ all_finished", "Higher = more AI-assisted completions"],
  ["AI Adoption % (tagged)", "ai_finished ÷ (ai + manual_finished)", "Use when TW-AI field coverage ≥ 80%"],
  ["TW-AI Field Coverage", "(ai + manual_finished) ÷ all_finished", "Low = interpret AI metrics cautiously"],
  ["DCI AI", "ai_started ÷ ai_finished", "Same zones; need ≥ 5 finishes per segment"],
  ["DCI Manual", "manual_started ÷ manual_finished", "Same zones; need ≥ 5 finishes per segment"],
  ["DCI AI vs Manual Delta", "DCI AI − DCI Manual", "Positive = AI segment more backlogged"],
  ["Cycle AI vs Manual Delta", "avg_cycle_days_ai − avg_cycle_days_manual", "Positive = AI tickets take longer"],
  ["Intake DCI", "tickets_created ÷ tickets_finished", "> 1.0 = queue growing"],
  ["Intake DCI (points)", "story_points_intake ÷ story_points_finished", "> 1.0 = heavier intake than closes"],
  ["Backlog Pressure", "tickets_created − tickets_started", "Positive = tickets accumulating unstarted"],
  ["Avg Queue Lag Days", "avg(StartWork − Created)", "Higher = slower pickup after creation"],
  ["SP Coverage %", "tickets_with_SP ÷ tickets_in_DCI", "< 70% = switch to Ticket DCI as primary"],
  ["Confidence Score", "1.0 minus penalties", "< 0.6 = interpret that writer's metrics with caution"],
  ["Avg Cycle Days", "avg(FinishWork − StartWork)", "Lower = faster in-progress delivery"],
  ["Avg SP per Finish", "story_points_finished ÷ tickets_finished", "Higher = heavier typical ticket complexity"],
];

function MetricEntry({ metric, first }: { metric: Metric; first: boolean }) {
  return (
    <Stack gap={8}>
      {!first && <Divider />}
      <Text weight="semibold">{metric.name}</Text>
      <Text tone="secondary">{metric.definition}</Text>
      <Row gap={8} align="center">
        <Text size="small" tone="tertiary" weight="medium">Formula</Text>
        <Code>{metric.formula}</Code>
      </Row>
      <Text size="small" tone="tertiary" italic>{metric.howToRead}</Text>
      {metric.note && <Callout tone="warning">{metric.note}</Callout>}
    </Stack>
  );
}

export default function DCIMetricReference() {
  return (
    <Stack gap={28} style={{ padding: 28, maxWidth: 880, margin: "0 auto" }}>

      {/* Header */}
      <Stack gap={8}>
        <Row gap={10} align="center">
          <H1>DCI Metric Reference</H1>
          <Pill size="sm">Formula v1.3.0</Pill>
        </Row>
        <Text tone="secondary">
          The <Text weight="semibold" as="span">Demand-to-Capacity Index (DCI)</Text> measures the
          ratio of work <Text weight="semibold" as="span">started</Text> to work{" "}
          <Text weight="semibold" as="span">finished</Text> in a reporting window. A value near 1.0
          means balanced flow. Above 1.0 the backlog grows; below 0.75 the backlog shrinks faster
          than new work arrives. <Text weight="semibold" as="span">SP DCI</Text> is the primary
          metric; <Text weight="semibold" as="span">Ticket DCI</Text> is the fallback when Story
          Points coverage falls below 70%.
        </Text>
      </Stack>

      {/* DCI Zones — always-visible key reference */}
      <Stack gap={10}>
        <H2>DCI Zones</H2>
        <Text size="small" tone="tertiary">
          Applied identically to SP DCI and Ticket DCI. Every DCI value maps to one of these four zones.
        </Text>
        <Table
          headers={["Value", "Zone", "What it means"]}
          rows={[
            ["> 1.0", "Backlog building", "More complexity starting than finishing — queue grows"],
            ["0.80–0.95", "Healthy runway", "Sustainable throughput with a modest backlog buffer"],
            ["0.75–0.80", "Watch band", "Marginal — monitor the trend closely"],
            ["< 0.75", "Backlog drain", "More finishing than starting — queue is shrinking"],
          ]}
          rowTone={["warning", "success", "info", "neutral"]}
          striped
          columnAlign={["left", "left", "left"]}
        />
      </Stack>

      <Divider />

      {/* Primary Metrics */}
      <Stack gap={12}>
        <H2>Primary Metrics</H2>
        <Card>
          <CardHeader>Execution metrics</CardHeader>
          <CardBody>
            <Stack gap={16}>
              {PRIMARY.map((m, i) => (
                <div key={m.name}><MetricEntry metric={m} first={i === 0} /></div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </Stack>

      {/* AI Segmentation */}
      <CollapsibleSection
        title="AI Segmentation Metrics"
        count={AI_METRICS.length}
        defaultOpen={true}
      >
        <Card style={{ marginTop: 8 }}>
          <CardBody>
            <Stack gap={16}>
              {AI_METRICS.map((m, i) => (
                <div key={m.name}><MetricEntry metric={m} first={i === 0} /></div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </CollapsibleSection>

      {/* Intake & Queue Health */}
      <CollapsibleSection
        title="Intake & Queue Health"
        count={INTAKE_METRICS.length}
        defaultOpen={false}
      >
        <Card style={{ marginTop: 8 }}>
          <CardBody>
            <Stack gap={16}>
              {INTAKE_METRICS.map((m, i) => (
                <div key={m.name}><MetricEntry metric={m} first={i === 0} /></div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </CollapsibleSection>

      {/* Reliability Indicators */}
      <CollapsibleSection
        title="Reliability Indicators"
        count={RELIABILITY_METRICS.length}
        defaultOpen={false}
      >
        <Card style={{ marginTop: 8 }}>
          <CardBody>
            <Stack gap={16}>
              {RELIABILITY_METRICS.map((m, i) => (
                <div key={m.name}><MetricEntry metric={m} first={i === 0} /></div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </CollapsibleSection>

      {/* Throughput & Complexity */}
      <CollapsibleSection
        title="Throughput & Complexity"
        count={THROUGHPUT_METRICS.length}
        defaultOpen={false}
      >
        <Card style={{ marginTop: 8 }}>
          <CardBody>
            <Stack gap={16}>
              {THROUGHPUT_METRICS.map((m, i) => (
                <div key={m.name}><MetricEntry metric={m} first={i === 0} /></div>
              ))}
            </Stack>
          </CardBody>
        </Card>
      </CollapsibleSection>

      <Divider />

      {/* Quick Reference Table */}
      <Stack gap={10}>
        <H2>Quick Reference</H2>
        <Text size="small" tone="tertiary">All 17 metrics, formulas, and reading guides at a glance.</Text>
        <Table
          headers={["Metric", "Formula", "How to read"]}
          rows={QUICK_REF_ROWS.map(([name, formula, read]) => [
            <Text weight="semibold" size="small" as="span">{name}</Text>,
            <Code>{formula}</Code>,
            <Text size="small" tone="secondary" as="span">{read}</Text>,
          ])}
          striped
          stickyHeader
          columnAlign={["left", "left", "left"]}
        />
      </Stack>

      <Text size="small" tone="tertiary" style={{ textAlign: "center" }}>
        Source: dci_formula.yaml v1.3.0 · Tab5_Metric_Definitions.csv
      </Text>

    </Stack>
  );
}

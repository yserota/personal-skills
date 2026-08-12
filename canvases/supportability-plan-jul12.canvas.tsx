import {
  Stack, Grid, Row, H1, H2, H3, Text, Card, CardHeader, CardBody,
  Table, Stat, Pill, Divider, Callout, CollapsibleSection, UsageBar,
  Link, useCanvasState,
} from "cursor/canvas";

const JIRA_BASE = "https://ca-il-jira.il.cyber-ark.com:8443/browse";
function jiraUrl(key: string) { return `${JIRA_BASE}/${key}`; }
function isRealKey(key: string) { return key.startsWith("DOC-"); }
function crossUrl(key: string) { return `${JIRA_BASE}/${key}`; }

type Coverage = "covered" | "partial" | "gap";
type TicketKind = "active" | "proposed" | "review";

type ProgramTicket = {
  key: string;
  driver: string;
  cross: string;
  summary: string;
  status: string;
  priority: string;
  writer: string;
  phase: string;
  kind: TicketKind;
  tier: string;
};

const driverRows = [
  { driver: "CPM_16", cross: "CROSS-462", product: "CPM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23868", phase: "FY27 Q1" },
  { driver: "CPM_17", cross: "CROSS-1060", product: "CPM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23094", phase: "FY27 Q1" },
  { driver: "CPM_17", cross: "CROSS-1059", product: "CPM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23094", phase: "FY27 Q1" },
  { driver: "CPM_21", cross: "CROSS-1063", product: "CPM", tier: "Tier 1", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23075", phase: "FY27 Q1" },
  { driver: "CPM_29", cross: "CROSS-1064", product: "CPM", tier: "Tier 1", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-21787", phase: "FY27 Q1" },
  { driver: "CPM_4", cross: "CROSS-1069", product: "CPM", tier: "Tier 1", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-22848/47", phase: "FY27 Q1" },
  { driver: "CPM_43", cross: "CROSS-1071", product: "CPM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23869", phase: "FY27 Q1" },
  { driver: "Identity_10", cross: "CROSS-320", product: "Identity", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23099 / DOC-23853", phase: "FY27 Q1" },
  { driver: "PSM_39", cross: "CROSS-1095", product: "PSM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23095", phase: "FY27 Q1" },
  { driver: "PSM_69", cross: "CROSS-1103", product: "PSM", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23095", phase: "FY27 Q1" },
  { driver: "PVWA_1", cross: "CROSS-368", product: "PVWA", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23096", phase: "FY27 Q1" },
  { driver: "PVWA_10", cross: "CROSS-1109", product: "PVWA", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23097", phase: "FY27 Q1" },
  { driver: "PVWA_19", cross: "CROSS-1114", product: "PVWA", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23097", phase: "FY27 Q1" },
  { driver: "PVWA_2", cross: "CROSS-369", product: "PVWA", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23098", phase: "FY27 Q1" },
  { driver: "Vault_18", cross: "CROSS-1131", product: "Vault", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23117", phase: "FY27 Q1" },
  { driver: "Vault_7", cross: "CROSS-1135", product: "Vault", tier: "Tier 1", priority: "High", coverage: "covered" as Coverage, existingDoc: "DOC-23118", phase: "FY27 Q1" },
  { driver: "CPM_11", cross: "CROSS-460", product: "CPM", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "CPM_14", cross: "CROSS-1055", product: "CPM", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "CPM_43", cross: "CROSS-1072", product: "CPM", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "EPM_0", cross: "CROSS-1075", product: "EPM", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "EPM_0", cross: "CROSS-1074", product: "EPM", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "EPM_27", cross: "CROSS-1135", product: "EPM", tier: "Tier 2/3", priority: "Low", coverage: "partial" as Coverage, existingDoc: "DOC-23118", phase: "FY27 Q3" },
  { driver: "Identity_1", cross: "CROSS-344", product: "Identity", tier: "Tier 2/3", priority: "Medium", coverage: "partial" as Coverage, existingDoc: "DOC-23103/22441", phase: "FY27 Q1" },
  { driver: "Identity_10", cross: "CROSS-319", product: "Identity", tier: "Tier 2/3", priority: "Medium", coverage: "partial" as Coverage, existingDoc: "DOC-23099/22039", phase: "FY27 Q1" },
  { driver: "Identity_15", cross: "CROSS-1044", product: "Identity", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "Identity_2", cross: "CROSS-328", product: "Identity", tier: "Tier 2/3", priority: "Medium", coverage: "covered" as Coverage, existingDoc: "DOC-23104", phase: "FY27 Q1" },
  { driver: "Identity_2", cross: "CROSS-1088", product: "Identity", tier: "Tier 2/3", priority: "High", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q2" },
  { driver: "Identity_22", cross: "CROSS-600", product: "Identity", tier: "Tier 2/3", priority: "Medium", coverage: "covered" as Coverage, existingDoc: "DOC-23102", phase: "FY27 Q1" },
  { driver: "Identity_22", cross: "CROSS-1089", product: "Identity", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "Identity_7", cross: "CROSS-1092", product: "Identity", tier: "Tier 2/3", priority: "Low", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "PSM_15", cross: "CROSS-479", product: "PSM", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "PSM_5", cross: "CROSS-1098", product: "PSM", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-22807", phase: "FY27 Q2" },
  { driver: "PSM_65", cross: "CROSS-1102", product: "PSM", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "PVWA_142", cross: "CROSS-1111", product: "PVWA", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "PVWA_158", cross: "CROSS-1113", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q2" },
  { driver: "PVWA_25", cross: "CROSS-1116", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23107", phase: "FY27 Q2" },
  { driver: "PVWA_3", cross: "CROSS-1118", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23118", phase: "FY27 Q2" },
  { driver: "PVWA_32", cross: "CROSS-1120", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23108", phase: "FY27 Q2" },
  { driver: "PVWA_32", cross: "CROSS-1126", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23108", phase: "FY27 Q2" },
  { driver: "PVWA_40", cross: "CROSS-1122", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23109", phase: "FY27 Q2" },
  { driver: "PVWA_45", cross: "CROSS-1124", product: "PVWA", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
  { driver: "PVWA_93", cross: "CROSS-1128", product: "PVWA", tier: "Tier 2/3", priority: "High", coverage: "partial" as Coverage, existingDoc: "DOC-23110", phase: "FY27 Q2" },
  { driver: "Vault_0", cross: "CROSS-130", product: "Vault", tier: "Tier 2/3", priority: "Medium", coverage: "gap" as Coverage, existingDoc: "", phase: "FY27 Q3" },
];

const programTickets: ProgramTicket[] = [
  { key: "DOC-23094", driver: "CPM_17", cross: "CROSS-1059/1060", summary: "Azure CPM plugin documentation - API permissions, app key rotation, error codes", status: "Open", priority: "High", writer: "Orna Kenet", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23095", driver: "PSM_39/69", cross: "CROSS-1095/1103", summary: "PSM-RDP troubleshooting guide - Windows config, error codes, disconnect handling", status: "Open", priority: "High", writer: "Orna Kenet", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23096", driver: "PVWA_1", cross: "CROSS-368", summary: "PVWA LDAP + cert management - error messages and troubleshooting steps", status: "Open", priority: "High", writer: "Elisha Khera", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23097", driver: "PVWA_10/19", cross: "CROSS-1109/1114", summary: "PVWA Safe access + safe members - recovery process and AD group guide", status: "Open", priority: "High", writer: "Elisha Khera", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23098", driver: "PVWA_2", cross: "CROSS-369", summary: "PVWA System hygiene - removing orphaned components and disconnected objects", status: "Open", priority: "High", writer: "Elisha Khera", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23099", driver: "Identity_10", cross: "CROSS-320", summary: "Identity service access troubleshooting - RBAC role mapping and post-auth access gaps", status: "Under Review", priority: "High", writer: "Sabrina Jess", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23853", driver: "Identity_10", cross: "CROSS-320", summary: "Identity login lockout troubleshooting - split from DOC-23099", status: "Done", priority: "High", writer: "Sabrina Jess", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23102", driver: "Identity_22", cross: "CROSS-600", summary: "SIEM integration guide - Splunk and Azure Sentinel supported versions", status: "Blocked", priority: "Medium", writer: "Gillian Candiloro", phase: "FY27 Q1", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23103", driver: "Identity_1", cross: "CROSS-344", summary: "RADIUS / VPN auth configuration supplement - if not covered by DOC-22441", status: "Blocked", priority: "Medium", writer: "Sabrina Jess", phase: "FY27 Q1", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23104", driver: "Identity_2", cross: "CROSS-328", summary: "Azure AD / Entra ID user provisioning guide - sync config and conditional access", status: "Open", priority: "High", writer: "Gillian Candiloro", phase: "FY27 Q1", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23105", driver: "Identity access", cross: "-", summary: "Identity access management error guide", status: "Closed", priority: "Medium", writer: "Gillian Candiloro", phase: "FY27 Q1", kind: "review", tier: "-" },
  { key: "DOC-23117", driver: "Vault_18", cross: "CROSS-1131", summary: "Privilege Cloud recording and log retention guide - default limits, storage management, compliance", status: "Open", priority: "High", writer: "Orna Kenet", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23118", driver: "Vault_7", cross: "CROSS-1135", summary: "Privilege Cloud email notifications and dual control workflow configuration guide", status: "Open", priority: "High", writer: "Elisha Khera", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23100", driver: "EPM_1", cross: "CROSS-309", summary: "JAMF / Intune macOS deployment expansion", status: "Closed", priority: "Medium", writer: "Steve Goodman", phase: "FY27 Q2", kind: "review", tier: "-" },
  { key: "DOC-23106", driver: "PVWA_9", cross: "-", summary: "[PLACEHOLDER] PVWA connectivity + PSM config", status: "Closed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q2", kind: "review", tier: "-" },
  { key: "DOC-23107", driver: "PVWA_25", cross: "CROSS-1116", summary: "[PLACEHOLDER] Login + auth error handling", status: "Open", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q2", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23108", driver: "PVWA_32", cross: "CROSS-1120/1126", summary: "[PLACEHOLDER] PCloud portal access failures", status: "Open", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q2", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23109", driver: "PVWA_40", cross: "CROSS-1122", summary: "[PLACEHOLDER] Orphaned safes recovery", status: "Open", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q2", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23110", driver: "PVWA_93", cross: "CROSS-1128", summary: "[PLACEHOLDER] Activity logging + reports", status: "Open", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q2", kind: "active", tier: "Tier 2/3" },
  { key: "DOC-23868", driver: "CPM_16", cross: "CROSS-462", summary: "CPM account reconciliation stuck / Linux SSH troubleshooting guide", status: "Open", priority: "High", writer: "Orna Kenet", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "DOC-23869", driver: "CPM_43", cross: "CROSS-1071", summary: "CPM Privilege Cloud_43 documentation - migration paths and version compatibility", status: "Open", priority: "High", writer: "Orna Kenet", phase: "FY27 Q1", kind: "active", tier: "Tier 1" },
  { key: "NEW-09", driver: "Identity_2", cross: "CROSS-1088", summary: "Azure secrets expiration visibility best practices", status: "Proposed", priority: "High", writer: "Gillian Candiloro", phase: "FY27 Q2", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-15", driver: "PVWA_158", cross: "CROSS-1113", summary: "PVWA offline access and component DR setup", status: "Proposed", priority: "High", writer: "Orna Kenet", phase: "FY27 Q2", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-03", driver: "CPM_11", cross: "CROSS-460", summary: "CPM password rotation plugin troubleshooting", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-04", driver: "CPM_14", cross: "CROSS-1055", summary: "CPM installation prerequisites v14 cleanup", status: "Proposed", priority: "Low", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-05", driver: "CPM_43", cross: "CROSS-1072", summary: "CPM missing docs for older versions", status: "Proposed", priority: "Low", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-06", driver: "EPM_0", cross: "CROSS-1075", summary: "EPM case-sensitive configuration", status: "Proposed", priority: "Low", writer: "Steve Goodman", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-07", driver: "EPM_0", cross: "CROSS-1074", summary: "EPM Secure Token vs Apple Secure Token", status: "Proposed", priority: "Low", writer: "Steve Goodman", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-08", driver: "Identity_15", cross: "CROSS-1044", summary: "Identity driver 15 supportability docs", status: "Proposed", priority: "Medium", writer: "Sabrina Jess", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-10", driver: "Identity_22", cross: "CROSS-1089", summary: "Identity SIEM system requirements", status: "Proposed", priority: "Low", writer: "Sabrina Jess", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-11", driver: "Identity_7", cross: "CROSS-1092", summary: "Identity default administrators clarification", status: "Proposed", priority: "Low", writer: "Sabrina Jess", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-12", driver: "PSM_15", cross: "CROSS-479", summary: "PSM certificate management troubleshooting", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-13", driver: "PSM_65", cross: "CROSS-1102", summary: "PSM timeout values clarification", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-14", driver: "PVWA_142", cross: "CROSS-1111", summary: "PVWA retention rules and tuning", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-16", driver: "PVWA_45", cross: "CROSS-1124", summary: "PVWA performance troubleshooting", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
  { key: "NEW-17", driver: "Vault_0", cross: "CROSS-130", summary: "Vault Privilege Cloud_0 supportability", status: "Proposed", priority: "Medium", writer: "Orna Kenet", phase: "FY27 Q3", kind: "proposed", tier: "Tier 2/3" },
];

const covered = driverRows.filter((r) => r.coverage === "covered").length;
const partial = driverRows.filter((r) => r.coverage === "partial").length;
const gaps = driverRows.filter((r) => r.coverage === "gap").length;

const q1 = programTickets.filter((t) => t.phase === "FY27 Q1");
const q2 = programTickets.filter((t) => t.phase === "FY27 Q2");
const q3 = programTickets.filter((t) => t.phase === "FY27 Q3");

function CrossLinks({ value }: { value: string }) {
  if (!value || value === "-") return <Text size="small">-</Text>;
  const parts = value.split("/");
  if (!parts[0].startsWith("CROSS-")) return <Text size="small">{value}</Text>;
  const keys = parts.map((p, i) =>
    i === 0 ? p : (p.startsWith("CROSS-") ? p : "CROSS-" + p)
  );
  if (keys.length === 1) {
    return <Link href={crossUrl(keys[0])}><Text size="small">{keys[0]}</Text></Link>;
  }
  return (
    <Row gap={4} align="center" wrap>
      {keys.map((k) => (
        <Link key={k} href={crossUrl(k)}><Text size="small">{k}</Text></Link>
      ))}
    </Row>
  );
}

function CoveragePill({ coverage }: { coverage: Coverage }) {
  const tone = coverage === "covered" ? "success" : coverage === "partial" ? "warning" : "danger";
  const label = coverage === "covered" ? "Covered" : coverage === "partial" ? "Partial" : "Gap";
  return <Pill size="sm" tone={tone} active={coverage === "gap"}>{label}</Pill>;
}

function KindPill({ kind }: { kind: TicketKind }) {
  const tone = kind === "proposed" ? "danger" : kind === "review" ? "warning" : "neutral";
  const label = kind === "proposed" ? "Proposed" : kind === "review" ? "Review" : "Active";
  return <Pill size="sm" tone={tone} active={kind !== "active"}>{label}</Pill>;
}

function QuarterTable({ tickets, title }: { tickets: ProgramTicket[]; title: string }) {
  return (
    <Stack gap={8}>
      <Row gap={8} align="center">
        <H3>{title}</H3>
        <Pill size="sm" active>{tickets.length} tickets</Pill>
      </Row>
      <Table
        headers={["Ticket", "Driver", "CROSS", "Writer", "Status"]}
        rows={tickets.map((t) => [
          <Stack gap={2}>
            <Text size="small" weight="semibold" tone={t.kind === "proposed" ? "secondary" : undefined}>
              {isRealKey(t.key) ? <Link href={jiraUrl(t.key)}>{t.key}</Link> : t.key}
              {" — "}{t.summary}
            </Text>
          </Stack>,
          <Text size="small">{t.driver}</Text>,
          <CrossLinks value={t.cross} />,
          <Text size="small">{t.writer}</Text>,
          <Row gap={4}>
            <Pill size="sm" tone={t.status === "Blocked" ? "warning" : t.status === "Proposed" ? "danger" : t.status === "Under Review" || t.status === "Done" ? "success" : "neutral"} active={t.status !== "Open"}>{t.status}</Pill>
            {t.kind !== "active" && <KindPill kind={t.kind} />}
          </Row>,
        ])}
        rowTone={tickets.map((t) => t.kind === "proposed" ? "danger" as const : t.kind === "review" ? "warning" as const : "neutral" as const)}
        striped
      />
    </Stack>
  );
}

export default function SupportabilityPlanJul12() {
  const [phaseFilter, setPhaseFilter] = useCanvasState<string>("phaseFilter", "All");

  const filteredProgram = phaseFilter === "All"
    ? programTickets
    : programTickets.filter((t) => t.phase === phaseFilter);

  return (
    <Stack gap={28} style={{ padding: 24, maxWidth: 1200 }}>

      <Stack gap={8}>
        <H1>Supportability Documentation Program</H1>
        <Text tone="secondary">Tableau Intake gap analysis · Aug 4, 2026 · FY27 Q1 started Aug 1, 2026</Text>
        <Row gap={8} wrap>
          <Pill size="sm" active>Phase: Gap closure + execution</Pill>
          <Pill size="sm">33 tickets after filing</Pill>
          <Pill size="sm" tone="danger" active>15 gaps to file</Pill>
        </Row>
      </Stack>

      <Callout tone="info" title="Plan summary">
        Full Tableau driver x CROSS matrix: 15 covered, 13 partial, 15 gaps. Program: 18 active tickets (1 Done, 1 Under Review, 2 Blocked) + 15 proposed = 33 total.
        DOC-23099 split: DOC-23853 (login lockout, Done) + DOC-23099 (service access, Under Review with Sivan). DOC-23102 and DOC-23103 Blocked. DOC-23100, DOC-23105, DOC-23106 Closed.
      </Callout>

      <Grid columns={5} gap={12}>
        <Stat value={43} label="Tableau doc rows" />
        <Stat value={covered} label="Covered" tone="success" />
        <Stat value={partial} label="Partial" tone="warning" />
        <Stat value={gaps} label="Gaps" tone="danger" />
        <Stat value={33} label="Program total" />
      </Grid>

      <Stack gap={6}>
        <H3>Tableau driver coverage by row</H3>
        <Text size="small" tone="tertiary">Source: Tableau Intake.xlsx · Jul 10, 2026 · 43 documentation rows</Text>
        <UsageBar
          segments={[
            { value: covered, label: "Covered", tone: "success" },
            { value: partial, label: "Partial", tone: "warning" },
            { value: gaps, label: "Gap", tone: "danger" },
          ]}
        />
      </Stack>

      <Grid columns={3} gap={12}>
        <Card>
          <CardHeader>FY27 Q1</CardHeader>
          <CardBody>
            <Stat value={14} label="Deliverables" />
            <Text size="small" tone="secondary">13 active + 1 Done (DOC-23853); DOC-23099 Under Review; DOC-23102 and DOC-23103 Blocked</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>FY27 Q2</CardHeader>
          <CardBody>
            <Stat value={6} label="Deliverables" />
            <Text size="small" tone="secondary">4 active + 2 high-priority gaps (DOC-23100, DOC-23106 closed)</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>FY27 Q3</CardHeader>
          <CardBody>
            <Stat value={13} label="Deliverables" />
            <Text size="small" tone="secondary">Remaining Tableau Tier 2/3 gaps</Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={16}>
        <H2>Program roadmap by quarter</H2>
        <QuarterTable tickets={q1} title="FY27 Q1 — Aug to Oct 2026" />
        <QuarterTable tickets={q2} title="FY27 Q2 — Nov 2026 to Jan 2027" />
        <QuarterTable tickets={q3} title="FY27 Q3 — Feb to Apr 2027" />
      </Stack>

      <CollapsibleSection title="Full program ticket list (33)" count={33}>
        <Stack gap={8} style={{ paddingTop: 8 }}>
          <Row gap={6} wrap>
            {["All", "FY27 Q1", "FY27 Q2", "FY27 Q3"].map((p) => (
              <Pill key={p} size="sm" active={phaseFilter === p} onClick={() => setPhaseFilter(p)}>{p}</Pill>
            ))}
          </Row>
          <Table
            headers={["Ticket", "Driver", "CROSS", "Phase", "Writer", "Kind"]}
            rows={filteredProgram.map((t) => [
              <Text size="small" weight="semibold">
                {isRealKey(t.key) ? <Link href={jiraUrl(t.key)}>{t.key}</Link> : t.key}
                {" — "}{t.summary}
              </Text>,
              <Text size="small">{t.driver}</Text>,
              <CrossLinks value={t.cross} />,
              <Text size="small">{t.phase}</Text>,
              <Text size="small">{t.writer}</Text>,
              <KindPill kind={t.kind} />,
            ])}
            striped
            stickyHeader
            style={{ maxHeight: 420 }}
          />
        </Stack>
      </CollapsibleSection>

      <CollapsibleSection title="Tableau gap matrix (43 rows)" count={43}>
        <Stack gap={8} style={{ paddingTop: 8 }}>
          <Table
            headers={["Driver", "CROSS", "Tier", "Coverage", "Existing DOC", "Phase"]}
            rows={driverRows.map((r) => [
              <Text size="small" weight="semibold">{r.driver}</Text>,
              <CrossLinks value={r.cross} />,
              <Text size="small">{r.tier}</Text>,
              <CoveragePill coverage={r.coverage} />,
              <Text size="small" tone={r.existingDoc ? "secondary" : "tertiary"}>{r.existingDoc || "-"}</Text>,
              <Text size="small">{r.phase}</Text>,
            ])}
            rowTone={driverRows.map((r) => r.coverage === "gap" ? "danger" as const : r.coverage === "partial" ? "warning" as const : "neutral" as const)}
            striped
            stickyHeader
            style={{ maxHeight: 480 }}
          />
        </Stack>
      </CollapsibleSection>

      <Text size="small" tone="tertiary">
        Confluence page 700399537 · Publish body: Supportability-Exports/supportability-publish/project-plan-publish-20260712.md
      </Text>

    </Stack>
  );
}

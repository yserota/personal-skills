import {
  Card,
  CardBody,
  CardHeader,
  CollapsibleSection,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Row,
  Spacer,
  Stack,
  Stat,
  Text,
  TodoList,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

// ── CONTENT ─────────────────────────────────────────────────────────────────
// Updated by manage-my-day on Sunday, August 16, 2026 (refreshed 13:38)

const CONTENT = {
  date: "Sunday, August 16, 2026",
  generatedAt: "13:38",
  stats: { emails: 25, events: 6, actions: 14 },

  schedule: [
    { time: "08:00 – 08:10", block: "Wegovy shot", type: "break" as const },
    { time: "09:00 – 09:30", block: "Standup WFH", type: "meeting" as const },
    { time: "09:30 – 11:30", block: "Focus time", type: "work" as const },
    { time: "12:00 – 12:40", block: "Yvonne - Lili weekly", type: "meeting" as const },
    { time: "12:40 – 14:00", block: "Work block — GitHub approval, post-Lili action items", type: "work" as const },
    { time: "14:00 – 14:25", block: "Danielle : Yvonne Weekly sync", type: "meeting" as const },
    { time: "14:30 – 15:30", block: "R&D automation plan", type: "meeting" as const },
  ],

  actions: [
    { id: "a1", content: "URGENT · Approve RITM0164045 — Alon Arad (Sr. Staff Engineer) requests GitHub Enterprise access to tdocs org (Developer role, pending >2 days since Aug 13) (Email: IT Service Desk)", status: "pending" as const },
    { id: "a2", content: "IMPORTANT · Share latest AI pipeline documentation output link to Lili (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a3", content: "IMPORTANT · Add Lili to the Aon integration team meeting (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a4", content: "IMPORTANT · Notify Kora team of upcoming Flare→Markdown format changes to allow testing (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a5", content: "IMPORTANT · Coordinate with Vita on Kora communication plan (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a6", content: "IMPORTANT · Write updated job descriptions for TW technical content roles (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a7", content: "IMPORTANT · Share Yonyi adoption dashboard links to Lili (Gemini: Yvonne-Lili weekly)", status: "pending" as const },
    { id: "a8", content: "IMPORTANT · Find EPM release notes coverage for Steve next week — Adam to coordinate (Gemini: Standup Aug 16)", status: "pending" as const },
    { id: "a9", content: "IMPORTANT · Enter all manager performance reviews in Workday — deadline Sep 15 (Gemini: Adam/Yvonne 1:1 Aug 13)", status: "pending" as const },
    { id: "a10", content: "IMPORTANT · Follow up with Nicolas Malbranche on Salesforce Case 04181846 — Zero Touch PKI docs waiting on TW (Email: Salesforce)", status: "pending" as const },
    { id: "a11", content: "IMPORTANT · Meet with Meta to resolve priority source inconsistencies (Gemini: Adam/Yvonne 1:1 Aug 13)", status: "pending" as const },
    { id: "a12", content: "NICE · Present Claude / Day Manager AI tool at the next guild meeting (Gemini: Standup Aug 12)", status: "pending" as const },
    { id: "a13", content: "NICE · Arrange Soda demo with Steve for the team (Gemini: Standup Aug 13)", status: "pending" as const },
    { id: "a14", content: "NICE · Clarify AM MCP server status with Anat; escalate to Director of PM if unresolved (Gemini: Adam/Yvonne 1:1 Aug 13)", status: "pending" as const },
  ],

  digest: {
    email: [
      { from: "IT Service Desk", time: "11:43", text: "RITM0164045 pending approval >2 days — Alon Arad (Sr. Staff Engineer) requests GitHub Enterprise access to tdocs org (Developer role) to review TW pages. Needs your response." },
      { from: "Confluence (CyberArk)", time: "09:00", text: "2 new edits on 'Danielle Biber 1:1 Syncs' page this morning — she likely prepped the agenda ahead of your 14:00 sync." },
      { from: "Elad Gilat", time: "12:07", text: "PM AI Transformation status (Aug 9–13): 48 of 110 PMs onboarded. Peretz Regev flagged this as low for a top-priority effort and wants all 110 by September." },
      { from: "Nir Feldman", time: "10:43", text: "FY 2027 CI sign-off Session 2 (Aug 20) canceled — too many PTOs. Rescheduled to Sep 3, 4–5pm with agenda attached." },
      { from: "Salesforce", time: "09:00", text: "1 case waiting on Technical Writers: Zero Touch PKI (Machine Identity Security / Venafi), Case 04181846, owned by Nicolas Malbranche." },
    ],
    slack: [
      { channel: "No Slack data today", text: "Slack ingest did not run — no channel highlights available. Check Slack directly for any messages since Friday." },
    ],
    geminiNotes: [
      { meeting: "Yvonne - Lili weekly", date: "Aug 16", summary: "AI pipeline targeting 2x throughput and October Flare→Markdown completion; 8 action items for Yvonne including Kora team notification, TW job descriptions, and Aon integration invite." },
      { meeting: "Standup WFH", date: "Aug 16", summary: "EPM release coverage needed for Steve next week; Privilege Cloud Centralization rescheduled; Rick to process 14 open tickets pending approval." },
      { meeting: "Adam / Yvonne 1:1", date: "Aug 13", summary: "Perf reviews due Sep 15 in Workday; AM MCP server needs clarification with Anat; escalate unclear deadline to PM Director." },
      { meeting: "Yvonne / Shimrit", date: "Aug 13", summary: "Sensitive org change discussion rescheduled to Sunday — strategy to frame as industry-wide shift with financial support offered." },
      { meeting: "Standup WFH", date: "Aug 13", summary: "Kate to reinstall Cursor/MCP broker; Yvonne to share Day Manager AI tool with org; Danielle to audit stale PRs before Markdown switch." },
    ],
  },

  prep: [
    {
      event: "Standup WFH",
      time: "09:00 – 09:30",
      attendees: "rfox, sgoodman, dbiber, sfinkelstein, avinokoor, slorber, vgilin, okenetguler, kreuveny, ybisk, malawrence, rteller, lamitai, jwexler, bskelker, ylevin",
      context: [
        "Completed. Gemini notes: EPM release coverage coordination — Adam to find coverage for Steve's release notes and patches next week due to planned absences.",
        "Privilege Cloud Centralization project officially rescheduled. Rick has 14 open tickets needing approval reviews before publishing can proceed.",
        "Yonit to meet Vita about workload and deadlines. Shuli to ping Yonit about agentic onboarding and Kora integration timing.",
      ],
      questions: [],
    },
    {
      event: "Yvonne - Lili weekly",
      time: "12:00 – 12:40",
      attendees: "Lili Levy (lillevy@paloaltonetworks.com)",
      context: [
        "Completed. AI pipeline strategy: proposed pipeline aims to double throughput and cut cycle times by integrating R&D workflows while maintaining human review.",
        "Flare to Markdown migration progressing toward October completion; tagging excluded from the initial production phase to reduce complexity.",
        "8 action items assigned to Yvonne — all captured in Actions tab. Lili to review the Application Development Lifecycle definition document.",
      ],
      questions: [],
    },
    {
      event: "Danielle : Yvonne Weekly sync",
      time: "14:00 – 14:25",
      attendees: "Danielle Biber (dbiber@paloaltonetworks.com)",
      context: [
        "Danielle edited the 1:1 Confluence page twice this morning (09:00) — she came prepared with agenda items.",
        "Today she deleted two Asana projects: 'Docs rebranding' and 'Onboarding TWs template' — worth understanding if this was planned cleanup or migration to Jira.",
        "From Aug 16 standup: Danielle to meet Shuli and Orna separately; sprint planning to coordinate with Rick. From Aug 13 standup: stale PR audit before Markdown switch; persona placeholders needed for all writers.",
      ],
      questions: [
        "What is the status on the stale PR audit ahead of the Markdown migration?",
        "Were the Asana project deletions ('Docs rebranding', 'Onboarding TWs template') intentional — migrating to Jira or just closing out completed work?",
      ],
    },
    {
      event: "R&D automation plan",
      time: "14:30 – 15:30",
      attendees: "Seran (seran@paloaltonetworks.com), Orly Blum (oblum@paloaltonetworks.com), Vita Gilin (vgilin@paloaltonetworks.com)",
      context: [
        "Context from today's Lili meeting: TW's AI pipeline aims to double throughput and integrate R&D workflows — this likely directly overlaps with what R&D is planning on their side.",
        "Vita is the TW bridge for this session. She is also scheduled for a Flare→Markdown migration touchpoint (Aug 25) and the Metadata & Publication Lifecycle session (Aug 17 in-office).",
        "Seran and Orly are R&D-side with no TW Jira tickets. One hour signals a substantive agenda around tooling direction, ownership boundaries, or timeline alignment.",
      ],
      questions: [
        "What is TW's ownership scope in the automation plan — Vita's SOH workstream only, or broader TW involvement?",
        "How does the R&D automation plan connect to the Flare→Markdown migration and the AI documentation pipeline discussed with Lili today?",
      ],
    },
  ],
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeToMinutes(t: string): number {
  const [h, m] = t.trim().split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

function itemStartMinutes(timeRange: string): number {
  return timeToMinutes(timeRange.split(/\s*[–\-]\s*/)[0]);
}

const genMinutes = (() => {
  const [h, m] = CONTENT.generatedAt.split(":").map(Number);
  return h * 60 + (m || 0);
})();

// Index before which the NOW marker is inserted (after last past item)
const nowInsertIndex = (() => {
  let idx = 0;
  for (let i = 0; i < CONTENT.schedule.length; i++) {
    if (itemStartMinutes(CONTENT.schedule[i].time) < genMinutes) idx = i + 1;
  }
  return idx;
})();

// ── Types ─────────────────────────────────────────────────────────────────────

type Tab = "schedule" | "actions" | "digest" | "prep";
type ScheduleItem = typeof CONTENT.schedule[0];

// ── Sub-components ────────────────────────────────────────────────────────────

function TimelineRow({ item, isPast, isLast }: {
  item: ScheduleItem;
  isPast: boolean;
  isLast: boolean;
}) {
  const theme = useHostTheme();
  const isConflict = item.block.startsWith("CONFLICT");
  const dotColor = isConflict
    ? theme.category.orange
    : item.type === "meeting"
    ? theme.accent.primary
    : item.type === "work"
    ? theme.text.secondary
    : theme.text.tertiary;

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "116px 20px 1fr",
      opacity: isPast ? 0.38 : 1,
    }}>
      {/* Time */}
      <div style={{ paddingRight: 10, paddingTop: 3, paddingBottom: isLast ? 0 : 22, textAlign: "right" }}>
        <Text size="small" tone="tertiary" style={{ fontVariantNumeric: "tabular-nums" }}>
          {item.time}
        </Text>
      </div>
      {/* Spine */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: dotColor,
          flexShrink: 0,
          marginTop: 4,
        }} />
        {!isLast && (
          <div style={{
            flex: 1,
            width: 2,
            background: theme.stroke.tertiary,
            marginTop: 4,
            minHeight: 16,
          }} />
        )}
      </div>
      {/* Content */}
      <div style={{ paddingLeft: 10, paddingTop: 3, paddingBottom: isLast ? 0 : 22 }}>
        <Text
          size="small"
          tone={isConflict ? undefined : (item.type === "break" ? "tertiary" : "primary")}
          weight={isConflict ? "semibold" : "normal"}
          style={{ color: isConflict ? theme.category.orange : undefined }}
        >
          {item.block}
        </Text>
      </div>
    </div>
  );
}

function NowMarker() {
  const theme = useHostTheme();
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "116px 20px 1fr",
      height: 28,
    }}>
      <div />
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ width: 2, background: theme.stroke.tertiary, flex: 1 }} />
        <div style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: theme.accent.primary,
          flexShrink: 0,
        }} />
        <div style={{ width: 2, background: theme.stroke.tertiary, flex: 1 }} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 10 }}>
        <Text size="small" weight="semibold" style={{ color: theme.accent.primary, flexShrink: 0 }}>
          NOW
        </Text>
        <div style={{ flex: 1, height: 1, background: theme.stroke.secondary }} />
      </div>
    </div>
  );
}

function LegendItem({ type, label }: {
  type: "meeting" | "work" | "break" | "conflict";
  label: string;
}) {
  const theme = useHostTheme();
  const colors: Record<string, string> = {
    meeting: theme.accent.primary,
    work: theme.text.secondary,
    break: theme.text.tertiary,
    conflict: theme.category.orange,
  };
  return (
    <Row gap={6} align="center">
      <div style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: colors[type],
        flexShrink: 0,
      }} />
      <Text size="small" tone="tertiary">{label}</Text>
    </Row>
  );
}

function SchedulePanel() {
  const showNow = nowInsertIndex > 0 && nowInsertIndex < CONTENT.schedule.length;
  return (
    <Stack gap={12}>
      <H2>Schedule</H2>
      <div style={{ paddingTop: 4 }}>
        {CONTENT.schedule.map((item, i) => (
          <div key={i}>
            {showNow && i === nowInsertIndex && <NowMarker />}
            <TimelineRow
              item={item}
              isPast={itemStartMinutes(item.time) < genMinutes}
              isLast={i === CONTENT.schedule.length - 1}
            />
          </div>
        ))}
      </div>
      <Row gap={20} style={{ paddingTop: 4 }}>
        {(["meeting", "work", "break", "conflict"] as const).map(type => (
          <div key={type}>
            <LegendItem
              type={type}
              label={
                type === "meeting" ? "Meeting"
                : type === "work" ? "Work block"
                : type === "break" ? "Break / social"
                : "Conflict"
              }
            />
          </div>
        ))}
      </Row>
    </Stack>
  );
}

function ActionsPanel() {
  const theme = useHostTheme();
  const urgent = CONTENT.actions.filter(a => a.content.startsWith("URGENT"));
  const important = CONTENT.actions.filter(a => a.content.startsWith("IMPORTANT"));
  const nice = CONTENT.actions.filter(a => a.content.startsWith("NICE"));

  return (
    <Stack gap={16}>
      <H2>Action Items</H2>
      {urgent.length > 0 && (
        <div style={{
          borderLeft: `3px solid ${theme.category.orange}`,
          background: theme.fill.tertiary,
          borderRadius: "0 6px 6px 0",
          padding: "12px 12px 12px 14px",
        }}>
          <Stack gap={8}>
            <Text
              size="small"
              tone="tertiary"
              weight="semibold"
              style={{ letterSpacing: "0.05em", textTransform: "uppercase" }}
            >
              Urgent — today
            </Text>
            <TodoList todos={urgent.map(a => ({ ...a, content: a.content.replace(/^URGENT · /, "") }))} />
          </Stack>
        </div>
      )}
      {important.length > 0 && (
        <Stack gap={6}>
          <Text
            size="small"
            tone="tertiary"
            weight="semibold"
            style={{ letterSpacing: "0.05em", textTransform: "uppercase" }}
          >
            Important — this week
          </Text>
          <TodoList todos={important.map(a => ({ ...a, content: a.content.replace(/^IMPORTANT · /, "") }))} />
        </Stack>
      )}
      {nice.length > 0 && (
        <CollapsibleSection title="Nice to have" count={nice.length}>
          <TodoList todos={nice.map(a => ({ ...a, content: a.content.replace(/^NICE · /, "") }))} />
        </CollapsibleSection>
      )}
    </Stack>
  );
}

function DigestPanel() {
  const geminiNotes = CONTENT.digest.geminiNotes ?? [];
  return (
    <Stack gap={20}>
      <H2>Digest</H2>
      <Grid columns={2} gap={20}>
        <Stack gap={10}>
          <H3>Email highlights</H3>
          <Stack gap={0}>
            {CONTENT.digest.email.map((item, i) => (
              <div key={i}>
                <Stack gap={2} style={{ padding: "8px 0" }}>
                  <Row gap={8} align="center">
                    <Text size="small" weight="semibold">{item.from}</Text>
                    <Text size="small" tone="tertiary">{item.time}</Text>
                  </Row>
                  <Text size="small" tone="secondary">{item.text}</Text>
                </Stack>
                {i < CONTENT.digest.email.length - 1 && <Divider />}
              </div>
            ))}
          </Stack>
        </Stack>
        <Stack gap={10}>
          <H3>Slack highlights</H3>
          <Stack gap={0}>
            {CONTENT.digest.slack.map((item, i) => (
              <div key={i}>
                <Stack gap={2} style={{ padding: "8px 0" }}>
                  <Text size="small" weight="semibold" tone="secondary">{item.channel}</Text>
                  <Text size="small" tone="secondary">{item.text}</Text>
                </Stack>
                {i < CONTENT.digest.slack.length - 1 && <Divider />}
              </div>
            ))}
          </Stack>
        </Stack>
      </Grid>
      {geminiNotes.length > 0 && (
        <CollapsibleSection title="Meeting notes" count={geminiNotes.length}>
          <Stack gap={0}>
            {geminiNotes.map((note, i) => (
              <div key={i}>
                <Stack gap={2} style={{ padding: "8px 0" }}>
                  <Row gap={8} align="center">
                    <Text size="small" weight="semibold">{note.meeting}</Text>
                    <Text size="small" tone="tertiary">{note.date}</Text>
                  </Row>
                  <Text size="small" tone="secondary">{note.summary}</Text>
                </Stack>
                {i < geminiNotes.length - 1 && <Divider />}
              </div>
            ))}
          </Stack>
        </CollapsibleSection>
      )}
    </Stack>
  );
}

function PrepPanel() {
  return (
    <Stack gap={16}>
      <H2>Meeting Prep</H2>
      {CONTENT.prep.map((meeting, i) => (
        <div key={i}>
          <Card collapsible defaultOpen>
            <CardHeader trailing={<Text size="small" tone="tertiary">{meeting.time}</Text>}>
              {meeting.event}
            </CardHeader>
            <CardBody>
              <Stack gap={12}>
                <Stack gap={4}>
                  <Text size="small" tone="tertiary" weight="semibold">Attendees</Text>
                  <Text size="small">{meeting.attendees}</Text>
                </Stack>
                <Stack gap={4}>
                  <Text size="small" tone="tertiary" weight="semibold">Context</Text>
                  <Stack gap={4}>
                    {meeting.context.map((c, ci) => (
                      <div key={ci}>
                        <Row gap={8} align="start">
                          <Text size="small" tone="tertiary" style={{ flexShrink: 0 }}>·</Text>
                          <Text size="small" tone="secondary">{c}</Text>
                        </Row>
                      </div>
                    ))}
                  </Stack>
                </Stack>
                <Stack gap={4}>
                  <Text size="small" tone="tertiary" weight="semibold">Suggested questions</Text>
                  <Stack gap={4}>
                    {meeting.questions.map((q, qi) => (
                      <div key={qi}>
                        <Row gap={8} align="start">
                          <Text size="small" tone="tertiary" style={{ flexShrink: 0 }}>·</Text>
                          <Text size="small" tone="secondary">{q}</Text>
                        </Row>
                      </div>
                    ))}
                  </Stack>
                </Stack>
              </Stack>
            </CardBody>
          </Card>
        </div>
      ))}
    </Stack>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function DayManager() {
  const theme = useHostTheme();
  const [activeTab, setActiveTab] = useCanvasState<Tab>("activeTab", "schedule");

  const hour = parseInt(CONTENT.generatedAt.split(":")[0], 10);
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const urgentCount = CONTENT.actions.filter(a => a.content.startsWith("URGENT")).length;

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "schedule", label: "Schedule" },
    { id: "actions", label: `Actions (${CONTENT.actions.length})` },
    { id: "digest", label: "Digest" },
    { id: "prep", label: `Prep (${CONTENT.prep.length})` },
  ];

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <Stack gap={12}>
        <Stack gap={4}>
          <Text size="small" tone="tertiary">{greeting}</Text>
          <Row gap={0} align="center">
            <H1>{CONTENT.date}</H1>
            <Spacer />
            <Text size="small" tone="tertiary">Generated {CONTENT.generatedAt}</Text>
          </Row>
        </Stack>
        <div style={{
          background: theme.fill.tertiary,
          borderRadius: 8,
          padding: "12px 16px",
        }}>
          <Grid columns={3} gap={16}>
            <Stat value={CONTENT.stats.events} label="Events today" />
            <Stat value={CONTENT.stats.emails} label="Emails (last 24h)" />
            <Stat value={urgentCount} label="Urgent actions" />
          </Grid>
        </div>
        {urgentCount > 0 && (
          <Text size="small" tone="tertiary">
            {urgentCount} urgent {urgentCount === 1 ? "action requires" : "actions require"} attention today — see the Actions tab.
          </Text>
        )}
      </Stack>

      <Divider />

      {/* ── Tab strip ─────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", borderBottom: `1px solid ${theme.stroke.tertiary}` }}>
        {tabs.map(tab => (
          <div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "8px 16px",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: activeTab === tab.id ? 590 : 400,
              color: activeTab === tab.id ? theme.text.primary : theme.text.tertiary,
              borderBottom: activeTab === tab.id
                ? `2px solid ${theme.accent.primary}`
                : "2px solid transparent",
              marginBottom: -1,
              userSelect: "none",
            }}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {/* ── Panel content ─────────────────────────────────────────────────── */}
      {activeTab === "schedule" && <SchedulePanel />}
      {activeTab === "actions" && <ActionsPanel />}
      {activeTab === "digest" && <DigestPanel />}
      {activeTab === "prep" && <PrepPanel />}

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <Divider />
      <Text size="small" tone="quaternary">
        Day Manager · Refresh by running{" "}
        <Text as="span" weight="semibold" tone="quaternary">/manage-my-day</Text>{" "}
        in Cursor · Data from Gmail, Google Calendar, Slack, Gemini
      </Text>

    </Stack>
  );
}

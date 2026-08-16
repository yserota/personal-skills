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
// Updated by manage-my-day on Sunday, August 16, 2026

const CONTENT = {
  date: "Sunday, August 16, 2026",
  generatedAt: "07:21",
  stats: { emails: 3, events: 5, actions: 3 },

  schedule: [
    { time: "08:00 – 08:10", block: "Wegovy shot", type: "break" as const },
    { time: "09:00 – 09:30", block: "Standup WFH", type: "meeting" as const },
    { time: "09:30 – 11:30", block: "Focus time — clear backlog, priorities for the week", type: "work" as const },
    { time: "11:30 – 12:00", block: "Work block — prep for Yvonne-Lili weekly", type: "work" as const },
    { time: "12:00 – 12:40", block: "Yvonne - Lili weekly", type: "meeting" as const },
    { time: "12:40 – 14:00", block: "Work block — post-meeting follow-ups, prep for afternoon meetings", type: "work" as const },
    { time: "14:00 – 14:25", block: "Danielle : Yvonne Weekly sync", type: "meeting" as const },
    { time: "14:30 – 15:30", block: "R&D automation plan", type: "meeting" as const },
  ],

  actions: [
    { id: "a1", content: "IMPORTANT · Investigate new Idira Identity user account created for you (izomaker2.integration-cyberark.cloud) — verify this is expected system onboarding before clicking the login link (Email: Idira Account Management)", status: "pending" as const },
    { id: "a2", content: "NICE · Review 2 quarantined emails in PANW Proofpoint digest — log in to release or block (Email: Proofpoint)", status: "pending" as const },
    { id: "a3", content: "NICE · Review 1 quarantined email in CyberArk spam summary (Email: CyberArk Proofpoint)", status: "pending" as const },
  ],

  digest: {
    email: [
      { from: "Idira Account Management", time: "06:56", text: "New Idira Identity user account provisioned at izomaker2.integration-cyberark.cloud — invited by your system administrator. Verify expected before logging in." },
      { from: "Proofpoint (PANW)", time: "17:00 yesterday", text: "2 emails quarantined in your PANW Proofpoint digest. Review and release or block as appropriate." },
      { from: "Proofpoint (CyberArk)", time: "12:00 yesterday", text: "1 email in CyberArk spam quarantine. Log in to take action." },
    ],
    slack: [
      { channel: "No Slack data today", text: "Slack ingest did not run — no channel highlights available. Check Slack directly for any weekend messages." },
    ],
  },

  prep: [
    {
      event: "Standup WFH",
      time: "09:00 – 09:30",
      attendees: "rfox, sgoodman, dbiber, sfinkelstein, avinokoor, slorber, vgilin, okenetguler, kreuveny, ybisk, malawrence, rteller, lamitai, jwexler, bskelker, ylevin",
      context: [
        "Oded and Ofrit are both on PTO today — expect a lighter attendance than usual.",
        "No Slack or email context this morning to pre-populate agenda topics.",
      ],
      questions: [
        "Any blockers or carry-over items from last week to surface?",
        "Does anyone need context on the R&D automation plan session this afternoon?",
      ],
    },
    {
      event: "Yvonne - Lili weekly",
      time: "12:00 – 12:40",
      attendees: "Lili (one-on-one)",
      context: [
        "Weekly 1:1. No emails or Slack threads from Lili in the last 24 hours.",
        "No Gemini notes found for prior occurrences of this meeting.",
      ],
      questions: [
        "What are Lili's priorities and blockers heading into the week?",
        "Any cross-functional dependencies or team dynamics to address?",
      ],
    },
    {
      event: "Danielle : Yvonne Weekly sync",
      time: "14:00 – 14:25",
      attendees: "Danielle Biber (dbiber)",
      context: [
        "Weekly sync. No new emails from Danielle in the last 24 hours.",
        "Slack unavailable — ask Danielle at the top of the call if anything came up over the weekend.",
      ],
      questions: [
        "Any open blockers or items carrying over from last week?",
        "Status on current deliverables and week priorities?",
      ],
    },
    {
      event: "R&D automation plan",
      time: "14:30 – 15:30",
      attendees: "Seran (seran@), Oblum (oblum@), Vgilin (vgilin@)",
      context: [
        "One-hour planning session — longer than a typical sync, suggesting a substantive agenda around R&D automation direction.",
        "No email or Slack context available to determine scope. Review any prior Confluence pages or notes before joining.",
      ],
      questions: [
        "What is TW's role in the R&D automation plan, and what decisions require TW input?",
        "Are there documentation or tooling implications for the TW team from the automation strategy?",
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

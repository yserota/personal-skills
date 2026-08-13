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
// This object is updated by the manage-my-day Cursor skill.
// To refresh: open a new chat in the day-manager project and type /manage-my-day

const CONTENT = {
  date: "Thursday, August 13, 2026",
  generatedAt: "07:55",
  stats: { emails: 48, events: 9, actions: 8 },

  schedule: [
    { time: "08:00 – 09:00", block: "Team standup", type: "meeting" as const },
    { time: "09:00 – 10:30", block: "Work block: DOC-1234 first draft (due today)", type: "work" as const },
    { time: "10:30 – 11:00", block: "Product review (moved from 11:00 — Slack: #product-updates)", type: "meeting" as const },
    { time: "11:00 – 12:30", block: "Work block: PR #567 review + reply to Ofrit", type: "work" as const },
    { time: "12:30 – 13:30", block: "Lunch", type: "break" as const },
    { time: "13:30 – 14:00", block: "1:1 with manager", type: "meeting" as const },
    { time: "14:00 – 16:00", block: "Work block: Quarterly report", type: "work" as const },
    { time: "16:00 – 17:00", block: "Buffer — async reviews / Slack catch-up", type: "work" as const },
  ],

  actions: [
    { id: "a1", content: "URGENT · Review PR #567 before merge window at 13:00 (Email: Sarah)", status: "pending" as const },
    { id: "a2", content: "URGENT · Reply to Ofrit with Q3 delivery dates by EOD (Email: Ofrit)", status: "pending" as const },
    { id: "a3", content: "URGENT · Submit DOC-1234 first draft — due today (Jira)", status: "pending" as const },
    { id: "a4", content: "IMPORTANT · Update onboarding doc with new screenshots (Slack: #docs-team)", status: "pending" as const },
    { id: "a5", content: "IMPORTANT · Schedule sprint retro for this week (Slack: #engineering)", status: "pending" as const },
    { id: "a6", content: "NICE · Read new product spec v2.3 before Wednesday (Email: David)", status: "pending" as const },
    { id: "a7", content: "NICE · Confirm staging environment access request (Email: IT team)", status: "pending" as const },
  ],

  digest: {
    email: [
      { from: "Sarah", time: "10:45", text: "PR #567 ready for review — needs approval before merge window closes at 13:00." },
      { from: "Ofrit", time: "09:30", text: "Requesting Q3 delivery dates by EOD for exec review. Please confirm scope." },
      { from: "David", time: "yesterday", text: "New product spec v2.3 published to Confluence. Review requested before Wednesday." },
      { from: "IT Team", time: "08:00", text: "Staging environment access request is pending your email confirmation." },
    ],
    slack: [
      { channel: "#docs-team", text: "Onboarding doc screenshots are out of date. Action assigned to you." },
      { channel: "#engineering", text: "Sprint retro slot hasn't been picked yet. Please schedule this week." },
      { channel: "#product-updates", text: "Product review shifted to 10:30 today (was 11:00). Room B." },
    ],
    // Populated from gemini_notes.txt when available; omit or leave empty otherwise
    geminiNotes: [] as Array<{ meeting: string; date: string; summary: string }>,
  },

  prep: [
    {
      event: "Team standup",
      time: "08:00 – 09:00",
      attendees: "Full team",
      context: [
        "DOC-1234 first draft is due today — may need to flag as at-risk.",
        "Onboarding screenshots need an owner — good to raise now.",
      ],
      questions: [
        "Who is picking up the onboarding screenshot update?",
        "Any blockers on sprint goals before retro?",
      ],
    },
    {
      event: "1:1 with manager",
      time: "13:30 – 14:00",
      attendees: "Manager",
      context: [
        "Ofrit's Q3 delivery date request — align on what to commit vs push.",
        "PR #567 review is creating workload pressure on your own tasks.",
      ],
      questions: [
        "Q3 scope: what can we protect vs deprioritize?",
        "PR review load — is this on my plate long-term?",
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

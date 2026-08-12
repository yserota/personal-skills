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
  Pill,
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
  date: "Tuesday, August 11, 2026",
  generatedAt: "08:05",
  stats: { emails: 12, events: 4, actions: 7 },

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

// ── Types ────────────────────────────────────────────────────────────────────

type Tab = "schedule" | "actions" | "digest" | "prep";

// ── Sub-components ────────────────────────────────────────────────────────────

function ScheduleBlock({ type }: { type: "meeting" | "work" | "break" }) {
  const theme = useHostTheme();
  const colors: Record<string, string> = {
    meeting: theme.accent.primary,
    work: theme.text.secondary,
    break: theme.text.tertiary,
  };
  return (
    <span
      style={{
        display: "inline-block",
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: colors[type] ?? theme.text.tertiary,
        marginRight: 6,
        flexShrink: 0,
        marginTop: 5,
      }}
    />
  );
}

function SchedulePanel() {
  const theme = useHostTheme();
  return (
    <Stack gap={12}>
      <H2>Schedule</H2>
      <Stack gap={0}>
        {CONTENT.schedule.map((item, i) => (
          <div key={i}>
            <Row
              gap={10}
              align="start"
              style={{ padding: "8px 0" }}
            >
              <Text
                size="small"
                tone="tertiary"
                style={{ minWidth: 128, fontVariantNumeric: "tabular-nums", flexShrink: 0 }}
              >
                {item.time}
              </Text>
              <ScheduleBlock type={item.type} />
              <Text size="small" tone={item.type === "break" ? "tertiary" : "primary"}>
                {item.block}
              </Text>
            </Row>
            {i < CONTENT.schedule.length - 1 && (
              <Divider style={{ margin: 0 }} />
            )}
          </div>
        ))}
      </Stack>
      <Row gap={16} style={{ paddingTop: 4 }}>
        <Row gap={6} align="center">
          <ScheduleBlock type="meeting" />
          <Text size="small" tone="tertiary">Meeting</Text>
        </Row>
        <Row gap={6} align="center">
          <ScheduleBlock type="work" />
          <Text size="small" tone="tertiary">Work block</Text>
        </Row>
        <Row gap={6} align="center">
          <ScheduleBlock type="break" />
          <Text size="small" tone="tertiary">Break</Text>
        </Row>
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
        <Stack gap={6}>
          <Text size="small" tone="tertiary" weight="semibold" style={{ letterSpacing: "0.05em", textTransform: "uppercase" }}>
            Urgent — today
          </Text>
          <TodoList todos={urgent.map(a => ({ ...a, content: a.content.replace(/^URGENT · /, "") }))} />
        </Stack>
      )}
      {important.length > 0 && (
        <Stack gap={6}>
          <Text size="small" tone="tertiary" weight="semibold" style={{ letterSpacing: "0.05em", textTransform: "uppercase" }}>
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

// ── Root ─────────────────────────────────────────────────────────────────────

export default function DayManager() {
  const theme = useHostTheme();
  const [activeTab, setActiveTab] = useCanvasState<Tab>("activeTab", "schedule");

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "schedule", label: "Schedule" },
    { id: "actions", label: `Actions (${CONTENT.actions.length})` },
    { id: "digest", label: "Digest" },
    { id: "prep", label: `Prep (${CONTENT.prep.length})` },
  ];

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      {/* Header */}
      <Stack gap={8}>
        <Row gap={0} align="center">
          <H1>{CONTENT.date}</H1>
          <Spacer />
          <Text size="small" tone="tertiary">Generated {CONTENT.generatedAt}</Text>
        </Row>
        <Grid columns={3} gap={16}>
          <Stat value={CONTENT.stats.events} label="Meetings today" />
          <Stat value={CONTENT.stats.emails} label="Emails (last 24h)" />
          <Stat
            value={CONTENT.actions.filter(a => a.content.startsWith("URGENT")).length}
            label="Urgent actions"
            tone={CONTENT.actions.filter(a => a.content.startsWith("URGENT")).length > 0 ? "warning" : "success"}
          />
        </Grid>
      </Stack>

      <Divider />

      {/* Tab bar */}
      <Row gap={8}>
        {tabs.map(tab => (
          <div key={tab.id}>
            <Pill
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </Pill>
          </div>
        ))}
      </Row>

      {/* Panel content */}
      {activeTab === "schedule" && <SchedulePanel />}
      {activeTab === "actions" && <ActionsPanel />}
      {activeTab === "digest" && <DigestPanel />}
      {activeTab === "prep" && <PrepPanel />}

      {/* Footer */}
      <Divider />
      <Text size="small" tone="quaternary">
        Day Manager · Refresh by running <Text as="span" weight="semibold" tone="quaternary">/manage-my-day</Text> in Cursor ·
        Data from Gmail, Google Calendar, Slack
      </Text>
    </Stack>
  );
}

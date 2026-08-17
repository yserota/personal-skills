---
name: manage-my-day
description: Read today's ingested Gmail, Google Calendar, and Slack data, analyse it with Claude, and render a four-panel Cursor canvas with a daily digest, action items, time-blocked schedule, and meeting prep notes. Use when the user says "manage my day", "what's on today", "daily briefing", "plan my day", or "show me the dashboard".
---

# Manage My Day

## Purpose

Reads today's plain-text data files (written by the ingestion scripts), sends them to
Claude for analysis, then builds or updates `day_manager.canvas.tsx` with four panels:

| Panel | Content |
|---|---|
| **Digest** | Key emails and Slack threads — top 3 bullets each |
| **Actions** | Concrete tasks extracted from messages, with source |
| **Schedule** | Time-blocked plan layered over calendar events |
| **Prep** | Per-meeting context, attendees, suggested questions |

---

## When to use

- User says: manage my day, daily briefing, plan my day, what's on today, show me my schedule, what do I need to do.
- After `ingest_all.py` has been run for today (data files exist).
- User wants a quick morning orientation before diving in.

---

## Prerequisites

Ingestion scripts must have been run today:

```powershell
cd C:\Users\yserota\Documents\Cursor-AI\day-manager
.venv\Scripts\python.exe scripts\ingest_all.py
```

If the data files for today don't exist, tell the user to run the above first.

---

## Agent workflow

### Step 1 — Locate today's data files

Read the `.env` file in the project root to get `DATA_DIR`. If `.env` is not present
or `DATA_DIR` is not set, fall back to `G:\My Drive\day-manager` (the confirmed
Google Drive for Desktop sync path on this machine), then `data/` as a last resort.

```python
from datetime import date
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = Path(os.getenv("DATA_DIR", r"G:\My Drive\day-manager"))
today = date.today().strftime("%Y-%m-%d")
day_dir = DATA_DIR / today
```

Check for:
- `{day_dir}/gmail.txt`
- `{day_dir}/calendar.txt`
- `{day_dir}/slack.txt`
- `{day_dir}/gemini_notes.txt` *(optional — skip silently if absent, do not warn the user)*

If any required file is missing, warn the user and continue with the files that exist. Never fail completely due to a single missing source. `gemini_notes.txt` is always optional.

### Step 2 — Read the files

Read all available files in full. They are plain text, typically 5–50 KB each. Read `gemini_notes.txt` only if it exists and is non-empty.

### Step 2.5 — Enrich with Jira (and Confluence if available)

After reading the data files, query Jira via the `jira_search` MCP tool to add live ticket context that the ingestion scripts don't capture. Run these queries in parallel before sending to Claude:

**Always run:**

```
# Team workload snapshot — in-progress and under-review DOC tickets (for standup context)
jql: project = DOC AND status in ("In Progress", "Under Review") ORDER BY priority ASC, updated DESC
limit: 10, fields: summary,status,assignee,priority,updated
```

```
# Recently updated open tickets across the team (past 7 days)
jql: project = DOC AND updated >= -7d AND statusCategory != Done ORDER BY updated DESC
limit: 10, fields: summary,status,assignee,priority,updated,issuetype
```

**For each calendar event with named attendees** whose Jira username can be inferred (use the email prefix, e.g. `rfox` from `rfox@paloaltonetworks.com` — note that CyberArk team members use @cyberark.com emails while PANW-side attendees use @paloaltonetworks.com):

```
# Per-attendee open tickets (CyberArk Jira users only)
jql: assignee = "{username}" AND statusCategory != Done AND project = DOC ORDER BY updated DESC
limit: 5, fields: summary,status,priority,updated
```

Skip per-attendee queries for @paloaltonetworks.com attendees — they use a separate PANW Jira instance not connected to this broker.

**Try Confluence search** (may return 404 on the on-premise instance — skip silently if it fails, do not warn the user):

```
# Search for pages related to each meeting topic
confluence_search(query="<meeting name>", limit=3)
```

**Incorporate Jira results into Claude's context** by appending a `<jira>` block to the analysis prompt (see Step 3). Format ticket lists as:
```
- {KEY}: {summary} — {assignee} ({status}, {priority})
```

Group by assignee when surfacing in prep notes. Use ticket keys (e.g. DOC-24223) as references so the user can click through.

### Step 3 — Analyse with Claude

Send the contents to Claude with the following system prompt template. Fill in the actual file contents between the XML tags. Omit the `<gemini_notes>` block entirely if `gemini_notes.txt` was not available.

```
You are a world-class executive assistant. Analyse the following inputs from today
and produce a structured daily briefing. Be concise, actionable, and prioritised.
Use the person's actual names, times, and content — do not fabricate anything.

<calendar>
{calendar.txt contents}
</calendar>

<gmail>
{gmail.txt contents}
</gmail>

<slack>
{slack.txt contents}
</slack>

<gemini_notes>
{gemini_notes.txt contents — omit this block if the file was not available}
</gemini_notes>

<jira>
{Jira ticket data from Step 2.5 — omit this block if no Jira data was retrieved}

Team tickets in progress:
{list of in-progress/under-review DOC tickets with assignee, key, status, priority}

Per-meeting attendee tickets (where available):
{for each meeting: list the open tickets for each attendee}
</jira>

Produce exactly four sections:

## DIGEST
Summarise the most important emails and Slack messages. For each source, give
≤5 bullet points. Focus on what requires attention, not FYIs. Lead each bullet
with the sender/channel and the gist.

If gemini_notes is present, also produce a GEMINI_NOTES sub-section listing each
meeting note as a single line: "{meeting title} ({date}): {one-sentence summary of
key outcomes or decisions}". Include ≤5 entries ordered by most recent first.

## ACTIONS
List every concrete action item you found across all four sources (email, Slack,
calendar, and gemini_notes). When extracting from Gemini notes, focus on:
- Explicit action items or follow-ups called out in the notes
- Commitments made during the meeting that require follow-through
- Decisions that create downstream tasks
Format each as:
- [ ] {task description} — ({source}: {sender, channel, or meeting name})
Sort by urgency: URGENT (today), IMPORTANT (this week), NICE (whenever).

## SCHEDULE
Build a time-blocked plan for today that:
1. Lists all calendar events with their times.
2. Fills gaps with work blocks for the URGENT action items.
3. Flags time conflicts or back-to-back meetings.
Format: HH:MM – HH:MM  Task or event name [source if not calendar]

## PREP
For each calendar event with attendees, produce a short prep note:
- Event name + time
- Who is attending (besides me)
- 2–3 bullet points of context from emails/Slack/Gemini notes/Jira related to this meeting.
  For standups: list the 2–3 most urgent open tickets from the Jira team snapshot.
  For 1:1s: list the attendee's open tickets (if Jira data is available for them).
  If a Gemini note exists for a previous occurrence of this meeting (e.g. last week's
  standup), pull the most relevant outcomes or open items from it.
- 1–2 suggested agenda items or questions to raise
If no relevant context is found for an event, say so briefly.
```

### Step 4 — Parse Claude's output

Extract the four sections from Claude's response:
- Everything under `## DIGEST` → `digestContent`
- Everything under `## ACTIONS` → `actionsContent`
- Everything under `## SCHEDULE` → `scheduleContent`
- Everything under `## PREP` → `prepContent`

### Step 5 — Write the canvas

Locate the canvas file. It must be written to the Cursor-managed `canvases/` directory
for the current workspace so the IDE can render it:

```
~/.cursor/projects/<workspace-slug>/canvases/day-manager.canvas.tsx
```

The workspace slug is derived from the absolute project path with path separators
replaced by `-` and the leading separator dropped (e.g. a project at
`/Users/alice/projects/day-manager` → slug `Users-alice-projects-day-manager`).
If unsure of the slug, list `~/.cursor/projects/` (macOS/Linux) or
`%USERPROFILE%\.cursor\projects\` (Windows) and pick the entry whose name matches
this project's path.

A template copy lives at `day_manager.canvas.TEMPLATE.tsx` in the project root —
use it as a read-only base if the canvases copy doesn't exist yet. **Never write
back to the template file.**

The canvas file contains a `CONTENT` constant near the top. Update the following fields
with today's real data from Claude's analysis:

```typescript
const CONTENT = {
  date: "{weekday, month day year — e.g. Tuesday, August 11, 2026}",
  generatedAt: "{HH:MM}",
  stats: { emails: N, events: N, actions: N },

  schedule: [
    { time: "HH:MM – HH:MM", block: "description", type: "meeting" | "work" | "break" },
    // ... one entry per time block from Claude's SCHEDULE section
  ],

  actions: [
    { id: "a1", content: "URGENT · description (Source: context)", status: "pending" },
    // ... prefix each with URGENT ·, IMPORTANT ·, or NICE · to match panel grouping
  ],

  digest: {
    email: [
      { from: "Name", time: "HH:MM or 'yesterday'", text: "summary" },
    ],
    slack: [
      { channel: "#channel-name", text: "summary" },
    ],
    // Omit this field entirely (or set to []) if gemini_notes.txt was not available
    geminiNotes: [
      { meeting: "Meeting title", date: "Aug 12", summary: "one-sentence outcome" },
    ],
  },

  prep: [
    {
      event: "Meeting name",
      time: "HH:MM – HH:MM",
      attendees: "attendee list",
      context: ["bullet 1", "bullet 2"],
      questions: ["question 1", "question 2"],
    },
  ],
};
```

**SDK constraint — do not use `tone` on `Stat`.** The `Stat` component's `tone` prop (`"success" | "danger" | "warning" | "info"`) is declared in the types but broken at runtime — the SDK internally reads `theme.status.{tone}` which no longer exists in `CanvasTokens`. Omit `tone` on all `Stat` components. To surface urgency, use a `Callout` component with `tone="warning"` beneath the stats grid instead.



```
[Daily Briefing — {date}](~/.cursor/projects/<workspace-slug>/canvases/day-manager.canvas.tsx)
```

---

## Failure rules

- Data files missing → tell user to run `ingest_all.py` first; do not fabricate content.
- Claude returns garbled sections → surface the raw output and ask the user to re-run.
- Canvas file not found → create it fresh (the file should already exist from setup).
- `.env` / `DATA_DIR` not set → default to `data/` in project root.

---

## Related

- `scripts/ingest_all.py` — run this first each morning
- `scripts/ingest_gmail.py` — Gmail only
- `scripts/ingest_gcal.py` — Google Calendar only
- `scripts/ingest_slack.py` — Slack only
- `scheduler/run_ingest.ps1` — Task Scheduler wrapper (runs automatically at 08:00)
- `SETUP.md` — auth configuration guide

## Jira integration notes

- Jira (`ca-il-jira.il.cyber-ark.com:8443`) is available via the `jira_search` MCP tool through the policy broker. No extra setup needed.
- The primary project for TW team tickets is `DOC`. Use `project = DOC` as the default filter.
- CyberArk Jira usernames match email prefixes for @cyberark.com staff (e.g. `rfox`, `sgoodman`, `okenet`). PANW-side attendees (@paloaltonetworks.com) use a separate Jira instance — skip per-attendee lookups for them.
- Confluence search (`confluence_search`) currently returns HTTP 404 on the on-premise instance. Skip silently; do not surface the error to the user.
- Yvonne's own tickets: her Jira account (if any) is not on this instance. Use `reporter` or `watcher` queries with her CyberArk identity if needed.

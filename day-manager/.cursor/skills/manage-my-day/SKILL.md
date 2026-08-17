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
- 2–3 bullet points of context from emails/Slack/Gemini notes related to this meeting.
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

# Day Manager — Setup Guide

This project ingests your Gmail, Google Calendar, and Slack into local text files
each morning so a Cursor AI skill can analyse them and manage your day.

Gmail and Calendar are exported by a **Google Apps Script** (runs inside your Google
Workspace account — no GCP project needed). Slack is fetched directly via the Slack API.

---

## 1. Prerequisites

- Python 3.10+ installed
- `uv` package manager: https://docs.astral.sh/uv/
- Google Drive for Desktop installed and signed in (syncs Drive files to local disk)
- Access to https://script.google.com with your work Google account

---

## 2. Install Python dependencies

```powershell
cd C:\Users\yserota\Documents\Cursor-AI\day-manager
uv venv
uv pip install -e .
```

---

## 3. Google Apps Script setup (Gmail + Calendar)

This script runs inside your Google Workspace account. It exports your Gmail and
Calendar to a `day-manager/` folder in your Google Drive each morning at 8am.
Google Drive for Desktop then syncs those files to your local machine automatically.

> **Corporate network note:** Some organizations block https://script.google.com
> on certain VPN profiles. If you see an access error, try switching VPN configurations
> or connecting from a different network before proceeding.

### 3a. Create the script

1. Go to https://script.google.com (sign in with your **work** Google account)
2. Click **New project**
3. Name it `day-manager` (top-left title area)
4. Delete all existing code in the editor
5. Get the script code — use whichever method works on your machine:
   - **Option A:** Open `apps-script/day_manager.gs` in Cursor, select all (Ctrl+A), copy (Ctrl+C)
   - **Option B:** Open a Cursor chat in this project and ask: *"Show me the full contents of apps-script/day_manager.gs"* — then copy from the chat response
6. Paste into the Apps Script editor, replacing any existing code
7. Click **Save** (Ctrl+S)

### 3b. Run setup once

1. In the function dropdown at the top, select **setup**
2. Click **Run**
3. A permissions dialog appears — click **Review permissions** → choose your work account → **Allow**
   - It requests: Gmail (read), Calendar (read), Drive (read/write for the export folder)
4. Check the **Execution log** at the bottom — you should see:
   ```
   Setup complete. Daily trigger set for 8:00.
   Day Manager export complete for YYYY-MM-DD.
   Gmail: exported N threads → gmail.txt
   Calendar: exported N events → calendar.txt
   ```

### 3c. Verify the Drive files

1. Open Google Drive (drive.google.com or Drive for Desktop)
2. You should see a folder called `day-manager` → inside it, a folder named today's date
3. Inside that: `gmail.txt` and `calendar.txt`

The script now runs automatically every morning at 8:00am. You can also run it
manually anytime: select **exportAll** in the dropdown → **Run**.

---

## 4. Slack setup

1. Go to https://api.slack.com/apps → **Create New App → From scratch**
2. Name it (e.g. **day-manager**), choose your workspace → Create
3. In **OAuth & Permissions → Scopes → Bot Token Scopes**, add:
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `groups:read`
   - `im:history`
   - `mpim:history`
4. Click **Install to Workspace** and copy the **Bot OAuth Token** (`xoxb-...`)
5. Invite the bot to each channel you want to monitor:
   ```
   /invite @day-manager
   ```

---

## 5. Configure .env

Copy `.env.example` to `.env` and fill in the values:

```powershell
Copy-Item .env.example .env
notepad .env
```

Key values to set:

| Variable | Description |
|---|---|
| `SLACK_TOKEN` | `xoxb-...` bot token from step 4 |
| `SLACK_CHANNELS` | Comma-separated channel names (no `#`) |
| `DATA_DIR` | Local path where Google Drive syncs the `day-manager` folder |

### Finding your DATA_DIR

Google Drive for Desktop syncs your Drive to a local folder. Find it:

```powershell
# Common paths — check which one exists on your machine:
Test-Path "C:\Users\yserota\Google Drive\My Drive\day-manager"
Test-Path "C:\Users\yserota\My Drive\day-manager"
Test-Path "G:\My Drive\day-manager"
```

Use whichever path exists, e.g.:
```
DATA_DIR=C:\Users\yserota\Google Drive\My Drive\day-manager
```

---

## 6. Test the ingestion

```powershell
cd C:\Users\yserota\Documents\Cursor-AI\day-manager
.venv\Scripts\python.exe scripts\ingest_all.py
```

Expected output:
```
✓ Found data\YYYY-MM-DD\gmail.txt
✓ Found data\YYYY-MM-DD\calendar.txt
✓ Slack completed in X.Xs
All checks passed. Ready for /manage-my-day in Cursor.
```

If Gmail/Calendar files are missing, run the Apps Script manually (step 3b) and wait
for Drive for Desktop to sync (watch the tray icon).

---

## 7. Schedule daily Slack ingestion (Windows Task Scheduler)

The Apps Script already handles Gmail + Calendar at 8am via its own trigger.
Register the PowerShell wrapper to run `ingest_all.py` (Slack + verification) daily:

```powershell
$scriptPath = (Resolve-Path "scheduler\run_ingest.ps1").Path
schtasks /create `
  /tn "DayManagerIngest" `
  /tr "powershell.exe -ExecutionPolicy Bypass -File `"$scriptPath`"" `
  /sc DAILY `
  /st 08:05 `
  /ru "%USERNAME%" `
  /f
```

Set it to 08:05 so the Apps Script has time to run and Drive has time to sync first.

To verify:
```powershell
schtasks /query /tn "DayManagerIngest"
```

To run immediately:
```powershell
schtasks /run /tn "DayManagerIngest"
```

To remove:
```powershell
schtasks /delete /tn "DayManagerIngest" /f
```

Log output is written to `logs\ingest.log` and `logs\scheduler.log`.

---

## 8. Use the Cursor skill

### 8a. Open this project in Cursor

Open Cursor and open this folder as your workspace:
**File → Open Folder → select the `day-manager` folder**

The skill is defined in `.cursor/skills/manage-my-day/SKILL.md` and is
automatically available once the folder is open.

### 8b. Set up the canvas

The skill renders output as a live Cursor canvas. A template with the full UI
structure is included in the repo at `day_manager.canvas.TEMPLATE.tsx`.

**You do not need to copy or edit this file.** On the first run of `/manage-my-day`,
the skill reads the template, fills it with today's data, and writes the live canvas to
Cursor's managed canvases folder:

```
%USERPROFILE%\.cursor\projects\<workspace-slug>\canvases\day-manager.canvas.tsx
```

That path is outside the repo, so the generated daily canvas is never committed to git.
The template in the repo stays untouched and serves as the base for future runs.

> If the canvas does not open after running the skill, check that you opened the
> `day-manager` folder directly as your Cursor workspace (not a parent folder).

### 8c. Run the skill

After the morning ingestion has run (Apps Script + `ingest_all.py`), open a new
Cursor chat and type:

```
/manage-my-day
```

Cursor will invoke the skill, which:
1. Reads today's `gmail.txt`, `calendar.txt`, and `slack.txt` from `DATA_DIR`
2. Sends the contents to Claude for analysis
3. Builds a four-panel canvas with your daily briefing:
   - **Schedule** — time-blocked plan layered over your calendar
   - **Actions** — tasks extracted from emails and Slack, sorted by urgency
   - **Digest** — key highlights from email and Slack
   - **Prep** — context and suggested questions for each meeting

### 8d. Daily workflow

Each morning:
1. Apps Script runs at 8:00 AM → writes `gmail.txt` and `calendar.txt` to Drive
2. Task Scheduler runs at 8:05 AM → fetches Slack, verifies all three files
3. Open Cursor → new chat → `/manage-my-day`

### 8e. Troubleshooting the skill

**"Gmail and Calendar data are missing"** — the skill is looking in the wrong folder.
Make sure `DATA_DIR` in `.env` points to your Google Drive sync path:
```
DATA_DIR=G:\My Drive\day-manager
```
Then open Cursor with the `day-manager` folder as the workspace (not another project).

**Skill not found** — make sure you opened the `day-manager` folder directly in Cursor,
not a parent folder or a different project.

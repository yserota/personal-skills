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

### 3a. Create the script

1. Go to https://script.google.com (sign in with your **work** Google account)
2. Click **New project**
3. Name it `day-manager` (top-left title area)
4. Delete all existing code in the editor
5. Open `apps-script/day_manager.gs` from this project and **paste the entire contents**
6. Click **Save** (Ctrl+S)

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
schtasks /create `
  /tn "DayManagerIngest" `
  /tr "powershell.exe -ExecutionPolicy Bypass -File C:\Users\yserota\Documents\Cursor-AI\day-manager\scheduler\run_ingest.ps1" `
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

After the morning run, open Cursor in this folder and type:

```
/manage-my-day
```

The skill reads today's `gmail.txt`, `calendar.txt`, and `slack.txt`, sends them to
Claude for analysis, and renders a four-panel canvas:
- **Schedule** — time-blocked plan for the day
- **Actions** — tasks extracted from your messages
- **Digest** — key email and Slack highlights
- **Prep** — context and suggested questions for each meeting

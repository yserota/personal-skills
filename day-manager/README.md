# Day Manager

AI-assisted daily planning powered by Gmail, Google Calendar, and Slack.

Python scripts ingest your data each morning → Cursor AI skill analyses it and
renders a daily dashboard with digest, action items, schedule, and meeting prep.

## Quick start

See **[SETUP.md](SETUP.md)** for full auth and scheduler configuration.

```powershell
# 1. Install
uv venv && uv pip install -e .

# 2. Configure (fill in credentials and channels)
Copy-Item .env.example .env

# 3. Run ingestion (first run opens browser for Google OAuth)
.venv\Scripts\python.exe scripts\ingest_all.py

# 4. Open Cursor and type:
#    /manage-my-day
```

## Project structure

```
scripts/
  ingest_gmail.py    # Gmail → data/YYYY-MM-DD/gmail.txt
  ingest_gcal.py     # Google Calendar → data/YYYY-MM-DD/calendar.txt
  ingest_slack.py    # Slack → data/YYYY-MM-DD/slack.txt
  ingest_all.py      # Run all three
scheduler/
  run_ingest.ps1     # Windows Task Scheduler wrapper
.cursor/skills/manage-my-day/
  SKILL.md           # Cursor skill definition
day_manager.canvas.tsx  # Daily dashboard canvas
```

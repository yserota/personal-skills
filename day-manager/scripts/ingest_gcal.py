"""
Fetches today's and tomorrow's events from Google Calendar and writes them
to a plain-text file in the configured DATA_DIR.

Output: {DATA_DIR}/YYYY-MM-DD/calendar.txt
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json"))
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(
                    f"ERROR: credentials.json not found at {CREDENTIALS_PATH}\n"
                    "See SETUP.md section 3 to create Google OAuth credentials.",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def parse_event_time(dt_obj: dict) -> str:
    """Return a readable time string from a Calendar event dateTime or date."""
    if "dateTime" in dt_obj:
        dt = datetime.fromisoformat(dt_obj["dateTime"])
        return dt.strftime("%H:%M")
    if "date" in dt_obj:
        return "All day"
    return "?"


def fetch_events(service, days_ahead: int = 2) -> list[dict]:
    today = date.today()
    time_min = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    time_max = datetime.combine(
        today + timedelta(days=days_ahead), datetime.min.time(), tzinfo=timezone.utc
    ).isoformat()

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        )
        .execute()
    )
    return result.get("items", [])


def format_event(event: dict) -> str:
    summary = event.get("summary", "(untitled)")
    start = parse_event_time(event.get("start", {}))
    end = parse_event_time(event.get("end", {}))
    location = event.get("location", "")
    description = (event.get("description") or "").strip()[:400]
    attendees = event.get("attendees", [])

    attendee_list = ", ".join(
        a.get("displayName") or a.get("email", "") for a in attendees if not a.get("self")
    )

    lines = [f"  {start}–{end}  {summary}"]
    if location:
        lines.append(f"           Location:  {location}")
    if attendee_list:
        lines.append(f"           Attendees: {attendee_list}")
    if description:
        lines.append(f"           Notes:     {description.splitlines()[0]}")
    return "\n".join(lines)


def format_output(events: list[dict], run_at: datetime) -> str:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    today_events = []
    tomorrow_events = []
    for e in events:
        start = e.get("start", {})
        raw = start.get("dateTime") or start.get("date", "")
        ev_date = datetime.fromisoformat(raw).date() if raw else None
        if ev_date == today:
            today_events.append(e)
        elif ev_date == tomorrow:
            tomorrow_events.append(e)

    lines = [
        f"CALENDAR — {run_at.strftime('%A, %B %d %Y').replace(' 0', ' ')}",
        f"Fetched: {len(events)} events (today + tomorrow)",
        "=" * 72,
        "",
        f"TODAY — {today.strftime('%A %B %d').replace(' 0', ' ')}",
        "-" * 40,
    ]
    if today_events:
        for e in today_events:
            lines.append(format_event(e))
    else:
        lines.append("  (no events)")
    lines += [
        "",
        f"TOMORROW — {tomorrow.strftime('%A %B %d').replace(' 0', ' ')}",
        "-" * 40,
    ]
    if tomorrow_events:
        for e in tomorrow_events:
            lines.append(format_event(e))
    else:
        lines.append("  (no events)")
    lines.append("")
    return "\n".join(lines)


def main():
    run_at = datetime.now()
    date_str = run_at.strftime("%Y-%m-%d")
    out_dir = DATA_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "calendar.txt"

    print("Authenticating with Google Calendar…")
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    print("Fetching events (today + tomorrow)…")
    events = fetch_events(service)

    output = format_output(events, run_at)
    out_file.write_text(output, encoding="utf-8")
    print(f"Wrote {len(events)} events → {out_file}")


if __name__ == "__main__":
    main()

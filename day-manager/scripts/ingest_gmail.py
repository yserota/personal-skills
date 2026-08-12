"""
Fetches recent emails from Gmail and writes them to a plain-text file
in the configured DATA_DIR for the current date.

Output: {DATA_DIR}/YYYY-MM-DD/gmail.txt
"""

import base64
import email
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json"))
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "50"))
HOURS_BACK = int(os.getenv("GMAIL_HOURS_BACK", "24"))


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


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\s{3,}", "\n", text)
    return text.strip()


def decode_body(payload: dict) -> str:
    """Recursively decode the message body, preferring plain text."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    if mime_type == "text/html" and body_data:
        raw = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        return strip_html(raw)

    parts = payload.get("parts", [])
    plain = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
    if plain:
        data = plain.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in parts:
        text = decode_body(part)
        if text:
            return text

    return ""


def get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_emails(service) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    after_epoch = int(cutoff.timestamp())
    query = f"after:{after_epoch} -category:promotions -category:social"

    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=MAX_RESULTS)
        .execute()
    )
    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        full = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        headers = full["payload"].get("headers", [])
        subject = get_header(headers, "Subject") or "(no subject)"
        sender = get_header(headers, "From")
        date_str = get_header(headers, "Date")
        body = decode_body(full["payload"])

        body_preview = body[:800].strip()
        if len(body) > 800:
            body_preview += "\n[...truncated]"

        emails.append(
            {
                "from": sender,
                "subject": subject,
                "date": date_str,
                "body": body_preview,
            }
        )

    return emails


def format_output(emails: list[dict], run_at: datetime) -> str:
    lines = [
        f"GMAIL DIGEST — {run_at.strftime('%A, %B %d %Y').replace(' 0', ' ')}",
        f"Fetched: {len(emails)} messages (last {HOURS_BACK}h, max {MAX_RESULTS})",
        "=" * 72,
        "",
    ]
    if not emails:
        lines.append("No emails found in the configured window.")
        return "\n".join(lines)

    for i, e in enumerate(emails, 1):
        lines += [
            f"[{i}] {e['subject']}",
            f"    From:    {e['from']}",
            f"    Date:    {e['date']}",
            f"    ---",
            e["body"],
            "",
            "-" * 72,
            "",
        ]
    return "\n".join(lines)


def main():
    run_at = datetime.now()
    date_str = run_at.strftime("%Y-%m-%d")
    out_dir = DATA_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "gmail.txt"

    print(f"Authenticating with Gmail…")
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    print(f"Fetching emails (last {HOURS_BACK}h, max {MAX_RESULTS})…")
    emails = fetch_emails(service)

    output = format_output(emails, run_at)
    out_file.write_text(output, encoding="utf-8")
    print(f"Wrote {len(emails)} emails → {out_file}")


if __name__ == "__main__":
    main()

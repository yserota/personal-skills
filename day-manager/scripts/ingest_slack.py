"""
Fetches recent messages from configured Slack channels and writes them
to a plain-text file in the configured DATA_DIR.

Output: {DATA_DIR}/YYYY-MM-DD/slack.txt
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import truststore
truststore.inject_into_ssl()

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN", "")
SLACK_CHANNELS_RAW = os.getenv("SLACK_CHANNELS", "general")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

CHANNELS = [c.strip().lstrip("#") for c in SLACK_CHANNELS_RAW.split(",") if c.strip()]
MAX_MESSAGES_PER_CHANNEL = 100


def resolve_channel_id(client: WebClient, name: str) -> str | None:
    """
    Return channel ID for a given channel name or ID.
    If the value already looks like a Slack channel ID (starts with C), use it directly.
    Otherwise search by exact name using conversations.list with a name filter.
    """
    # Already an ID
    if name.upper().startswith("C") and len(name) >= 9:
        return name

    # Use name filter to avoid paginating the entire workspace
    try:
        resp = client.conversations_list(
            types="public_channel,private_channel",
            limit=1000,
            exclude_archived=True,
        )
        for ch in resp.get("channels", []):
            if ch.get("name") == name:
                return ch["id"]
    except SlackApiError as e:
        if e.response.get("error") == "ratelimited":
            wait = int(e.response.headers.get("Retry-After", 30))
            print(f"  Rate limited — waiting {wait}s then retrying once…")
            time.sleep(wait)
            resp = client.conversations_list(
                types="public_channel,private_channel",
                limit=1000,
                exclude_archived=True,
            )
            for ch in resp.get("channels", []):
                if ch.get("name") == name:
                    return ch["id"]
        else:
            raise
    return None


def fetch_channel_messages(client: WebClient, channel_id: str) -> list[dict]:
    """Fetch messages posted since yesterday midnight."""
    yesterday_midnight = datetime.combine(
        (datetime.now() - timedelta(days=1)).date(),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    oldest = str(yesterday_midnight.timestamp())

    messages = []
    cursor = None
    while True:
        try:
            resp = client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                limit=MAX_MESSAGES_PER_CHANNEL,
                **({"cursor": cursor} if cursor else {}),
            )
        except SlackApiError as e:
            if e.response.get("error") == "ratelimited":
                retry_after = int(e.response.headers.get("Retry-After", 5))
                print(f"  Rate limited — waiting {retry_after}s…")
                time.sleep(retry_after)
                continue
            raise

        messages.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor or len(messages) >= MAX_MESSAGES_PER_CHANNEL:
            break

    return messages


def resolve_channel_name(client: WebClient, channel_id: str) -> str:
    """Return the human-readable name for a channel ID, falling back to the ID."""
    try:
        resp = client.conversations_info(channel=channel_id)
        return resp["channel"].get("name") or channel_id
    except SlackApiError:
        return channel_id


def resolve_username(client: WebClient, user_id: str, cache: dict) -> str:
    if user_id in cache:
        return cache[user_id]
    try:
        resp = client.users_info(user=user_id)
        name = (
            resp["user"].get("real_name")
            or resp["user"].get("name")
            or user_id
        )
    except SlackApiError:
        name = user_id
    cache[user_id] = name
    return name


def format_channel(
    channel_name: str,
    messages: list[dict],
    client: WebClient,
    user_cache: dict,
) -> list[str]:
    lines = [
        f"#{channel_name}",
        "-" * 40,
    ]
    if not messages:
        lines.append("  (no messages)")
        lines.append("")
        return lines

    for msg in reversed(messages):
        ts = float(msg.get("ts", 0))
        dt = datetime.fromtimestamp(ts).strftime("%H:%M")
        user_id = msg.get("user", "")
        username = resolve_username(client, user_id, user_cache) if user_id else "bot"
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        text_preview = text[:300]
        if len(text) > 300:
            text_preview += " […]"
        lines.append(f"  {dt}  {username}: {text_preview}")

    lines.append("")
    return lines


def main():
    if not SLACK_TOKEN:
        print(
            "ERROR: SLACK_TOKEN is not set.\nSee SETUP.md section 4 to create a Slack app.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_at = datetime.now()
    date_str = run_at.strftime("%Y-%m-%d")
    out_dir = DATA_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "slack.txt"

    client = WebClient(token=SLACK_TOKEN)
    user_cache: dict = {}

    body_lines: list[str] = []
    total = 0
    display_names: list[str] = []

    for channel_input in CHANNELS:
        print(f"Resolving #{channel_input}…")
        channel_id = resolve_channel_id(client, channel_input)
        if not channel_id:
            print(f"  WARNING: channel #{channel_input} not found (not a member?)")
            body_lines += [f"#{channel_input}", "  (channel not found or bot not invited)", ""]
            display_names.append(channel_input)
            continue

        # If the config value was a raw channel ID, look up the human-readable name
        is_raw_id = channel_input.upper().startswith("C") and len(channel_input) >= 9
        display_name = resolve_channel_name(client, channel_id) if is_raw_id else channel_input
        display_names.append(display_name)

        print(f"  Fetching messages for #{display_name}…")
        messages = fetch_channel_messages(client, channel_id)
        total += len(messages)
        body_lines += format_channel(display_name, messages, client, user_cache)

    header = [
        f"SLACK DIGEST — {run_at.strftime('%A, %B %d %Y').replace(' 0', ' ')}",
        f"Channels: {', '.join('#' + n for n in display_names)}",
        "=" * 72,
        "",
    ]

    output = "\n".join(header + body_lines)
    out_file.write_text(output, encoding="utf-8")
    print(f"Wrote {total} messages across {len(display_names)} channel(s) -> {out_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
export_subscribers.py — Fetch Mailchimp subscribers and email the list to jf4151@nyu.edu

Usage:
    python3 export_subscribers.py

Required environment variables:
    MAILCHIMP_API_KEY   — your Mailchimp API key (e.g. abc123...–us14)
    MAILCHIMP_LIST_ID   — your Audience/List ID (found in Audience > Settings > Audience name and defaults)
    SMTP_USER           — Gmail address used to send the email
    SMTP_PASS           — Gmail App Password (not your regular password)
                          Generate at: https://myaccount.google.com/apppasswords
"""

import os
import csv
import sys
import io
import json
import base64
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta, timezone

# ── Config ──────────────────────────────────────────────────────────────────

MAILCHIMP_API_KEY = os.environ.get("MAILCHIMP_API_KEY", "")
MAILCHIMP_LIST_ID = os.environ.get("MAILCHIMP_LIST_ID", "")
SMTP_USER         = os.environ.get("SMTP_USER", "")
SMTP_PASS         = os.environ.get("SMTP_PASS", "")

GOATCOUNTER_API_KEY  = os.environ.get("GOATCOUNTER_API_KEY", "")
GOATCOUNTER_SITE_URL = os.environ.get("GOATCOUNTER_SITE_URL", "https://rizzolabs.goatcounter.com")

RECIPIENTS        = [
    "jf4151@nyu.edu",
    "johnrossrizzo@gmail.com",
    "beheshti.mahya@gmail.com",
    "Dylan.Mcdonald@nyulangone.org",
]
SMTP_HOST         = "smtp.gmail.com"
SMTP_PORT         = 587

# ── Mailchimp ────────────────────────────────────────────────────────────────

def get_server_prefix(api_key: str) -> str:
    """The server prefix is the part after the dash in the API key (e.g. 'us14')."""
    try:
        return api_key.split("-")[-1]
    except Exception:
        print("ERROR: Could not parse server prefix from API key.")
        sys.exit(1)


def fetch_all_members(api_key: str, list_id: str) -> list[dict]:
    """Page through Mailchimp's /lists/{id}/members endpoint and return all members."""
    prefix  = get_server_prefix(api_key)
    base    = f"https://{prefix}.api.mailchimp.com/3.0"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    members   = []
    offset    = 0
    page_size = 1000

    while True:
        url = (
            f"{base}/lists/{list_id}/members"
            f"?count={page_size}&offset={offset}"
            f"&fields=members.email_address,members.status,"
            f"members.timestamp_opt,members.merge_fields"
        )
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"ERROR fetching members (HTTP {e.code}): {body}")
            sys.exit(1)

        batch = data.get("members", [])
        members.extend(batch)

        if len(batch) < page_size:
            break
        offset += page_size

    return members


# ── Build CSV ────────────────────────────────────────────────────────────────

def build_csv(members: list[dict]) -> str:
    """Return a CSV string with one row per subscriber."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Email", "First Name", "Last Name", "Status", "Subscribed At"])

    for m in members:
        merge = m.get("merge_fields", {})
        writer.writerow([
            m.get("email_address", ""),
            merge.get("FNAME", ""),
            merge.get("LNAME", ""),
            m.get("status", ""),
            m.get("timestamp_opt", ""),
        ])

    return buf.getvalue()


# ── GoatCounter ─────────────────────────────────────────────────────────────

def fetch_goatcounter_stats(api_key: str, site_url: str) -> dict | None:
    """Fetch traffic summary (7-day) and top pages (30-day) from GoatCounter.

    Uses HTTP Basic auth with username 'any' and the API token as the password.
    Returns None on any failure so the caller can degrade gracefully.
    """
    today     = datetime.now(tz=timezone.utc).date()
    week_ago  = today - timedelta(days=6)
    month_ago = today - timedelta(days=29)

    today_s     = today.isoformat()
    week_ago_s  = week_ago.isoformat()
    month_ago_s = month_ago.isoformat()

    token_b64 = base64.b64encode(f"any:{api_key}".encode()).decode()
    auth_header = {"Authorization": f"Basic {token_b64}"}

    def _get(url: str) -> dict:
        req = urllib.request.Request(url, headers=auth_header)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    base = site_url.rstrip("/") + "/api/v0"

    try:
        total_url = (
            f"{base}/stats/total"
            f"?start={week_ago_s}&end={today_s}"
        )
        total_data = _get(total_url)

        hits_url = (
            f"{base}/stats/hits"
            f"?start={month_ago_s}&end={today_s}&daily=true&limit=10"
        )
        hits_data = _get(hits_url)

        daily_7d = [
            (entry["day"], entry["daily"])
            for entry in total_data["stats"]
        ]
        top_pages_30d = [
            (h["path"], h["title"], h["count"])
            for h in hits_data["hits"]
        ]

        return {
            "total_7d":      total_data["total"],
            "daily_7d":      daily_7d,
            "top_pages_30d": top_pages_30d,
            "range_7d":      (week_ago_s, today_s),
            "range_30d":     (month_ago_s, today_s),
        }

    except urllib.error.HTTPError as exc:
        print(f"GoatCounter HTTP error {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        print(f"GoatCounter URL error: {exc.reason}")
    except TimeoutError:
        print("GoatCounter request timed out.")
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"GoatCounter response parse error: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"GoatCounter unexpected error: {type(exc).__name__}: {exc}")

    return None


def format_stats_section(stats: dict | None) -> str:
    """Format GoatCounter stats as a plain-text block for the email body."""
    if stats is None:
        return "Website analytics: not available for this run."

    start_7d,  end_7d  = stats["range_7d"]
    start_30d, end_30d = stats["range_30d"]

    lines: list[str] = [
        "Website analytics",
        "=================",
        "",
        f"Traffic summary ({start_7d} to {end_7d})",
        f"  Total pageviews: {stats['total_7d']}",
        "",
        f"  {'Date':<12}  {'Pageviews':>9}",
    ]
    for day, count in stats["daily_7d"]:
        lines.append(f"  {day:<12}  {count:>9}")

    lines += [
        "",
        f"Top pages ({start_30d} to {end_30d})",
    ]
    for rank, (path, title, count) in enumerate(stats["top_pages_30d"], start=1):
        lines.append(f"  {rank:>2}.  {count:>5}   {path:<20} {title}")

    return "\n".join(lines)


# ── Send email ───────────────────────────────────────────────────────────────

def send_email(csv_data: str, total: int, stats_text: str = ""):
    today     = datetime.now().strftime("%Y-%m-%d")
    filename  = f"rizzo_labs_subscribers_{today}.csv"
    subject   = f"Rizzo Labs Subscriber List — {total} contacts ({today})"

    stats_block = f"\n{stats_text}\n\n" if stats_text else ""
    body = (
        f"Hi everyone,\n\n"
        f"This is the Rizzo Labs auto subscription management system.\n\n"
        f"Attached is the current Rizzo Labs mailing list exported from Mailchimp.\n\n"
        f"  Total subscribers: {total}\n"
        f"  Export date: {today}\n"
        f"{stats_block}"
        f"The CSV includes email address, name, subscription status, and sign-up date.\n\n"
        f"---\n"
        f"This is an automatically generated email. If you have any questions, you can respond directly to this email.\n"
    )

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = ", ".join(RECIPIENTS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(csv_data.encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(attachment)

    print(f"Connecting to {SMTP_HOST}:{SMTP_PORT} …")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, RECIPIENTS, msg.as_string())

    print(f"Email sent to {', '.join(RECIPIENTS)} with {total} subscriber(s) attached as '{filename}'.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    missing = [v for v in ("MAILCHIMP_API_KEY", "MAILCHIMP_LIST_ID", "SMTP_USER", "SMTP_PASS")
               if not os.environ.get(v)]
    if missing:
        print("ERROR: Missing required environment variable(s):", ", ".join(missing))
        print(__doc__)
        sys.exit(1)

    print(f"Fetching members from Mailchimp list {MAILCHIMP_LIST_ID} …")
    members = fetch_all_members(MAILCHIMP_API_KEY, MAILCHIMP_LIST_ID)
    print(f"  Retrieved {len(members)} member(s).")

    gc_key  = os.environ.get("GOATCOUNTER_API_KEY", "")
    gc_url  = os.environ.get("GOATCOUNTER_SITE_URL", "https://rizzolabs.goatcounter.com")
    if gc_key:
        print("Fetching GoatCounter analytics …")
        try:
            stats = fetch_goatcounter_stats(gc_key, gc_url)
        except Exception as exc:  # noqa: BLE001
            print(f"GoatCounter fetch failed unexpectedly: {type(exc).__name__}: {exc}")
            stats = None
    else:
        print("GOATCOUNTER_API_KEY not set — skipping website analytics.")
        stats = None

    stats_text = format_stats_section(stats)

    csv_data = build_csv(members)
    send_email(csv_data, len(members), stats_text=stats_text)


if __name__ == "__main__":
    main()

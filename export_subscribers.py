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
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────

MAILCHIMP_API_KEY = os.environ.get("MAILCHIMP_API_KEY", "")
MAILCHIMP_LIST_ID = os.environ.get("MAILCHIMP_LIST_ID", "")
SMTP_USER         = os.environ.get("SMTP_USER", "")
SMTP_PASS         = os.environ.get("SMTP_PASS", "")

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


# ── Send email ───────────────────────────────────────────────────────────────

def send_email(csv_data: str, total: int):
    today     = datetime.now().strftime("%Y-%m-%d")
    filename  = f"rizzo_labs_subscribers_{today}.csv"
    subject   = f"Rizzo Labs Subscriber List — {total} contacts ({today})"

    body = (
        f"Hi everyone,\n\n"
        f"This is the Rizzo Labs auto subscription management system.\n\n"
        f"Attached is the current Rizzo Labs mailing list exported from Mailchimp.\n\n"
        f"  Total subscribers: {total}\n"
        f"  Export date: {today}\n\n"
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

    csv_data = build_csv(members)
    send_email(csv_data, len(members))


if __name__ == "__main__":
    main()

"""Distribute the digest: email subscribers, cross-post to Dev.to, write archive page."""
import os
import re
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "archive"
SITE = ROOT / "site"
SUBS_FILE = ROOT / "subscribers.txt"


def send_email(subject, markdown_body, html_body):
    key = os.environ.get("RESEND_KEY")
    if not key:
        print("[email] RESEND_KEY missing, skipping")
        return
    if not SUBS_FILE.exists():
        print("[email] no subscribers.txt, skipping")
        return
    subs = [
        s.strip()
        for s in SUBS_FILE.read_text(encoding="utf-8").splitlines()
        if s.strip() and not s.startswith("#")
    ]
    if not subs:
        print("[email] empty subscriber list")
        return
    from_addr = os.environ.get("RESEND_FROM", "Token Ledger <onboarding@resend.dev>")
    for s in subs:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [s],
                "subject": subject,
                "html": html_body,
                "text": markdown_body,
            },
            timeout=30,
        )
        if r.status_code >= 300:
            print(f"[email] {s} failed: {r.status_code} {r.text[:200]}")
        else:
            print(f"[email] sent to {s}")
        time.sleep(0.5)


def cross_post_devto(title, markdown_body, canonical_url):
    key = os.environ.get("DEVTO_KEY")
    if not key:
        print("[devto] no key, skipping")
        return
    r = requests.post(
        "https://dev.to/api/articles",
        headers={"api-key": key, "Content-Type": "application/json"},
        json={
            "article": {
                "title": title,
                "body_markdown": markdown_body
                + f"\n\n---\n*Originally published at [The Token Ledger]({canonical_url}). Subscribe for the daily digest.*",
                "published": True,
                "canonical_url": canonical_url,
                "tags": ["ai", "llm", "api", "news"],
            }
        },
        timeout=60,
    )
    if r.status_code >= 300:
        print(f"[devto] failed: {r.status_code} {r.text[:300]}")
    else:
        print(f"[devto] posted: {r.json().get('url')}")


def slugify(s):
    return re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")[:80]


def write_archive(date_str, title, markdown_body):
    ARCHIVE.mkdir(exist_ok=True)
    fname = f"{date_str}.md"
    (ARCHIVE / fname).write_text(
        f"---\ntitle: {title}\ndate: {date_str}\n---\n\n{markdown_body}\n",
        encoding="utf-8",
    )
    return f"archive/{fname}"


def rebuild_archive_index():
    """Regenerate site/archive.html from all markdown files in archive/."""
    files = sorted(ARCHIVE.glob("*.md"), reverse=True)
    items = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        title_match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem
        items.append(
            f'<li><a href="entry.html?d={f.stem}"><span class="d">{f.stem}</span> {title}</a></li>'
        )
    return "\n".join(items)

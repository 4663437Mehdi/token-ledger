"""Daily orchestrator. Run via GitHub Actions cron."""
import os
import re
import time
from pathlib import Path

from sources import fetch_openrouter_models, load_previous, save_snapshot, diff_snapshots
from digest import synthesize
from outputs import send_email, cross_post_devto, write_archive, rebuild_archive_index, ROOT, SITE

DATE = time.strftime("%Y-%m-%d")
SITE_URL = os.environ.get("SITE_URL", "https://4663437mehdi.github.io/token-ledger")


def md_to_simple_html(md):
    html = md
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)
    paragraphs = []
    for block in html.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("<h") or block.startswith("<ul") or block.startswith("<ol"):
            paragraphs.append(block)
        elif block.startswith("- ") or block.startswith("* "):
            items = "".join(f"<li>{re.sub(r'^[-*] ', '', line)}</li>" for line in block.split("\n"))
            paragraphs.append(f"<ul>{items}</ul>")
        else:
            paragraphs.append(f"<p>{block.replace(chr(10), '<br>')}</p>")
    return "\n".join(paragraphs)


def main():
    print(f"=== Token Ledger run for {DATE} ===")
    new = fetch_openrouter_models()
    old = load_previous()
    print(f"old={len(old)} new={len(new)}")
    diff = diff_snapshots(old, new)
    print(f"added={len(diff['added'])} removed={len(diff['removed'])} price_changes={len(diff['price_changes'])}")

    digest_md = synthesize(diff, new, DATE)
    title_match = re.search(r"^# (.+)$", digest_md, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"Token Ledger — {DATE}"
    print(f"title: {title}")

    write_archive(DATE, title, digest_md)

    canonical = f"{SITE_URL}/entry.html?d={DATE}"
    html_body = md_to_simple_html(digest_md) + f'<hr><p><a href="{SITE_URL}">Subscribe at The Token Ledger</a></p>'

    send_email(subject=title, markdown_body=digest_md, html_body=html_body)
    cross_post_devto(title=title, markdown_body=digest_md, canonical_url=canonical)

    archive_index = rebuild_archive_index()
    idx_path = SITE / "archive_index.html"
    idx_path.write_text(
        f"<!doctype html><meta charset=utf-8><title>Archive — The Token Ledger</title>"
        f"<link rel=stylesheet href=style.css><body><main><h1>Archive</h1>"
        f'<p><a href="./">← Home</a></p><ul class="archive">{archive_index}</ul></main></body>',
        encoding="utf-8",
    )

    save_snapshot(new)
    print("=== done ===")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read-only CLI and library for finding recent Microsoft emails in Zoho Mail."""

from __future__ import annotations

import argparse
import email
import getpass
import imaplib
import json
import re
import ssl
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


DEFAULT_TERMS = ("microsoft", "azure", "office365", "accountprotection")
DEFAULT_HOST = "imap.zoho.com"
DEFAULT_FOLDER = "INBOX"
DEFAULT_DAYS = 62
DEFAULT_OUTPUT = "microsoft_emails.json"


def decoded(value: str | None) -> str:
    """Decode an RFC 2047 email header value to a plain string."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (LookupError, UnicodeError):
        return value


def message_text(message: Message) -> str:
    """Extract readable plain text from an email message body."""
    parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() not in ("text/plain", "text/html"):
                continue
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                parts.append(payload.decode(charset, errors="replace"))
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="replace"))

    text = "\n".join(parts)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_terms(terms: Sequence[str] | None) -> tuple[str, ...]:
    """Return lowercase search terms, falling back to defaults."""
    if not terms:
        return DEFAULT_TERMS
    cleaned = tuple(t.strip().lower() for t in terms if t and t.strip())
    return cleaned or DEFAULT_TERMS


def matches_microsoft(
    from_addr: str,
    subject: str,
    body: str,
    terms: Sequence[str],
) -> bool:
    """Return True if any term appears in From, Subject, or body."""
    haystack = f"{from_addr} {subject} {body}".lower()
    return any(term in haystack for term in terms)


def parse_message_date(raw: str | None) -> str | None:
    """Parse an email Date header into ISO-8601, or return None."""
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError, OverflowError, IndexError):
        return decoded(raw) or None


def message_to_record(message: Message, uid: str) -> dict[str, Any]:
    """Convert an email.message.Message into a serializable dict."""
    from_addr = decoded(message.get("From"))
    subject = decoded(message.get("Subject"))
    body = message_text(message)
    return {
        "uid": uid,
        "from": from_addr,
        "subject": subject,
        "date": parse_message_date(message.get("Date")),
        "message_id": decoded(message.get("Message-ID")),
        "snippet": body[:400],
        "body_preview": body[:2000],
    }


def since_imap_date(days: int) -> str:
    """IMAP SINCE date string for *days* ago (e.g. 01-Jan-2026)."""
    since = datetime.now(timezone.utc) - timedelta(days=max(days, 0))
    return since.strftime("%d-%b-%Y")


def connect_imap(
    host: str,
    email_addr: str,
    password: str,
    *,
    timeout: int = 60,
) -> imaplib.IMAP4_SSL:
    """Open a read-only IMAP SSL session to Zoho Mail."""
    context = ssl.create_default_context()
    client = imaplib.IMAP4_SSL(host, 993, ssl_context=context, timeout=timeout)
    client.login(email_addr, password)
    return client


def search_uids(
    client: imaplib.IMAP4_SSL,
    folder: str,
    days: int,
) -> list[str]:
    """Select folder (readonly) and return UIDs newer than *days* ago."""
    status, _ = client.select(folder, readonly=True)
    if status != "OK":
        raise RuntimeError(f"Cannot select folder {folder!r}: {status}")

    criteria = f'(SINCE {since_imap_date(days)})'
    status, data = client.uid("search", None, criteria)
    if status != "OK" or not data or not data[0]:
        return []
    return data[0].decode("ascii", errors="ignore").split()


def fetch_message(client: imaplib.IMAP4_SSL, uid: str) -> Message | None:
    """Fetch a single message by UID as an email.Message."""
    status, data = client.uid("fetch", uid, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        return None
    raw = data[0][1] if isinstance(data[0], tuple) else None
    if not raw:
        return None
    return email.message_from_bytes(raw)


def find_microsoft_emails(
    email_addr: str,
    password: str,
    *,
    host: str = DEFAULT_HOST,
    days: int = DEFAULT_DAYS,
    terms: Sequence[str] | None = None,
    folder: str = DEFAULT_FOLDER,
    progress: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Connect to Zoho Mail and return matching Microsoft-related messages.

    Read-only: folder is selected with readonly=True; nothing is deleted
    or marked. Password is never written to the result objects.
    """
    terms_norm = normalize_terms(terms)
    results: list[dict[str, Any]] = []
    client = connect_imap(host, email_addr, password)
    try:
        uids = search_uids(client, folder, days)
        total = len(uids)
        for index, uid in enumerate(uids, start=1):
            if progress is not None:
                try:
                    progress(index, total)
                except Exception:  # noqa: BLE001 — UI callbacks must not abort search
                    pass
            message = fetch_message(client, uid)
            if message is None:
                continue
            record = message_to_record(message, uid)
            if matches_microsoft(
                record["from"],
                record["subject"],
                record.get("body_preview") or record.get("snippet") or "",
                terms_norm,
            ):
                record["matched_terms"] = [
                    t
                    for t in terms_norm
                    if t
                    in f"{record['from']} {record['subject']} {record.get('body_preview', '')}".lower()
                ]
                results.append(record)
    finally:
        try:
            client.close()
        except imaplib.IMAP4.error:
            pass
        client.logout()

    results.sort(key=lambda r: r.get("date") or "", reverse=True)
    return results


def write_results(path: str | Path, results: Iterable[dict[str, Any]]) -> Path:
    """Write search results as pretty-printed JSON."""
    out = Path(path)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": 0,
        "emails": list(results),
    }
    payload["count"] = len(payload["emails"])
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="חיפוש לקריאה בלבד של הודעות ממיקרוסופט בתיבת Zoho"
    )
    parser.add_argument("--email", required=True, help="כתובת הדואר של Zoho")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="שרת IMAP; לחשבון אירופי נסה imap.zoho.eu",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="מספר ימים אחורה",
    )
    parser.add_argument(
        "--term",
        action="append",
        dest="terms",
        help="מילת זיהוי לשולח; אפשר לחזור על האפשרות",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="קובץ התוצאות",
    )
    parser.add_argument(
        "--folder",
        default=DEFAULT_FOLDER,
        help="תיקייה לחיפוש; ברירת המחדל היא INBOX",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="סיסמת אפליקציה (לא מומלץ — עדיף הזנה אינטראקטיבית)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    password = args.password or getpass.getpass("Zoho app password: ")
    if not password:
        print("Password is required.", file=sys.stderr)
        return 2

    try:
        results = find_microsoft_emails(
            args.email,
            password,
            host=args.host,
            days=args.days,
            terms=args.terms,
            folder=args.folder,
        )
    except imaplib.IMAP4.error as exc:
        print(f"IMAP error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    out = write_results(args.output, results)
    print(f"Found {len(results)} matching email(s). Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

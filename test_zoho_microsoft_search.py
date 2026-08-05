#!/usr/bin/env python3
"""Unit tests for zoho_microsoft_search (no live IMAP)."""

from __future__ import annotations

import email
from email.message import EmailMessage
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))

from zoho_microsoft_search import (  # noqa: E402
    DEFAULT_TERMS,
    decoded,
    matches_microsoft,
    message_text,
    message_to_record,
    normalize_terms,
    since_imap_date,
    write_results,
)


class TestDecoded(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(decoded(None), "")
        self.assertEqual(decoded(""), "")

    def test_plain(self) -> None:
        self.assertEqual(decoded("Hello"), "Hello")

    def test_encoded(self) -> None:
        raw = "=?utf-8?B?TWljcm9zb2Z0?= Account"
        self.assertIn("Microsoft", decoded(raw))


class TestMessageText(unittest.TestCase):
    def test_plain(self) -> None:
        msg = EmailMessage()
        msg.set_content("Azure security alert for your account.")
        text = message_text(msg)
        self.assertIn("Azure security alert", text)

    def test_html_stripped(self) -> None:
        msg = EmailMessage()
        msg.set_content(
            "<p>Hello <b>Microsoft</b></p>",
            subtype="html",
        )
        text = message_text(msg)
        self.assertNotIn("<", text)
        self.assertIn("Microsoft", text)


class TestMatching(unittest.TestCase):
    def test_normalize_default(self) -> None:
        self.assertEqual(normalize_terms(None), DEFAULT_TERMS)
        self.assertEqual(normalize_terms([]), DEFAULT_TERMS)

    def test_normalize_custom(self) -> None:
        self.assertEqual(normalize_terms([" Azure ", "Teams"]), ("azure", "teams"))

    def test_match_from(self) -> None:
        self.assertTrue(
            matches_microsoft(
                "account-security-noreply@accountprotection.microsoft.com",
                "Sign-in",
                "",
                DEFAULT_TERMS,
            )
        )

    def test_no_match(self) -> None:
        self.assertFalse(
            matches_microsoft("friend@example.com", "Lunch", "see you soon", DEFAULT_TERMS)
        )


class TestRecordAndIO(unittest.TestCase):
    def test_message_to_record(self) -> None:
        msg = EmailMessage()
        msg["From"] = "noreply@microsoft.com"
        msg["Subject"] = "Your Azure subscription"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
        msg["Message-ID"] = "<abc@microsoft.com>"
        msg.set_content("Please review your Azure billing.")
        record = message_to_record(msg, "42")
        self.assertEqual(record["uid"], "42")
        self.assertIn("microsoft.com", record["from"])
        self.assertIn("Azure", record["subject"])
        self.assertTrue(record["date"])
        self.assertIn("Azure", record["snippet"])

    def test_since_imap_date_format(self) -> None:
        value = since_imap_date(7)
        # e.g. 29-Jul-2026
        self.assertRegex(value, r"^\d{2}-[A-Za-z]{3}-\d{4}$")

    def test_write_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            out = write_results(path, [{"uid": "1", "subject": "Hi"}])
            text = out.read_text(encoding="utf-8")
            self.assertIn('"count": 1', text)
            self.assertIn("Hi", text)


if __name__ == "__main__":
    unittest.main()

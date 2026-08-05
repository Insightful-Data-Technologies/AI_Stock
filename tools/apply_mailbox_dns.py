#!/usr/bin/env python3
"""Apply Microsoft 365 SPF (and verify MX/DMARC) on GoDaddy.

Does NOT switch MX to Google — live mail is Microsoft 365 / Outlook.
Requires GODADDY_API_KEY, GODADDY_API_SECRET, GODADDY_DOMAIN in the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API = "https://api.godaddy.com/v1"
SPF_VALUE = "v=spf1 include:spf.protection.outlook.com -all"
DMARC_PREFIX = "v=DMARC1; p=none; rua=mailto:dmarc-reports@"


def headers(key: str, secret: str) -> dict[str, str]:
    return {
        "Authorization": f"sso-key {key}:{secret}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def expected_mx(domain: str) -> str:
    return f"{domain.replace('.', '-')}.mail.protection.outlook.com"


def get_records(domain: str, auth: dict[str, str], rtype: str | None = None) -> list:
    path = f"/domains/{domain}/records"
    if rtype:
        path += f"/{rtype}"
    r = requests.get(API + path, headers=auth, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply-spf",
        action="store_true",
        help="Replace root SPF TXT with Microsoft 365 SPF (merges other @ TXT).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply-spf, print planned PUT body only.",
    )
    args = parser.parse_args()

    key = os.getenv("GODADDY_API_KEY", "")
    secret = os.getenv("GODADDY_API_SECRET", "")
    domain = os.getenv("GODADDY_DOMAIN", "").strip()
    if not key or not secret:
        print("Missing GODADDY_API_KEY / GODADDY_API_SECRET", file=sys.stderr)
        return 1
    if not domain:
        print("Missing GODADDY_DOMAIN", file=sys.stderr)
        return 1

    auth = headers(key, secret)
    mx = get_records(domain, auth, "MX")
    txt = get_records(domain, auth, "TXT")
    want_mx = expected_mx(domain)
    want_dmarc = f"{DMARC_PREFIX}{domain}"

    print(f"Domain configured: yes ({len(domain)} chars)")
    print("MX:")
    for rec in mx:
        print(f"  priority={rec.get('priority')} name={rec.get('name')}")
    print(f"TXT count: {len(txt)}")

    mx_ok = any(
        (rec.get("data") or "").rstrip(".").lower() == want_mx.lower() for rec in mx
    )
    print(f"MX Outlook check: {'OK' if mx_ok else 'MISSING'}")

    spf_recs = [
        r
        for r in txt
        if r.get("name") in ("@", domain) and str(r.get("data", "")).startswith("v=spf1")
    ]
    dmarc_recs = [
        r for r in txt if r.get("name") in ("_dmarc", f"_dmarc.{domain}")
    ]

    if spf_recs:
        current_spf = spf_recs[0]["data"]
        print(f"Current SPF starts with v=spf1: yes")
        print(f"SPF needs update: {current_spf != SPF_VALUE}")
    else:
        print("No SPF found")
        current_spf = None

    if dmarc_recs:
        print(f"DMARC OK: {dmarc_recs[0]['data'] == want_dmarc}")
    else:
        print("DMARC missing")

    if not args.apply_spf:
        print("\nDry inspection only. Re-run with --apply-spf to update SPF.")
        return 0 if mx_ok else 2

    root_txt = [r for r in txt if r.get("name") in ("@", domain)]
    others = [
        {"data": r["data"], "ttl": r.get("ttl") or 3600}
        for r in root_txt
        if not str(r.get("data", "")).startswith("v=spf1")
    ]
    others.append({"data": SPF_VALUE, "ttl": 3600})

    if args.dry_run:
        print("\nDry-run PUT TXT/@ body (data redacted lengths):")
        for item in others:
            print(f"  ttl={item['ttl']} data_len={len(item['data'])} spf={item['data'].startswith('v=spf1')}")
        return 0

    url = f"{API}/domains/{domain}/records/TXT/@"
    r = requests.put(url, headers=auth, data=json.dumps(others), timeout=30)
    if not r.ok:
        print(f"Failed: {r.status_code} {r.text}", file=sys.stderr)
        return 1
    print("\nSPF updated successfully.")
    refreshed = get_records(domain, auth, "TXT")
    print(f"TXT count after update: {len(refreshed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

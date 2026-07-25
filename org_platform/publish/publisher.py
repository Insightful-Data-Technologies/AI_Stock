"""Publish a Google Studio site URL onto a GoDaddy domain."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from org_platform.publish.godaddy import GoDaddyClient, GoDaddyError


STUDIO_HINTS = (
    "web.app",
    "firebaseapp.com",
    "appspot.com",
    "run.app",
    "cloudfunctions.net",
    "googleusercontent.com",
    "aistudio",
    "studio",
)


def normalize_domain(domain: str) -> str:
    d = domain.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0].split("?")[0]
    if d.startswith("www."):
        d = d[4:]
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", d):
        raise ValueError(f"Invalid domain: {domain}")
    return d


def parse_studio_url(site_url: str) -> Dict[str, Any]:
    raw = site_url.strip()
    if not raw:
        raise ValueError("Google Studio site URL is required")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("Could not parse hostname from site URL")
    if host.startswith("www."):
        host = host[4:]
    kind = "generic"
    if host.endswith(".web.app") or host.endswith(".firebaseapp.com"):
        kind = "firebase_hosting"
    elif host.endswith(".appspot.com"):
        kind = "app_engine"
    elif host.endswith(".run.app"):
        kind = "cloud_run"
    elif "aistudio" in host or "ai.google" in host:
        kind = "google_ai_studio"
    elif any(h in host for h in STUDIO_HINTS):
        kind = "google_studio_like"
    return {
        "input": site_url.strip(),
        "canonical_url": f"https://{host}",
        "host": host,
        "kind": kind,
        "path": parsed.path or "/",
    }


# Standard Google Front End targets used by Cloud Run / AI Studio custom domains.
CLOUD_RUN_WWW_CNAME = "ghs.googlehosted.com"
CLOUD_RUN_APEX_A = ["216.239.32.21", "216.239.34.21", "216.239.36.21", "216.239.38.21"]
CLOUD_RUN_APEX_AAAA = [
    "2001:4860:4802:32::15",
    "2001:4860:4802:34::15",
    "2001:4860:4802:36::15",
    "2001:4860:4802:38::15",
]


def build_publish_plan(
    site_url: str,
    domain: str,
    *,
    include_www: bool = True,
    apex_forward: bool = True,
    verification_txt: Optional[str] = None,
    ttl: int = 600,
) -> Dict[str, Any]:
    studio = parse_studio_url(site_url)
    root = normalize_domain(domain)
    records: List[Dict[str, Any]] = []
    steps: List[str] = []
    cloud_runish = studio["kind"] in {"cloud_run", "google_ai_studio", "app_engine"}

    if include_www:
        www_target = CLOUD_RUN_WWW_CNAME if cloud_runish else studio["host"]
        records.append(
            {
                "type": "CNAME",
                "name": "www",
                "data": www_target,
                "ttl": ttl,
                "purpose": (
                    "Point www at Google hosting (Cloud Run / AI Studio domain mapping)"
                    if cloud_runish
                    else "Point www.<domain> at Studio host"
                ),
            }
        )
        steps.append(f"Set CNAME www → {www_target}")

    if verification_txt:
        records.append(
            {
                "type": "TXT",
                "name": "@",
                "data": verification_txt,
                "ttl": ttl,
                "purpose": "Domain ownership verification for Google / Firebase",
            }
        )
        steps.append("Set TXT @ verification token from Google Studio / Firebase")

    apex_forward_to = None
    if cloud_runish:
        for ip in CLOUD_RUN_APEX_A:
            records.append(
                {
                    "type": "A",
                    "name": "@",
                    "data": ip,
                    "ttl": ttl,
                    "purpose": "Cloud Run / AI Studio apex IPv4",
                }
            )
        for ip in CLOUD_RUN_APEX_AAAA:
            records.append(
                {
                    "type": "AAAA",
                    "name": "@",
                    "data": ip,
                    "ttl": ttl,
                    "purpose": "Cloud Run / AI Studio apex IPv6",
                }
            )
        steps.append("Set apex A/AAAA records to Google Front End IPs")
        steps.append(
            f"In Google Cloud Run → Domain mappings: map {root} and www.{root} "
            f"to service host {studio['host']}"
        )
    elif apex_forward:
        apex_forward_to = f"https://www.{root}"
        steps.append(f"Forward apex {root} → https://www.{root} (or add provider A records)")

    steps.extend(
        [
            "Wait for DNS propagation + Google SSL certificate (often 15–60 minutes)",
            f"Verify https://www.{root} serves the Studio app (not the old placeholder)",
        ]
    )

    return {
        "domain": root,
        "studio": studio,
        "records": records,
        "apex_forward_to": apex_forward_to,
        "public_urls": {
            "www": f"https://www.{root}",
            "apex": f"https://{root}",
            "studio": studio["canonical_url"],
        },
        "steps": steps,
        "notes": [
            "For Cloud Run / Google AI Studio, DNS alone is not enough: create Domain mappings in GCP.",
            "www should CNAME to ghs.googlehosted.com (not the *.run.app hostname) when using domain mappings.",
            "API credentials are used only to write DNS; they are never stored in job history.",
        ],
    }


def apply_plan(
    plan: Dict[str, Any],
    client: GoDaddyClient,
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    if dry_run:
        for rec in plan["records"]:
            results.append({"action": "dry_run", "record": rec, "ok": True})
        if plan.get("apex_forward_to"):
            results.append(
                {
                    "action": "dry_run",
                    "forward": plan["apex_forward_to"],
                    "ok": True,
                }
            )
        return {"mode": "dry_run", "applied": False, "results": results, "error": None}

    if not client.configured:
        raise GoDaddyError("GoDaddy credentials required for live publish")

    # Confirm domain exists on the account when list/get works
    try:
        client.get_domain(plan["domain"])
        results.append({"action": "verify_domain", "ok": True, "domain": plan["domain"]})
    except GoDaddyError as exc:
        # Some keys can edit DNS but not GET /domains/{domain}
        results.append(
            {
                "action": "verify_domain",
                "ok": False,
                "domain": plan["domain"],
                "warning": str(exc),
                "status_code": exc.status_code,
            }
        )

    # Group by (type, name) — GoDaddy PUT replaces the whole set for that key.
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for rec in plan["records"]:
        grouped.setdefault((rec["type"], rec["name"]), []).append(rec)

    for (rtype, name), recs in grouped.items():
        payload = [{"data": r["data"], "ttl": int(r.get("ttl") or 600)} for r in recs]
        try:
            client._request(
                "PUT",
                f"/domains/{plan['domain']}/records/{rtype}/{name}",
                json=payload,
            )
            results.append({"action": "put_records", "type": rtype, "name": name, "records": recs, "ok": True})
        except GoDaddyError as exc:
            results.append(
                {
                    "action": "put_records",
                    "type": rtype,
                    "name": name,
                    "records": recs,
                    "ok": False,
                    "error": str(exc),
                    "status_code": exc.status_code,
                    "body": exc.body,
                }
            )

    if plan.get("apex_forward_to"):
        ok, msg = client.set_forwarding(plan["domain"], plan["apex_forward_to"])
        results.append({"action": "apex_forward", "ok": ok, "detail": msg, "to": plan["apex_forward_to"]})

    applied = any(r.get("action") == "put_records" and r.get("ok") for r in results)
    failed = [r for r in results if r.get("ok") is False and r.get("action") == "put_records"]
    return {
        "mode": "live",
        "applied": applied and not failed,
        "results": results,
        "error": None if not failed else "One or more DNS record updates failed",
    }


def run_publish(
    site_url: str,
    domain: str,
    *,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    dry_run: bool = True,
    include_www: bool = True,
    apex_forward: bool = True,
    verification_txt: Optional[str] = None,
) -> Dict[str, Any]:
    plan = build_publish_plan(
        site_url,
        domain,
        include_www=include_www,
        apex_forward=apex_forward,
        verification_txt=verification_txt,
    )
    client = GoDaddyClient(api_key=api_key, api_secret=api_secret)
    application = apply_plan(plan, client, dry_run=dry_run)
    return {
        "plan": plan,
        "application": application,
        "credentials_configured": client.configured,
        "status": "planned" if dry_run else ("published" if application.get("applied") else "failed"),
    }


def credentials_status(api_key: Optional[str] = None, api_secret: Optional[str] = None) -> Dict[str, Any]:
    client = GoDaddyClient(api_key=api_key, api_secret=api_secret)
    if not client.configured:
        return {"configured": False, "ok": False, "message": "No GoDaddy credentials in env or request"}
    try:
        info = client.ping()
        return {"configured": True, "ok": True, **info}
    except GoDaddyError as exc:
        return {
            "configured": True,
            "ok": False,
            "message": str(exc),
            "status_code": exc.status_code,
        }

"""GoDaddy Domains API client (credentials from env or request — never logged)."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import requests


class GoDaddyError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class GoDaddyClient:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = (api_key or os.environ.get("GODADDY_API_KEY") or os.environ.get("GODADDY_KEY") or "").strip()
        self.api_secret = (
            api_secret or os.environ.get("GODADDY_API_SECRET") or os.environ.get("GODADDY_SECRET") or ""
        ).strip()
        self.base_url = os.environ.get("GODADDY_API_BASE", "https://api.godaddy.com/v1").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _headers(self) -> Dict[str, str]:
        if not self.configured:
            raise GoDaddyError("GoDaddy API credentials missing (set GODADDY_API_KEY + GODADDY_API_SECRET)")
        return {
            "Authorization": f"sso-key {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        try:
            res = requests.request(method, url, headers=self._headers(), timeout=30, **kwargs)
        except requests.RequestException as exc:
            raise GoDaddyError(f"GoDaddy network error: {exc}") from exc
        if res.status_code >= 400:
            raise GoDaddyError(
                f"GoDaddy API {res.status_code} for {path}",
                status_code=res.status_code,
                body=res.text[:500],
            )
        if res.status_code == 204 or not res.content:
            return None
        return res.json()

    def list_domains(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/domains")
        return data if isinstance(data, list) else []

    def get_domain(self, domain: str) -> Dict[str, Any]:
        return self._request("GET", f"/domains/{domain}")

    def get_records(self, domain: str, record_type: Optional[str] = None, name: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/domains/{domain}/records"
        if record_type and name:
            path = f"/domains/{domain}/records/{record_type}/{name}"
        elif record_type:
            path = f"/domains/{domain}/records/{record_type}"
        data = self._request("GET", path)
        return data if isinstance(data, list) else []

    def put_record(self, domain: str, record_type: str, name: str, data: str, ttl: int = 600) -> None:
        self._request(
            "PUT",
            f"/domains/{domain}/records/{record_type}/{name}",
            json=[{"data": data, "ttl": ttl}],
        )

    def put_records(self, domain: str, records: List[Dict[str, Any]]) -> None:
        """Replace-or-set typed records via PATCH add/update semantics."""
        self._request("PATCH", f"/domains/{domain}/records", json=records)

    def set_forwarding(self, domain: str, target_url: str, type_: str = "REDIRECT_PERMANENT") -> Tuple[bool, str]:
        """Best-effort apex forwarding. Not all accounts expose this endpoint."""
        payload = {
            "type": type_,
            "url": target_url,
            "mask": False,
            "title": "",
        }
        try:
            self._request("PUT", f"/domains/{domain}/forwarding", json=payload)
            return True, "apex forwarding configured"
        except GoDaddyError as exc:
            return False, f"forwarding API unavailable ({exc.status_code or 'error'}) — use www or set A records manually"

    def ping(self) -> Dict[str, Any]:
        domains = self.list_domains()
        return {
            "ok": True,
            "domain_count": len(domains),
            "domains": [d.get("domain") for d in domains[:50] if d.get("domain")],
        }

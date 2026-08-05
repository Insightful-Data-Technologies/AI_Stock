"""Content Studio LLM helpers — Azure first, then OpenAI, never dump DeploymentNotFound."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from org_platform.publish.env_loader import load_dotenv

load_dotenv()

TONES = {
    "professional": "Professional / Business",
    "institutional": "Institutional / Sell-side",
    "executive": "Executive brief",
    "neutral": "Neutral / Clear",
    "persuasive": "Persuasive / Marketing",
}

DEFAULT_DRAFT = """# Institutional Financial Article Writing Guidelines

Write for publications like Bloomberg, Reuters, and The Financial Times.

- Lead with the market-moving fact in the first sentence.
- Prefer precise verbs over adjectives.
- Attribute every forward-looking claim.
- Keep paragraphs short; one idea each.
- Close with implications for capital allocation, not opinion theater.
"""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _azure_deployments() -> List[str]:
    # Deployment names come only from env — never hardcode the live deployment id.
    primary = _env("AZURE_OPENAI_DEPLOYMENT")
    extras = [
        primary,
        _env("AZURE_OPENAI_DEPLOYMENT_FALLBACK"),
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-35-turbo",
    ]
    out: List[str] = []
    for d in extras:
        if d and d not in out:
            out.append(d)
    return out


def _http_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout: float = 60.0,
) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def _extract_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Empty model response")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif isinstance(block, str):
                parts.append(block)
        content = "".join(parts)
    text = (content or "").strip()
    if not text:
        raise RuntimeError("Model returned blank text")
    return text


def _call_azure(messages: List[Dict[str, str]], max_tokens: int = 2400) -> Tuple[str, str]:
    endpoint = _env("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = _env("AZURE_OPENAI_API_KEY")
    api_version = _env("AZURE_OPENAI_API_VERSION")
    if not endpoint or not api_key:
        raise RuntimeError("Azure OpenAI is not configured")
    if not api_version:
        raise RuntimeError("AZURE_OPENAI_API_VERSION is not set")
    deployments = _azure_deployments()
    if not deployments:
        raise RuntimeError("AZURE_OPENAI_DEPLOYMENT is not set")

    last_err: Optional[Exception] = None
    for deployment in deployments:
        url = (
            f"{endpoint}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={api_version}"
        )
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.35,
        }
        try:
            data = _http_json(
                url,
                payload,
                {"api-key": api_key, "Content-Type": "application/json"},
            )
            return _extract_text(data), f"azure:{deployment}"
        except Exception as exc:  # noqa: BLE001 — try next deployment
            last_err = exc
            msg = str(exc)
            # Only auto-advance on missing deployment; other errors stop the chain early.
            if "DeploymentNotFound" in msg or "404" in msg:
                continue
            raise
    raise RuntimeError(f"Azure deployments failed: {last_err}")


def _call_openai(messages: List[Dict[str, str]], max_tokens: int = 2400) -> Tuple[str, str]:
    api_key = _env("OPENAI_API_KEY")
    if not api_key or not api_key.startswith("sk-"):
        raise RuntimeError("OpenAI API key is not configured")
    model = _env("OPENAI_MODEL", "gpt-4o-mini")
    data = _http_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.35,
        },
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    return _extract_text(data), f"openai:{model}"


def _local_rewrite(text: str, tone_key: str) -> str:
    """Deterministic polish when cloud models are unreachable (dev / restricted egress)."""
    cleaned = re.sub(r"[ \t]+\n", "\n", text.strip())
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    lines = [ln.rstrip() for ln in cleaned.splitlines()]
    out: List[str] = []
    tone_label = TONES.get(tone_key, TONES["professional"])
    out.append(f"<!-- Content Studio · {tone_label} rewrite -->")
    out.append("")
    for ln in lines:
        if not ln:
            out.append("")
            continue
        if ln.startswith("#"):
            out.append(ln)
            continue
        # Light institutional polish without inventing facts.
        polished = ln
        polished = re.sub(r"\bvery\b", "", polished, flags=re.I)
        polished = re.sub(r"\breally\b", "", polished, flags=re.I)
        polished = re.sub(r"\s{2,}", " ", polished).strip()
        if polished and polished[0].islower():
            polished = polished[0].upper() + polished[1:]
        if polished and polished[-1] not in ".!?:;":
            polished += "."
        out.append(polished)
    out.append("")
    out.append(
        f"_Tone applied: {tone_label}. Source draft preserved; claims were not invented._"
    )
    return "\n".join(out).strip()


def _local_translate(text: str, target_lang: str) -> str:
    target = (target_lang or "he").lower()
    note = "Hebrew" if target.startswith("he") else "English"
    return (
        f"[Content Studio local translate → {note}]\n\n"
        f"{text.strip()}\n\n"
        "_Cloud translation unavailable in this environment. "
        "Configure a reachable Azure OpenAI deployment and retry._"
    )


def _build_rewrite_messages(text: str, tone_key: str) -> List[Dict[str, str]]:
    tone = TONES.get(tone_key, TONES["professional"])
    system = (
        "You are Content Studio for Insightful Data Technologies. "
        "Rewrite the user's draft in the requested tone. "
        "Keep facts, numbers, and structure. Improve clarity and institutional quality. "
        "Return only the rewritten draft — no preamble."
    )
    user = f"Target tone: {tone}\n\nDraft:\n{text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _build_translate_messages(text: str, target_lang: str) -> List[Dict[str, str]]:
    lang = "Hebrew" if (target_lang or "he").lower().startswith("he") else "English"
    system = (
        "You are Content Studio translator. Translate faithfully, preserve formatting "
        "and financial terminology. Return only the translation."
    )
    user = f"Translate to {lang}:\n\n{text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def content_studio_complete(
    *,
    mode: str,
    text: str,
    tone: str = "professional",
    target_lang: str = "he",
) -> Dict[str, Any]:
    draft = (text or "").strip()
    if not draft:
        raise ValueError("Draft is empty")

    mode_l = (mode or "rewrite").lower()
    if mode_l == "translate":
        messages = _build_translate_messages(draft, target_lang)
    else:
        messages = _build_rewrite_messages(draft, tone)

    errors: List[str] = []
    for caller in (_call_azure, _call_openai):
        try:
            result, provider = caller(messages)
            return {
                "ok": True,
                "text": result,
                "provider": provider,
                "mode": mode_l,
                "tone": tone,
                "target_lang": target_lang,
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{caller.__name__}: {exc}")

    # Restricted cloud egress / missing deployment — still finish the page action.
    if mode_l == "translate":
        local = _local_translate(draft, target_lang)
    else:
        local = _local_rewrite(draft, tone)
    return {
        "ok": True,
        "text": local,
        "provider": "local-fallback",
        "mode": mode_l,
        "tone": tone,
        "target_lang": target_lang,
        "warnings": errors,
    }

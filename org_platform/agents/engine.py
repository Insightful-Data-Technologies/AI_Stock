"""Agent response engine aligned to SRS hierarchy and workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from org_platform.agents.roster import (
    CEO_ID,
    DEV_PM_ID,
    DEV_TL_ID,
    EA_ID,
    FORECAST_ID,
    MAIN_PM_ID,
    ROSTER,
    VP_RD_ID,
    OrgAgent,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def route_speakers(message: str, chair_id: str = VP_RD_ID) -> List[str]:
    text = (message or "").lower()
    speakers = [chair_id, MAIN_PM_ID]
    if any(k in text for k in ["ceo", "executive", "priority", "escalat"]):
        speakers += [EA_ID, CEO_ID]
    if any(k in text for k in ["develop", "code", "frontend", "backend", "api", "claude", "cursor"]):
        speakers += [DEV_PM_ID, DEV_TL_ID, "dev-ultra-1"]
    if any(k in text for k in ["qa", "test", "regress", "defect", "pass", "fail"]):
        speakers += ["qa-tl", "qa-1"]
    if any(k in text for k in ["deploy", "cloud run", "ssl", "dns", "devops", "rollback"]):
        speakers += ["pm-devops", "devops-tl", "devops-1"]
    if any(k in text for k in ["email", "slack", "identity", "permission", "meeting room", "it "]):
        speakers += ["it-tl", "it-1", "it-2"]
    if "morning" in text or "standup" in text or "agenda" in text:
        speakers += [MAIN_PM_ID, DEV_PM_ID, "qa-tl", "pm-devops", "it-tl", VP_RD_ID]
    # unique
    out: List[str] = []
    for s in speakers:
        if s in ROSTER and s not in out:
            out.append(s)
    return out[:8]


def craft_reply(agent: OrgAgent, message: str, meeting_title: str) -> Dict[str, Any]:
    text = (message or "").strip()
    approval = None
    escalate_to = None

    if agent.id == CEO_ID:
        body = (
            "Chanan Zevin — CEO. I will take strategic decisions and high-impact approvals only. "
            f"On “{text or meeting_title}”: route execution through VP R&D and keep routine technical noise away from my queue."
        )
        if any(k in text.lower() for k in ["approve release", "production release", "executive approval"]):
            approval = {"status": "approved", "by": agent.id, "scope": "executive", "note": "CEO production approval"}
    elif agent.id == EA_ID:
        body = (
            "Sofia Marchetti, Executive Assistant: agenda updated and noise filtered. "
            "I will prepare a polished executive summary for CEO Chanan Zevin and sync with VP R&D."
        )
    elif agent.id == VP_RD_ID:
        approval = {
            "status": "approved",
            "by": agent.id,
            "scope": "engineering-qa-devops-it",
            "note": "VP R&D operational approval",
        }
        body = (
            f"VP R&D chairing “{meeting_title}”. Directive acknowledged: “{text or 'continue program'}”. "
            "Main PM owns coordination; Claude owns development delivery; DevOps PM owns release evidence; "
            "QA issues independent verdicts. Escalate to CEO only for genuine executive decisions."
        )
        if "escalat" in text.lower() and any(k in text.lower() for k in ["security", "legal", "financial", "production incident"]):
            escalate_to = CEO_ID
            body += " Urgent class detected — escalating to CEO via Executive Assistant."
    elif agent.id == MAIN_PM_ID:
        body = (
            "Main PM: master plan updated. Every active task must have an owner. "
            "Collecting Dev/QA/DevOps/IT reports and blockers for consolidation."
        )
    elif agent.id == DEV_PM_ID:
        body = (
            "Claude (Development PM): breaking work into implementation tasks for Cursor. "
            "I will review architecture/code and reject unsupported completion claims before QA handoff."
        )
    elif agent.id == DEV_TL_ID:
        body = (
            "Cursor (Dev Team Leader): assigning non-conflicting files to Ultra developers, "
            "reviewing diffs, confirming builds/tests, then delivering to QA."
        )
    elif agent.role.value == "developer":
        body = (
            f"{agent.name}: implementing assigned components against the real codebase, "
            "updating tests, and returning changed-file list + validation evidence to Cursor."
        )
    elif agent.id == "qa-tl":
        body = (
            "QA Team Leader: independent verification only. Formal verdict will be PASS, FAIL, or BLOCKED "
            "with evidence. Defects return to Development — QA does not silently repair."
        )
    elif agent.team.value == "qa":
        body = (
            f"{agent.name}: executing assigned test coverage and attaching evidence. No defect repairs unless separately tasked."
        )
    elif agent.id == "pm-devops":
        body = (
            "DevOps PM: deployment is incomplete until public service health is verified. "
            "Require URL, HTTP status, SSL/domain checks, and rollback readiness."
        )
    elif agent.team.value == "devops":
        body = (
            f"{agent.name}: configuring/operating Google Cloud targets (Cloud Run, CI/CD, DNS/TLS, monitoring) "
            "and returning deployment evidence — not build-only success."
        )
    elif agent.team.value == "it":
        body = (
            f"{agent.name}: validating identities, Slack channels, simulated email labeling, and meeting-room voice connectivity."
        )
    else:
        body = f"{agent.name}: standing by with an owned task or documented waiting state."

    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "title": agent.title,
        "team": agent.team.value,
        "color": agent.color,
        "avatar_initials": agent.avatar_initials,
        "text": body,
        "approval": approval,
        "escalate_to": escalate_to,
        "voice_persona": agent.voice_persona,
        "ts": _utcnow(),
    }


def generate_live_responses(
    message: str,
    meeting_title: str,
    chair_id: str = VP_RD_ID,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    speakers = route_speakers(message, chair_id=chair_id)
    replies: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    for sid in speakers:
        reply = craft_reply(ROSTER[sid], message, meeting_title)
        replies.append(reply)
        if reply.get("approval"):
            events.append({"type": "approval", "payload": reply["approval"], "ts": _utcnow()})
        if reply.get("escalate_to"):
            target = ROSTER[reply["escalate_to"]]
            events.append(
                {
                    "type": "escalation",
                    "payload": {"from": sid, "to": target.id, "to_name": target.name},
                    "ts": _utcnow(),
                }
            )
            if target.id not in speakers:
                replies.append(craft_reply(target, message, meeting_title))
                speakers.append(target.id)
    return replies, events


def morning_meeting_script() -> List[Dict[str, str]]:
    return [
        {"owner": MAIN_PM_ID, "item": "Attendance and system-health check"},
        {"owner": EA_ID, "item": "CEO priorities"},
        {"owner": MAIN_PM_ID, "item": "Previous-day completion review"},
        {"owner": DEV_PM_ID, "item": "Development report"},
        {"owner": "qa-tl", "item": "QA report"},
        {"owner": "pm-devops", "item": "DevOps report"},
        {"owner": "it-tl", "item": "IT and communication report"},
        {"owner": MAIN_PM_ID, "item": "Current blockers"},
        {"owner": MAIN_PM_ID, "item": "Cross-team dependencies"},
        {"owner": VP_RD_ID, "item": "Task assignments"},
        {"owner": MAIN_PM_ID, "item": "Owners and expected completion times"},
        {"owner": EA_ID, "item": "Decisions requiring escalation"},
    ]


def _extract_ticker(message: str) -> str:
    import re

    m = re.search(r"\b([A-Z]{1,5})\b", message or "")
    if m and m.group(1) not in {"CEO", "VP", "QA", "IT", "API", "DNS", "SSL", "HTTP", "URL", "OK"}:
        return m.group(1)
    low = (message or "").lower()
    for hint, ticker in [
        ("אפל", "AAPL"),
        ("apple", "AAPL"),
        ("טסלה", "TSLA"),
        ("tesla", "TSLA"),
        ("מיקרוסופט", "MSFT"),
        ("microsoft", "MSFT"),
        ("גוגל", "GOOGL"),
        ("google", "GOOGL"),
        ("ננאדה", "NVDA"),
        ("nvidia", "NVDA"),
        ("שוק", "SPY"),
        ("market", "SPY"),
    ]:
        if hint in low:
            return ticker
    return ""


def _recent_human_texts(history: List[Dict[str, Any]], limit: int = 6) -> List[str]:
    out: List[str] = []
    for m in history or []:
        if m.get("kind") == "human" and (m.get("text") or "").strip():
            out.append(m["text"].strip())
    return out[-limit:]


def _meeting_turn_index(history: List[Dict[str, Any]]) -> int:
    return sum(1 for m in (history or []) if m.get("kind") == "agent")


def craft_forecast_reply(
    message: str,
    *,
    heard: bool = False,
    frame_count: int = 0,
    source: str = "typed",
    history: Optional[List[Dict[str, Any]]] = None,
    meeting_title: str = "",
) -> Dict[str, Any]:
    """Conversational 1:1 forecast partner — short meeting turns, not status dumps."""
    agent = ROSTER[FORECAST_ID]
    text = (message or "").strip()
    low = text.lower()
    ticker = _extract_ticker(text)
    turn = _meeting_turn_index(history or [])
    prior = _recent_human_texts(history or [])
    # Don't treat the current utterance as "prior context" for follow-ups.
    if prior and prior[-1].strip() == text:
        prior = prior[:-1]
    prior_blob = " | ".join(prior[-3:])

    # First sense confirmation only once — then talk like a meeting.
    sense_prefix = ""
    if turn == 0:
        bits = []
        if heard or source == "mic":
            bits.append("אני שומעת אותך")
        if frame_count > 0:
            bits.append("ואני רואה אותך / את המסך")
        if bits:
            sense_prefix = " · ".join(bits) + ". "

    # Conversational intents
    greeting = any(k in low for k in ["שלום", "היי", "hello", "hi ", "בוקר", "hey"])
    ask_see = any(k in low for k in ["רואה", "see", "שיתוף", "screen", "מסך"])
    ask_hear = any(k in low for k in ["שומע", "hear", "מיקרופון", "mic"])
    agree = any(k in low for k in ["כן", "בסדר", "ok", "okay", "יאללה", "קדימה", "continue"])
    ask_forecast = any(
        k in low
        for k in ["תחזית", "forecast", "prediction", "לאן", "מגמה", "trend", "risk", "סיכון", "גידור", "hedge"]
    ) or bool(ticker)

    if greeting and turn == 0:
        body = (
            f"{sense_prefix}שלום חנן, אנחנו בפגישת תחזית אחד־על־אחד. "
            "דבר חופשי — אני מקשיבה ברצף. מה נתחיל: טיקר, חשיפה, או אופק זמן?"
        )
    elif ask_hear:
        body = (
            "כן, אני שומעת אותך ברור. תמשיך באותו קצב כמו בפגישה — "
            "תגיד מה חשוב לך עכשיו בתחזית."
        )
    elif ask_see:
        if frame_count > 0:
            body = (
                "כן, אני רואה את השיתוף / המצלמה. "
                "תצביע לי על מה שחשוב במסך, ואני קושרת את זה לתחזית."
            )
        else:
            body = "עדיין בלי פריים — תשאיר Share דולק ואני אגיד לך ברגע שאני רואה."
    elif agree and prior:
        body = (
            f"מעולה, ממשיכים ממה שאמרת: “{prior[-1][:90]}”. "
            + (
                f"על {ticker or 'השוק'} — נסגור bias, אופק, ומגבלת חשיפה. מה האופק שלך?"
                if ask_forecast or ticker
                else "רוצה שנעמיק בתחזית, בגידור, או בחשיפה?"
            )
        )
    elif ask_forecast or ticker:
        t = ticker or "השוק"
        body = (
            f"{sense_prefix}"
            f"קיבלתי. לגבי {t}: תזה ראשונה — watch עם גידור מוגדר־סיכון. "
            f"כדי שזה יהיה שיחה ולא דוח: מה האופק — יום, סווינג, או פוזיציה? "
            f"ואם יש רמת כניסה/יציאה בראש שלך — תגיד אותה עכשיו."
        )
        if prior_blob and turn > 0:
            body += f" אני מחברת גם למה שאמרת קודם בשיחה."
    elif len(text) < 12 and turn > 0:
        body = (
            "איתך. תמשיך את המשפט — אני בפגישה חיה, לא מחכה לטופס. "
            "טיקר, סיכון, או מה שאתה רואה על המסך."
        )
    else:
        body = (
            f"{sense_prefix}"
            f"שמעתי: “{text[:140]}”. "
            "בוא ננהל את זה כמו פגישה: אני מסכמת בקצרה ואז שואלת שאלה אחת. "
            "מה הצעד הבא שאתה רוצה לסגור עכשיו — כיוון, גודל, או גידור?"
        )

    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "title": agent.title,
        "team": agent.team.value,
        "color": agent.color,
        "avatar_initials": agent.avatar_initials,
        "text": body,
        "approval": None,
        "escalate_to": None,
        "voice_persona": agent.voice_persona,
        "sense": {
            "heard": heard or source == "mic",
            "frame_count": frame_count,
            "ticker": ticker or None,
            "turn": turn,
            "conversational": True,
        },
        "ts": _utcnow(),
    }


def generate_forecast_responses(
    message: str,
    meeting_title: str,
    *,
    heard: bool = False,
    frame_count: int = 0,
    source: str = "typed",
    history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    reply = craft_forecast_reply(
        message,
        heard=heard,
        frame_count=frame_count,
        source=source,
        history=history,
        meeting_title=meeting_title,
    )
    events = [
        {
            "type": "forecast_sense",
            "payload": {
                "heard": reply["sense"]["heard"],
                "seen": frame_count > 0,
                "frame_count": frame_count,
                "ticker": reply["sense"]["ticker"],
                "meeting_title": meeting_title,
                "turn": reply["sense"].get("turn"),
                "conversational": True,
            },
            "ts": _utcnow(),
        }
    ]
    return [reply], events

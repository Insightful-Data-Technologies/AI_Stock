"""Deterministic multi-agent response engine with escalation + approvals."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from org_platform.agents.roster import (
    CEO_ID,
    ROSTER,
    SUPER_ADMIN_ID,
    OrgAgent,
    escalate_from,
    next_approver,
)


APPROVAL_PATTERNS = re.compile(
    r"\b(approve|approved|authorization|sign[\s-]?off|green[\s-]?light|go ahead)\b",
    re.I,
)
ESCALATE_PATTERNS = re.compile(
    r"\b(escalate|urgent|blocker|blocked|critical|sev-?1|outage|ceo|executive)\b",
    re.I,
)
DEPLOY_PATTERNS = re.compile(r"\b(deploy|release|production|prod|rollout|cloud run)\b", re.I)
TEST_PATTERNS = re.compile(r"\b(test|qa|regression|e2e|acceptance|bug)\b", re.I)
INFRA_PATTERNS = re.compile(r"\b(infra|devops|pipeline|ci/?cd|redis|firestore|secret|iam)\b", re.I)
IT_PATTERNS = re.compile(r"\b(access|vpn|laptop|account|sso|identity|permission)\b", re.I)
MEETING_PATTERNS = re.compile(r"\b(agenda|standup|sync|meeting|status)\b", re.I)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def route_speakers(message: str, chair_id: str = SUPER_ADMIN_ID) -> List[str]:
    """Pick which agents should respond live to a human message."""
    speakers: List[str] = []
    text = message or ""

    if MEETING_PATTERNS.search(text) or not text.strip():
        speakers.extend(["pm-nova", chair_id])
    if DEPLOY_PATTERNS.search(text) or INFRA_PATTERNS.search(text):
        speakers.extend(["devops-lead-kai", "devops-lee"])
    if TEST_PATTERNS.search(text):
        speakers.extend(["qa-lead-sam", "qa-tess"])
    if IT_PATTERNS.search(text):
        speakers.extend(["it-lead-ava", "it-ben"])
    if re.search(r"\b(code|api|frontend|backend|implement|feature)\b", text, re.I):
        speakers.extend(["dev-lead-mira", "dev-jordan", "dev-rina"])
    if APPROVAL_PATTERNS.search(text):
        speakers.append(chair_id)
    if ESCALATE_PATTERNS.search(text) or "chanan" in text.lower() or "ceo" in text.lower():
        speakers.extend([chair_id, CEO_ID])

    # Always include chair for control surface
    if chair_id not in speakers:
        speakers.insert(0, chair_id)

    # Dedupe preserving order
    seen = set()
    ordered: List[str] = []
    for s in speakers:
        if s in ROSTER and s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered[:6]


def craft_reply(agent: OrgAgent, message: str, meeting_title: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lower = text.lower()
    approval = None
    escalate_to = None

    if agent.id == SUPER_ADMIN_ID:
        if APPROVAL_PATTERNS.search(text) or DEPLOY_PATTERNS.search(text) or not text:
            approval = {
                "status": "approved",
                "by": agent.id,
                "scope": "org-wide (super admin)",
                "note": "VP R&D Super Admin blanket approval granted.",
            }
            body = (
                f"As VP R&D Super Admin I am chairing this room for “{meeting_title}”. "
                "All team tracks are cleared to proceed under my authority — Dev, QA, DevOps, IT, and PMO. "
                "I will escalate to CEO Chanan Zevin only for company-level strategic risk."
            )
            if text:
                body = (
                    f"Acknowledged: “{text}”. {body} "
                    "Action: owners respond with concrete next steps in the next 60 seconds."
                )
        elif ESCALATE_PATTERNS.search(text):
            escalate_to = CEO_ID
            body = (
                "Severity noted. I am escalating to CEO Chanan Zevin now while keeping delivery teams moving "
                "on mitigation in parallel."
            )
        else:
            body = (
                f"VP R&D here — owning “{text}”. Routing to the right leads and approving the execution path."
            )
    elif agent.id == CEO_ID:
        if escalate_to or ESCALATE_PATTERNS.search(text) or APPROVAL_PATTERNS.search(text):
            approval = {
                "status": "approved",
                "by": agent.id,
                "scope": "executive",
                "note": "CEO final endorsement.",
            }
        body = (
            "Chanan Zevin speaking. I expect crisp ownership, measurable outcomes, and no silent blockers. "
            f"On “{text or meeting_title}”: proceed with VP R&D Super Admin as executive operator. "
            "Escalate back to me only if capital, legal, or brand risk appears."
        )
    elif agent.role.value.startswith("project_manager") or agent.team.value == "pmo":
        body = (
            f"{agent.name} (PM): Agenda locked for “{meeting_title}”. "
            f"Captured ask: “{text or 'general sync'}”. "
            "Owners: Dev (Mira), QA (Sam), DevOps (Kai), IT (Ava). "
            "I will track blockers and escalate to VP R&D if dates slip."
        )
    elif agent.team.value == "engineering":
        body = (
            f"{agent.name}: Implementation path for “{text or 'the current initiative'}” — "
            "split API/WebSocket contracts first, then UI participants + history, then E2E gate. "
            "Estimate follows after DevOps confirms runtime targets."
        )
    elif agent.team.value == "qa":
        body = (
            f"{agent.name}: Acceptance gates — join room, see all participants, send message, "
            "receive live multi-agent replies, trigger voice playback, escalate, and verify history persistence. "
            "No release without evidence."
        )
    elif agent.team.value == "devops":
        body = (
            f"{agent.name}: Runtime plan — containerized FastAPI service, health checks, "
            "Redis/Firestore adapters when credentials exist, Secret Manager for keys, Cloud Run deploy. "
            "Rollback via prior revision."
        )
    elif agent.team.value == "it":
        body = (
            f"{agent.name}: Access posture — least privilege for service accounts, no secrets in chat logs, "
            "SSO-ready operator seat for VP Super Admin, audit trail on approvals/escalations."
        )
    else:
        body = f"{agent.name}: Noted — standing by."

    # Auto-escalation suggestion when non-approver hits approval language
    if APPROVAL_PATTERNS.search(text) and not agent.can_approve:
        nxt = next_approver(agent.id)
        if nxt:
            escalate_to = nxt.id
            body += f" Escalating approval to {nxt.name}."

    if ESCALATE_PATTERNS.search(text) and agent.id not in (SUPER_ADMIN_ID, CEO_ID):
        nxt = escalate_from(agent.id) or ROSTER[SUPER_ADMIN_ID]
        escalate_to = nxt.id
        body += f" Flagging up to {nxt.name}."

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
    chair_id: str = SUPER_ADMIN_ID,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    speakers = route_speakers(message, chair_id=chair_id)
    replies: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    for sid in speakers:
        agent = ROSTER[sid]
        reply = craft_reply(agent, message, meeting_title)
        replies.append(reply)
        if reply.get("approval"):
            events.append({"type": "approval", "payload": reply["approval"], "ts": _utcnow()})
        if reply.get("escalate_to"):
            target = ROSTER.get(reply["escalate_to"])
            events.append(
                {
                    "type": "escalation",
                    "payload": {
                        "from": agent.id,
                        "to": reply["escalate_to"],
                        "to_name": target.name if target else reply["escalate_to"],
                    },
                    "ts": _utcnow(),
                }
            )
            # Ensure escalated party also speaks if missing
            if reply["escalate_to"] not in speakers:
                esc_agent = ROSTER[reply["escalate_to"]]
                esc_reply = craft_reply(esc_agent, message, meeting_title)
                replies.append(esc_reply)
                speakers.append(reply["escalate_to"])
    return replies, events

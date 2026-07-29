"""FastAPI application — SRS AI Enterprise Team and Communication Platform."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from org_platform.agents.comm_tests import run_all_communication_tests, run_communication_test
from org_platform.agents.engine import generate_live_responses, morning_meeting_script
from org_platform.agents.roster import (
    CEO_ID,
    COMPANY,
    DEV_PM_ID,
    DEV_TL_ID,
    EA_ID,
    MAIN_PM_ID,
    ROSTER,
    VP_RD_ID,
    hierarchy_edges,
    public_roster,
)
from org_platform.publish.env_loader import load_dotenv
from org_platform.publish.godaddy import GoDaddyError
from org_platform.publish.publisher import build_publish_plan, credentials_status, run_publish
from org_platform.store.platform import get_platform

# Load /workspace/.env (or cwd .env) so GODADDY_* keys are available when present.
load_dotenv()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Insightful Data Technologies – 2.o AI",
    version="2.0.0",
    description="AI Capital Enterprise Team — Google Cloud Enterprise / Vertex AI Agent Platform",
)

rooms: Dict[str, Set[WebSocket]] = {}


def P():
    return get_platform()


class CreateMeetingRequest(BaseModel):
    title: str = "Daily Morning Meeting"
    chair_id: str = VP_RD_ID
    participant_ids: Optional[List[str]] = None
    seed_intro: bool = True
    morning: bool = False
    one_on_one: bool = False


class ChatRequest(BaseModel):
    text: str
    sender_name: str = "Human Operator"
    sender_id: str = "human-operator"


class EscalateRequest(BaseModel):
    from_agent_id: str = VP_RD_ID
    reason: str = "Operator-requested escalation"


class MessageRequest(BaseModel):
    channel_id: str
    sender_id: str
    text: str
    thread_id: Optional[str] = None
    mentions: List[str] = Field(default_factory=list)
    priority: str = "normal"
    escalation_label: Optional[str] = None


class EmailRequest(BaseModel):
    from_id: str
    to_email: str
    subject: str
    body: str


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    business_objective: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    team_leader: Optional[str] = None
    priority: str = "P2"
    created_by: str = VP_RD_ID
    target_environment: str = "staging"


class TaskAssign(BaseModel):
    owner: str
    team_leader: str
    actor_id: str = DEV_PM_ID


class TaskTransition(BaseModel):
    status: str
    actor_id: str
    note: str = ""


class TaskEvidence(BaseModel):
    actor_id: str
    evidence: Dict[str, Any]


class QADecision(BaseModel):
    decision: str
    by: str = "qa-tl"
    notes: str = ""


class FinalApproval(BaseModel):
    by: str = VP_RD_ID
    note: str = ""


@app.get("/api/health")
def health() -> Dict[str, Any]:
    p = P()
    return {
        "ok": True,
        "service": "ai-capital-enterprise-team",
        "company": COMPANY,
        "agents": len(ROSTER),
        "store": p.meetings.backend_info(),
        "email": p.email.status(),
        "tasks": p.tasks.stats(),
        "channels": len(p.messages.list_channels()),
        "project_target": os.environ.get("GOOGLE_CLOUD_PROJECT", COMPANY["gcp_project"]),
    }


@app.get("/api/company")
def company() -> Dict[str, Any]:
    return COMPANY


@app.get("/api/org")
def org() -> Dict[str, Any]:
    return {
        "company": COMPANY,
        "roster": public_roster(),
        "hierarchy": hierarchy_edges(),
        "ceo": CEO_ID,
        "ea": EA_ID,
        "vp_rd": VP_RD_ID,
        "main_pm": MAIN_PM_ID,
        "dev_pm": DEV_PM_ID,
        "dev_tl": DEV_TL_ID,
    }


@app.get("/api/channels")
def channels() -> Dict[str, Any]:
    return {"channels": P().messages.list_channels()}


@app.get("/api/channels/{channel_id}/messages")
def channel_history(channel_id: str, q: Optional[str] = None) -> Dict[str, Any]:
    try:
        return {"messages": P().messages.history(channel_id, q=q)}
    except KeyError:
        raise HTTPException(404, "channel not found")


@app.post("/api/channels/messages")
def post_channel_message(body: MessageRequest) -> Dict[str, Any]:
    agent = ROSTER.get(body.sender_id)
    if not agent:
        raise HTTPException(400, "unknown sender")
    try:
        msg = P().messages.post(
            body.channel_id,
            body.sender_id,
            agent.name,
            body.text,
            thread_id=body.thread_id,
            mentions=body.mentions,
            priority=body.priority,
            escalation_label=body.escalation_label,
        )
    except KeyError:
        raise HTTPException(404, "channel not found")
    P().audit.append("message_posted", body.sender_id, {"message_id": msg["id"], "channel_id": body.channel_id})
    return {"message": msg}


@app.post("/api/channels/{channel_id}/messages/{message_id}/ack")
def ack_message(channel_id: str, message_id: str, agent_id: str) -> Dict[str, Any]:
    try:
        msg = P().messages.ack(channel_id, message_id, agent_id)
    except KeyError:
        raise HTTPException(404, "message not found")
    P().audit.append("message_acked", agent_id, {"message_id": message_id, "channel_id": channel_id})
    return {"message": msg}


@app.post("/api/email/send")
def send_email(body: EmailRequest) -> Dict[str, Any]:
    agent = ROSTER.get(body.from_id)
    if not agent:
        raise HTTPException(400, "unknown sender")
    P().email.ensure_mailbox(agent.email, agent.id)
    msg = P().email.send(agent.email, body.to_email, body.subject, body.body, from_id=agent.id)
    P().audit.append("email_sent", agent.id, {"email_id": msg["id"], "mode": msg["mode"]})
    return {"email": msg, "warning": msg["limitation"]}


@app.get("/api/email/inbox/{email}")
def inbox(email: str) -> Dict[str, Any]:
    return {"mode": "SIMULATED", "messages": P().email.inbox(email)}


@app.get("/api/email/status")
def email_status() -> Dict[str, Any]:
    return P().email.status()


@app.post("/api/tasks")
def create_task(body: TaskCreate) -> Dict[str, Any]:
    task = P().tasks.create(body.model_dump())
    P().audit.append("task_created", body.created_by, {"task_id": task["id"]})
    return {"task": task}


@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None, owner: Optional[str] = None) -> Dict[str, Any]:
    return {"tasks": P().tasks.list(status=status, owner=owner), "stats": P().tasks.stats()}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    task = P().tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    return {"task": task}


@app.post("/api/tasks/{task_id}/assign")
def assign_task(task_id: str, body: TaskAssign) -> Dict[str, Any]:
    if not P().tasks.get(task_id):
        raise HTTPException(404, "task not found")
    task = P().tasks.assign(task_id, body.owner, body.team_leader, body.actor_id)
    P().audit.append("task_assigned", body.actor_id, {"task_id": task_id, "owner": body.owner})
    # notify channels
    owner = ROSTER[body.owner]
    P().messages.post(
        "development" if owner.team.value == "development" else "project-management",
        body.actor_id,
        ROSTER[body.actor_id].name,
        f"Task {task_id} assigned to {owner.name}",
        mentions=[body.owner, body.team_leader],
    )
    return {"task": task}


@app.post("/api/tasks/{task_id}/transition")
def transition_task(task_id: str, body: TaskTransition) -> Dict[str, Any]:
    if not P().tasks.get(task_id):
        raise HTTPException(404, "task not found")
    task = P().tasks.transition(task_id, body.status, body.actor_id, body.note)
    P().audit.append("task_status", body.actor_id, {"task_id": task_id, "status": body.status, "note": body.note})
    return {"task": task}


@app.post("/api/tasks/{task_id}/evidence")
def add_evidence(task_id: str, body: TaskEvidence) -> Dict[str, Any]:
    if not P().tasks.get(task_id):
        raise HTTPException(404, "task not found")
    task = P().tasks.add_evidence(task_id, body.evidence, body.actor_id)
    P().audit.append("task_evidence", body.actor_id, {"task_id": task_id})
    return {"task": task}


@app.post("/api/tasks/{task_id}/qa")
def qa_decision(task_id: str, body: QADecision) -> Dict[str, Any]:
    if body.decision not in {"PASS", "FAIL", "BLOCKED"}:
        raise HTTPException(400, "decision must be PASS|FAIL|BLOCKED")
    task = P().tasks.set_qa(task_id, body.decision, body.by, body.notes)
    P().messages.post(
        "qa",
        body.by,
        ROSTER[body.by].name,
        f"QA {body.decision} on {task_id}: {body.notes}",
        priority="high",
    )
    P().audit.append("qa_decision", body.by, {"task_id": task_id, "decision": body.decision})
    return {"task": task}


@app.post("/api/tasks/{task_id}/approve")
def final_approve(task_id: str, body: FinalApproval) -> Dict[str, Any]:
    task = P().tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    if not task.get("qa_decision") or task["qa_decision"].get("decision") != "PASS":
        raise HTTPException(400, "QA PASS required before final approval")
    if not task.get("evidence"):
        raise HTTPException(400, "evidence required")
    task = P().tasks.approve(task_id, body.by, body.note)
    P().messages.post(
        "release-approvals",
        body.by,
        ROSTER[body.by].name,
        f"FINAL APPROVAL {task_id}: {body.note}",
        priority="high",
    )
    P().audit.append("final_approval", body.by, {"task_id": task_id})
    return {"task": task}


@app.post("/api/comm-tests/run-all")
def comm_test_all() -> Dict[str, Any]:
    return run_all_communication_tests()


@app.post("/api/comm-tests/{agent_id}")
def comm_test_one(agent_id: str) -> Dict[str, Any]:
    if agent_id not in ROSTER:
        raise HTTPException(404, "unknown agent")
    return run_communication_test(agent_id)


@app.get("/api/comm-tests")
def comm_test_status() -> Dict[str, Any]:
    return {"results": P().comm_results}


@app.get("/api/audit")
def audit(limit: int = 200, event_type: Optional[str] = None) -> Dict[str, Any]:
    return {"events": P().audit.list(limit=limit, event_type=event_type)}


@app.get("/api/dashboards/executive")
def exec_dashboard() -> Dict[str, Any]:
    stats = P().tasks.stats()
    live_one_on_one = _find_live_one_on_one()
    return {
        "company": COMPANY,
        "operational_status": "online",
        "active_projects": ["AI Capital Enterprise Team"],
        "one_on_one": {
            "available": True,
            "path": "/dashboard",
            "simulation_path": "/meeting-simulation.html",
            "live_meeting_id": live_one_on_one["id"] if live_one_on_one else None,
            "live_meeting_title": live_one_on_one.get("title") if live_one_on_one else None,
            "status": "live" if live_one_on_one else "ready",
        },
        "tasks": stats,
        "departments": {
            t: len([a for a in ROSTER.values() if a.team.value == t])
            for t in ["executive", "pmo", "development", "qa", "devops", "it"]
        },
        "production_incidents": len(P().messages.history("production-incidents")),
        "release_status": P().messages.history("release-approvals")[-5:],
        "ceo_approvals_queue": [
            t for t in P().tasks.list() if t["status"] == "escalated"
        ],
        "agent_availability": {
            "total": len(ROSTER),
            "comm_pass": sum(1 for r in P().comm_results.values() if r.get("status") == "PASS"),
            "comm_blocked": sum(1 for r in P().comm_results.values() if r.get("status") == "BLOCKED"),
        },
        "communication_health": {
            "channels": len(P().messages.list_channels()),
            "email": P().email.status(),
        },
    }


@app.get("/api/dashboards/management")
def mgmt_dashboard() -> Dict[str, Any]:
    tasks = P().tasks.list()
    by_team: Dict[str, List[dict]] = {}
    for t in tasks:
        owner = ROSTER.get(t.get("owner") or "")
        team = owner.team.value if owner else "unassigned"
        by_team.setdefault(team, []).append(
            {"id": t["id"], "title": t["title"], "owner": t.get("owner"), "status": t["status"]}
        )
    return {
        "company": COMPANY,
        "tasks_by_team": by_team,
        "blockers": [t for t in tasks if t["status"] in {"blocked", "escalated"}],
        "qa_results": [t for t in tasks if t.get("qa_decision")],
        "recent_reports": P().messages.history("agent-reports")[-20:],
        "escalation_queue": [t for t in tasks if t["status"] == "escalated"],
    }


@app.get("/api/dashboards/communication")
def comm_dashboard() -> Dict[str, Any]:
    return {
        "company": COMPANY,
        "online_agents": list(ROSTER.keys()),
        "message_channels": P().messages.list_channels(),
        "email_health": P().email.status(),
        "meeting_room_health": {"service": "live", "webrtc": "browser_webrtc_ready", "tts": "neural_browser", "stt": "webkit_speech"},
        "voice_readiness": True,
        "failed_comm_tests": [r for r in P().comm_results.values() if r.get("status") != "PASS"],
        "comm_results": P().comm_results,
    }


@app.post("/api/workflows/e2e-demo")
def e2e_workflow_demo() -> Dict[str, Any]:
    """SRS §19 acceptance workflow demonstration."""
    p = P()
    # 1 hierarchy already exists
    # 2 communication tests
    comm = run_all_communication_tests()

    # 3-8 development -> cursor -> claude -> QA cycle
    task = p.tasks.create(
        {
            "title": "Implement meeting transcript action-item extractor",
            "description": "Add endpoint and UI affordance for action items from morning meetings",
            "business_objective": "Satisfy SRS morning meeting outputs",
            "acceptance_criteria": [
                "API returns action items",
                "QA independent PASS",
                "Evidence attached",
            ],
            "created_by": DEV_PM_ID,
            "priority": "P1",
            "target_environment": "production",
        }
    )
    task = p.tasks.assign(task["id"], "dev-ultra-1", DEV_TL_ID, DEV_PM_ID)
    task = p.tasks.transition(task["id"], "acknowledged", "dev-ultra-1", "Ack to Cursor")
    p.messages.post("development", "dev-ultra-1", ROSTER["dev-ultra-1"].name, f"Progress on {task['id']} to Cursor", mentions=[DEV_TL_ID])
    task = p.tasks.transition(task["id"], "in_progress", "dev-ultra-1", "Coding extractor")
    task = p.tasks.add_evidence(
        task["id"],
        {
            "type": "code_change",
            "files": ["org_platform/api/app.py", "org_platform/agents/engine.py"],
            "tests": ["org_platform/tests/test_srs_acceptance.py"],
            "result": "unit_pass",
        },
        "dev-ultra-1",
    )
    task = p.tasks.transition(task["id"], "review", DEV_TL_ID, "Cursor reviewed diff")
    p.messages.post("development", DEV_TL_ID, "Cursor", f"Review complete for {task['id']} → Claude", mentions=[DEV_PM_ID])
    task = p.tasks.transition(task["id"], "qa", DEV_PM_ID, "Claude submits to QA")
    p.messages.post("qa", DEV_PM_ID, "Claude", f"Please QA {task['id']}", mentions=["qa-tl"])

    # defect cycle
    task = p.tasks.set_qa(task["id"], "FAIL", "qa-tl", "Missing mobile screenshot evidence")
    task = p.tasks.transition(task["id"], "in_progress", "dev-ultra-1", "Fixing QA FAIL")
    task = p.tasks.add_evidence(
        task["id"],
        {"type": "screenshot", "desktop": True, "mobile": True, "url": "http://127.0.0.1:8080/"},
        "dev-ultra-1",
    )
    task = p.tasks.transition(task["id"], "qa", DEV_TL_ID, "Resubmitted to QA")
    task = p.tasks.set_qa(task["id"], "PASS", "qa-tl", "Independent verification passed")

    # 9-10 DevOps deploy + health
    deploy = p.tasks.create(
        {
            "title": f"Deploy approved build for {task['id']}",
            "description": "Cloud Run deploy with public URL verification",
            "business_objective": "Production verification",
            "acceptance_criteria": ["Public URL", "HTTP 200", "Health OK"],
            "created_by": "pm-devops",
            "priority": "P1",
            "target_environment": "production",
        }
    )
    deploy = p.tasks.assign(deploy["id"], "devops-1", "devops-tl", "pm-devops")
    deploy = p.tasks.transition(deploy["id"], "acknowledged", "devops-1", "Ack deploy")
    deploy = p.tasks.transition(deploy["id"], "in_progress", "devops-1", "Deploying")
    deploy = p.tasks.add_evidence(
        deploy["id"],
        {
            "type": "deployment",
            "public_url": os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8080"),
            "http_status": 200,
            "health": "/api/health",
            "note": "GCP Cloud Run blocked without auth; public tunnel/local verified",
        },
        "devops-1",
    )
    deploy = p.tasks.set_qa(deploy["id"], "PASS", "qa-3", "Production smoke verified")
    deploy = p.tasks.approve(deploy["id"], "pm-devops", "Deployment evidence accepted")
    task = p.tasks.approve(task["id"], VP_RD_ID, "VP R&D final approval with evidence")

    # 11 IT simulated communication failure
    it_case = p.tasks.create(
        {
            "title": "Diagnose simulated Slack delivery failure",
            "description": "IT diagnosis drill",
            "created_by": "it-tl",
            "owner": "it-2",
            "team_leader": "it-tl",
            "priority": "P1",
        }
    )
    it_case = p.tasks.assign(it_case["id"], "it-2", "it-tl", "it-tl")
    it_case = p.tasks.transition(it_case["id"], "in_progress", "it-2", "Checking channel delivery")
    it_case = p.tasks.add_evidence(it_case["id"], {"type": "diagnosis", "finding": "reconnect websocket; delivery restored"}, "it-2")
    it_case = p.tasks.transition(it_case["id"], "review", "it-tl", "IT TL reviewed")
    it_case = p.tasks.set_qa(it_case["id"], "PASS", "qa-2", "Comms restored")
    it_case = p.tasks.approve(it_case["id"], "it-tl", "Closed")

    # 12-14 morning meeting
    meeting = p.meetings.create_meeting(
        title="Daily Morning Meeting",
        chair_id=VP_RD_ID,
        participant_ids=list(ROSTER.keys()),
        created_by=MAIN_PM_ID,
    )
    agenda = morning_meeting_script()
    transcript = []
    action_items = []
    for item in agenda:
        owner = ROSTER[item["owner"]]
        line = f"{owner.name}: {item['item']} — status green with owners assigned."
        transcript.append({"speaker": owner.id, "text": line})
        p.meetings.append_message(
            meeting["id"],
            {"kind": "agent", "sender_id": owner.id, "sender_name": owner.name, "text": line},
        )
        action_items.append(
            {
                "item": item["item"],
                "owner": owner.id,
                "owner_name": owner.name,
                "due": "end_of_day",
            }
        )
    p.meetings.append_events(
        meeting["id"],
        [
            {"type": "morning_agenda", "payload": {"agenda": agenda}, "ts": meeting["created_at"]},
            {"type": "action_items", "payload": {"items": action_items}, "ts": meeting["created_at"]},
        ],
    )

    # 15 escalation path
    blocker = p.tasks.create(
        {
            "title": "Production SSL renewal blocked",
            "description": "Certificate authority rate limit",
            "created_by": "devops-2",
            "priority": "P0",
        }
    )
    blocker = p.tasks.assign(blocker["id"], "devops-2", "devops-tl", "pm-devops")
    blocker = p.tasks.transition(blocker["id"], "blocked", "devops-2", "CA rate limit")
    blocker = p.tasks.transition(blocker["id"], "escalated", "devops-tl", "Escalated to DevOps PM → VP R&D")
    p.messages.post(
        "production-incidents",
        "devops-tl",
        "Kai Nakamura",
        f"ESCALATION {blocker['id']} → pm-devops → vp-rd",
        mentions=["pm-devops", VP_RD_ID],
        priority="urgent",
        escalation_label="production",
    )
    p.audit.append("escalation_path", "devops-tl", {"task_id": blocker["id"], "path": ["devops-2", "devops-tl", "pm-devops", VP_RD_ID]})

    # 16 EA executive summary
    summary = {
        "prepared_by": EA_ID,
        "for": CEO_ID,
        "headline": "AI Capital Enterprise Team operational",
        "completed": [task["id"], deploy["id"], it_case["id"]],
        "blockers": [blocker["id"]],
        "asks_for_ceo": ["Monitor SSL escalation only if customer-facing deadline slips"],
        "noise_filtered": True,
    }
    p.messages.post(
        "executive-management",
        EA_ID,
        ROSTER[EA_ID].name,
        f"EXEC SUMMARY for CEO: {summary['headline']}. Completed {len(summary['completed'])}, blockers {len(summary['blockers'])}.",
        mentions=[CEO_ID, VP_RD_ID],
        priority="high",
        attachments=[summary],
    )
    p.audit.append("executive_summary", EA_ID, summary)

    return {
        "status": "PASS" if comm["status"] == "PASS" else "BLOCKED",
        "communication_tests": comm,
        "dev_task": p.tasks.get(task["id"]),
        "deploy_task": p.tasks.get(deploy["id"]),
        "it_task": p.tasks.get(it_case["id"]),
        "blocker_task": p.tasks.get(blocker["id"]),
        "morning_meeting_id": meeting["id"],
        "action_items": action_items,
        "executive_summary": summary,
        "audit_events": len(p.audit.list(limit=1000)),
    }


@app.get("/api/meetings")
def list_meetings() -> Dict[str, Any]:
    return {"meetings": P().meetings.list_meetings()}


def _find_live_one_on_one() -> Optional[Dict[str, Any]]:
    for summary in P().meetings.list_meetings():
        if summary.get("status") != "live":
            continue
        meeting = P().meetings.get(summary["id"]) or summary
        title = meeting.get("title") or ""
        events = meeting.get("events") or []
        if any(e.get("type") == "one_on_one" for e in events) or re_search_one_on_one(title):
            return meeting
    return None


def re_search_one_on_one(title: str) -> bool:
    return bool(re.search(r"1:1|one[- ]?on[- ]?one", title, re.I))


@app.post("/api/meetings/one-on-one/ensure")
async def ensure_one_on_one_meeting() -> Dict[str, Any]:
    """Find a live Ultra Agent 1:1 room or create one (used by meeting-simulation.html)."""
    existing = _find_live_one_on_one()
    if existing:
        return {"meeting": existing, "created": False}
    created = await create_meeting(
        CreateMeetingRequest(
            title="Ultra Agent Meeting 1:1",
            chair_id=VP_RD_ID,
            participant_ids=[CEO_ID, VP_RD_ID, DEV_TL_ID],
            seed_intro=True,
            morning=False,
            one_on_one=True,
        )
    )
    return {**created, "created": True}


@app.post("/api/meetings")
async def create_meeting(body: CreateMeetingRequest) -> Dict[str, Any]:
    if body.chair_id not in ROSTER:
        raise HTTPException(400, f"Unknown chair_id {body.chair_id}")
    if body.one_on_one:
        # CEO ↔ Cursor (VP R&D chair) private room — voice, barge-in, screen share, summary.
        title = body.title if body.title and body.title != "Daily Morning Meeting" else "Ultra Agent Meeting 1:1"
        chair_id = body.chair_id if body.chair_id in {CEO_ID, VP_RD_ID, DEV_TL_ID} else VP_RD_ID
        participants = body.participant_ids or [CEO_ID, VP_RD_ID, DEV_TL_ID]
        # Keep the roster tight for a true 1:1 surface.
        participants = [pid for pid in participants if pid in ROSTER]
        if CEO_ID not in participants:
            participants.insert(0, CEO_ID)
        if VP_RD_ID not in participants:
            participants.append(VP_RD_ID)
        if DEV_TL_ID not in participants:
            participants.append(DEV_TL_ID)
    else:
        title = body.title
        chair_id = body.chair_id
        participants = body.participant_ids or list(ROSTER.keys())
    meeting = P().meetings.create_meeting(
        title=title,
        chair_id=chair_id,
        participant_ids=participants,
        created_by="human-operator",
    )
    if body.one_on_one:
        P().meetings.append_events(
            meeting["id"],
            [
                {
                    "type": "one_on_one",
                    "payload": {
                        "mode": "ultra-agent-1-1",
                        "features": ["voice", "barge-in", "screen-share", "summary"],
                        "participants": participants,
                    },
                    "ts": meeting["created_at"],
                }
            ],
        )
    if body.morning:
        P().meetings.append_events(
            meeting["id"],
            [{"type": "morning_agenda", "payload": {"agenda": morning_meeting_script()}, "ts": meeting["created_at"]}],
        )
    if body.seed_intro:
        if body.one_on_one:
            text = "Open the one-on-one room. Confirm voice, barge-in, screen share, and summary are ready."
        elif body.morning:
            text = "Open the morning meeting and confirm attendance."
        else:
            text = "Open the meeting and confirm all teams are present."
        replies, events = generate_live_responses(text, meeting["title"], chair_id=meeting["chair_id"])
        P().meetings.append_message(
            meeting["id"],
            {"kind": "human", "sender_id": "human-operator", "sender_name": "Human Operator", "text": text},
        )
        for r in replies:
            P().meetings.append_message(
                meeting["id"],
                {
                    "kind": "agent",
                    "sender_id": r["agent_id"],
                    "sender_name": r["agent_name"],
                    "text": r["text"],
                    "meta": r,
                },
            )
        P().meetings.append_events(meeting["id"], events)
        meeting = P().meetings.get(meeting["id"])
    P().audit.append(
        "meeting_created",
        chair_id,
        {"meeting_id": meeting["id"], "morning": body.morning, "one_on_one": body.one_on_one},
    )
    return {"meeting": meeting}


@app.get("/api/meetings/{meeting_id}")
def get_meeting(meeting_id: str) -> Dict[str, Any]:
    meeting = P().meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return {"meeting": meeting}


@app.post("/api/meetings/{meeting_id}/messages")
async def post_message(meeting_id: str, body: ChatRequest) -> Dict[str, Any]:
    meeting = P().meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.get("status") != "live":
        raise HTTPException(400, "Meeting is not live")
    human = P().meetings.append_message(
        meeting_id,
        {
            "kind": "human",
            "sender_id": body.sender_id,
            "sender_name": body.sender_name,
            "text": body.text,
        },
    )
    replies, events = generate_live_responses(body.text, meeting["title"], chair_id=meeting["chair_id"])
    agent_msgs = []
    for r in replies:
        agent_msgs.append(
            P().meetings.append_message(
                meeting_id,
                {
                    "kind": "agent",
                    "sender_id": r["agent_id"],
                    "sender_name": r["agent_name"],
                    "text": r["text"],
                    "meta": r,
                },
            )
        )
    P().meetings.append_events(meeting_id, events)
    payload = {"human": human, "replies": agent_msgs, "events": events, "meeting": P().meetings.get(meeting_id)}
    await broadcast(meeting_id, {"type": "chat_burst", **payload})
    return payload


@app.post("/api/meetings/{meeting_id}/escalate")
async def escalate(meeting_id: str, body: EscalateRequest) -> Dict[str, Any]:
    if not P().meetings.get(meeting_id):
        raise HTTPException(404, "Meeting not found")
    return await post_message(
        meeting_id,
        ChatRequest(
            text=f"ESCALATE TO CEO (security/financial/legal/production): {body.reason}",
            sender_name="VP R&D",
            sender_id=body.from_agent_id,
        ),
    )


@app.post("/api/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str) -> Dict[str, Any]:
    meeting = P().meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    ended = P().meetings.end_meeting(meeting_id)
    await broadcast(meeting_id, {"type": "meeting_ended", "meeting": ended})
    return {"meeting": ended}


async def broadcast(meeting_id: str, payload: Dict[str, Any]) -> None:
    dead: List[WebSocket] = []
    for ws in list(rooms.get(meeting_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        rooms.get(meeting_id, set()).discard(ws)


@app.websocket("/ws/meetings/{meeting_id}")
async def meeting_ws(websocket: WebSocket, meeting_id: str) -> None:
    meeting = P().meetings.get(meeting_id)
    if not meeting:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    rooms.setdefault(meeting_id, set()).add(websocket)
    await websocket.send_json({"type": "snapshot", "meeting": meeting, "roster": public_roster(), "company": COMPANY})
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "chat":
                await post_message(
                    meeting_id,
                    ChatRequest(
                        text=data.get("text", ""),
                        sender_name=data.get("sender_name", "Human Operator"),
                        sender_id=data.get("sender_id", "human-operator"),
                    ),
                )
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "escalate":
                await escalate(meeting_id, EscalateRequest(reason=data.get("reason", "Operator escalation")))
    except WebSocketDisconnect:
        pass
    finally:
        rooms.get(meeting_id, set()).discard(websocket)


studio_rooms: Dict[str, Set[WebSocket]] = {}


class CreateStudioRequest(BaseModel):
    title: str = "VP Delivery Studio — Screen Share Briefing"


class StudioChatRequest(BaseModel):
    text: str
    sender_id: str = CEO_ID
    sender_name: str = "Me (Chanan Zevin)"


class StudioFrameRequest(BaseModel):
    data_url: str
    note: str = ""


class StudioShareRequest(BaseModel):
    active: bool


class StudioDeliverRequest(BaseModel):
    briefing: str
    owner: str = "devops-1"
    title: Optional[str] = None
    priority: str = "P1"


def _vp_studio_reply(text: str, screen_sharing: bool, frame_count: int) -> str:
    seen = (
        f"I can see your shared screen ({frame_count} frame(s) received)."
        if screen_sharing or frame_count
        else "Share your screen so I can follow visually while you brief me."
    )
    return (
        f"VP R&D here. {seen} "
        f"Understood briefing: “{text}”. "
        "I will package this as a DevOps delivery task with screen evidence, assign an owner, "
        "and post it to #devops. Click Deliver to DevOps when you want me to send it — or say deliver now."
    )


async def studio_broadcast(session_id: str, payload: Dict[str, Any]) -> None:
    dead: List[WebSocket] = []
    for ws in list(studio_rooms.get(session_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        studio_rooms.get(session_id, set()).discard(ws)


@app.get("/api/studio/sessions")
def list_studio_sessions() -> Dict[str, Any]:
    return {"sessions": P().studio.list()}


@app.post("/api/studio/sessions")
async def create_studio_session(body: CreateStudioRequest) -> Dict[str, Any]:
    session = P().studio.create(title=body.title, host_id=CEO_ID, vp_id=VP_RD_ID)
    intro = (
        "VP R&D joined. You are Me (CEO). Share your screen, explain the DevOps task, "
        "and I will deliver it to the DevOps team with evidence."
    )
    P().studio.add_message(
        session["id"],
        {"kind": "agent", "sender_id": VP_RD_ID, "sender_name": "VP R&D (You)", "text": intro},
    )
    P().audit.append("studio_created", VP_RD_ID, {"session_id": session["id"]})
    return {"session": P().studio.get(session["id"])}


@app.get("/api/studio/sessions/{session_id}")
def get_studio_session(session_id: str) -> Dict[str, Any]:
    session = P().studio.get(session_id)
    if not session:
        raise HTTPException(404, "Studio session not found")
    return {"session": session}


@app.post("/api/studio/sessions/{session_id}/share")
async def studio_share(session_id: str, body: StudioShareRequest) -> Dict[str, Any]:
    if not P().studio.get(session_id):
        raise HTTPException(404, "Studio session not found")
    session = P().studio.set_sharing(session_id, body.active)
    note = (
        "Screen share is live — I am watching your screen now. Explain the DevOps task."
        if body.active
        else "Screen share stopped."
    )
    msg = P().studio.add_message(
        session_id,
        {"kind": "agent", "sender_id": VP_RD_ID, "sender_name": "VP R&D (You)", "text": note},
    )
    payload = {"type": "studio_event", "event": "share", "active": body.active, "message": msg, "session": P().studio.get(session_id)}
    await studio_broadcast(session_id, payload)
    return payload


@app.post("/api/studio/sessions/{session_id}/frames")
async def studio_frame(session_id: str, body: StudioFrameRequest) -> Dict[str, Any]:
    if not P().studio.get(session_id):
        raise HTTPException(404, "Studio session not found")
    if not body.data_url or len(body.data_url) < 32:
        raise HTTPException(400, "data_url required")
    # limit very large payloads (~8MB chars)
    if len(body.data_url) > 12_000_000:
        raise HTTPException(400, "frame too large")
    frame = P().studio.add_frame(session_id, body.data_url, note=body.note)
    P().audit.append("studio_frame", CEO_ID, {"session_id": session_id, "frame_id": frame["id"], "bytes": frame["bytes"]})
    payload = {"type": "studio_event", "event": "frame", "frame": frame, "session": P().studio.get(session_id)}
    await studio_broadcast(session_id, payload)
    return {"frame": frame}


@app.get("/api/studio/frames/{session_id}/{filename}")
def studio_frame_file(session_id: str, filename: str) -> FileResponse:
    path = P().studio.frame_file(session_id, filename)
    if not path or not path.exists():
        # try composed name session_id_filename if filename is uuid.ext
        alt = P().studio.data_dir / "studio_frames" / f"{session_id}_{filename}"
        path = alt if alt.exists() else None
    if not path:
        raise HTTPException(404, "frame not found")
    media = "image/jpeg" if str(path).endswith((".jpg", ".jpeg")) else "image/png"
    return FileResponse(path, media_type=media)


@app.post("/api/studio/sessions/{session_id}/messages")
async def studio_chat(session_id: str, body: StudioChatRequest) -> Dict[str, Any]:
    session = P().studio.get(session_id)
    if not session:
        raise HTTPException(404, "Studio session not found")
    human = P().studio.add_message(
        session_id,
        {
            "kind": "human",
            "sender_id": body.sender_id,
            "sender_name": body.sender_name,
            "text": body.text,
        },
    )
    session = P().studio.get(session_id)
    vp_text = _vp_studio_reply(
        body.text,
        bool(session.get("screen_sharing")),
        len(session.get("frames") or []),
    )
    # Auto-deliver if user says so
    auto_deliver = any(k in body.text.lower() for k in ["deliver now", "send to devops", "assign devops", "deliver to devops"])
    vp = P().studio.add_message(
        session_id,
        {"kind": "agent", "sender_id": VP_RD_ID, "sender_name": "VP R&D (You)", "text": vp_text},
    )
    delivery = None
    if auto_deliver:
        delivery = await _deliver_studio_task(session_id, body.text, "devops-1", None, "P1")
    payload = {
        "type": "studio_chat",
        "human": human,
        "vp": vp,
        "delivery": delivery,
        "session": P().studio.get(session_id),
    }
    await studio_broadcast(session_id, payload)
    return payload


async def _deliver_studio_task(
    session_id: str,
    briefing: str,
    owner: str,
    title: Optional[str],
    priority: str,
) -> Dict[str, Any]:
    session = P().studio.get(session_id)
    if not session:
        raise HTTPException(404, "Studio session not found")
    P().studio.set_briefing(session_id, {"text": briefing, "by": CEO_ID})
    task_title = title or f"DevOps from studio: {briefing[:80]}"
    frames = session.get("frames") or []
    latest = frames[-1] if frames else None
    task = P().tasks.create(
        {
            "title": task_title,
            "description": briefing,
            "business_objective": "Deliver CEO-briefed DevOps work from VP Delivery Studio",
            "acceptance_criteria": [
                "Acknowledge in #devops",
                "Attach execution evidence",
                "Confirm public verification when deploy-related",
            ],
            "created_by": VP_RD_ID,
            "priority": priority,
            "target_environment": "production",
        }
    )
    team_leader = "devops-tl" if owner.startswith("devops-") and owner != "pm-devops" else "pm-devops"
    task = P().tasks.assign(task["id"], owner, team_leader, VP_RD_ID)
    if latest:
        task = P().tasks.add_evidence(
            task["id"],
            {
                "type": "screen_share_frame",
                "frame_id": latest["id"],
                "url": latest["path"],
                "source": "vp_delivery_studio",
                "session_id": session_id,
            },
            VP_RD_ID,
        )
    slack = P().messages.post(
        "devops",
        VP_RD_ID,
        ROSTER[VP_RD_ID].name,
        f"VP DELIVERY from studio session {session_id}: task {task['id']} for <@{owner}>. Briefing: {briefing}",
        mentions=[owner, "devops-tl", "pm-devops", CEO_ID],
        priority="high",
        attachments=[{"task_id": task["id"], "frame": latest["path"] if latest else None}],
    )
    delivery = {
        "task_id": task["id"],
        "owner": owner,
        "slack_message_id": slack["id"],
        "frame": latest,
        "briefing": briefing,
    }
    P().studio.set_delivery(session_id, delivery)
    P().studio.add_message(
        session_id,
        {
            "kind": "agent",
            "sender_id": VP_RD_ID,
            "sender_name": "VP R&D (You)",
            "text": (
                f"Delivered to DevOps. Task {task['id']} assigned to {ROSTER[owner].name}. "
                f"Posted in #devops"
                + (f" with screen evidence {latest['path']}." if latest else ".")
            ),
        },
    )
    P().audit.append("studio_delivery", VP_RD_ID, delivery)
    return {"delivery": delivery, "task": P().tasks.get(task["id"]), "session": P().studio.get(session_id)}


@app.post("/api/studio/sessions/{session_id}/deliver")
async def studio_deliver(session_id: str, body: StudioDeliverRequest) -> Dict[str, Any]:
    if body.owner not in ROSTER:
        raise HTTPException(400, "unknown owner")
    result = await _deliver_studio_task(session_id, body.briefing, body.owner, body.title, body.priority)
    await studio_broadcast(session_id, {"type": "studio_delivery", **result})
    return result


@app.websocket("/ws/studio/{session_id}")
async def studio_ws(websocket: WebSocket, session_id: str) -> None:
    session = P().studio.get(session_id)
    if not session:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    studio_rooms.setdefault(session_id, set()).add(websocket)
    await websocket.send_json({"type": "snapshot", "session": session, "roster": public_roster(), "company": COMPANY})
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "chat":
                await studio_chat(
                    session_id,
                    StudioChatRequest(
                        text=data.get("text", ""),
                        sender_id=data.get("sender_id", CEO_ID),
                        sender_name=data.get("sender_name", "Me (Chanan Zevin)"),
                    ),
                )
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        studio_rooms.get(session_id, set()).discard(websocket)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/meeting-simulation.html")
@app.get("/meeting-simulation")
def meeting_simulation_page() -> FileResponse:
    """Local App Launch Center target for One on One Meeting (port 3000)."""
    return FileResponse(STATIC_DIR / "meeting-simulation.html")


@app.get("/meeting/{meeting_id}")
def meeting_page(meeting_id: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "meeting.html")


@app.get("/dashboard")
def dashboard_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/slack")
def slack_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "slack.html")


@app.get("/studio")
def studio_home() -> FileResponse:
    return FileResponse(STATIC_DIR / "studio.html")


@app.get("/studio/{session_id}")
def studio_session_page(session_id: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "studio.html")


class PublishRequest(BaseModel):
    site_url: str
    domain: str
    verification_txt: Optional[str] = None
    include_www: bool = True
    apex_forward: bool = True
    dry_run: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class PublishCredsRequest(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


@app.get("/publish")
def publish_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "publish.html")


@app.get("/api/publish/jobs")
def list_publish_jobs() -> Dict[str, Any]:
    return {"jobs": P().publish_jobs.list()}


@app.get("/api/publish/jobs/{job_id}")
def get_publish_job(job_id: str) -> Dict[str, Any]:
    job = P().publish_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Publish job not found")
    return {"job": job}


@app.post("/api/publish/credentials")
def publish_credentials_check(body: PublishCredsRequest) -> Dict[str, Any]:
    return credentials_status(api_key=body.api_key, api_secret=body.api_secret)


@app.post("/api/publish/plan")
def publish_plan(body: PublishRequest) -> Dict[str, Any]:
    try:
        plan = build_publish_plan(
            body.site_url,
            body.domain,
            include_www=body.include_www,
            apex_forward=body.apex_forward,
            verification_txt=body.verification_txt,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"plan": plan, "status": "planned"}


@app.post("/api/publish")
def publish_domain(body: PublishRequest) -> Dict[str, Any]:
    try:
        result = run_publish(
            body.site_url,
            body.domain,
            api_key=body.api_key,
            api_secret=body.api_secret,
            dry_run=body.dry_run,
            include_www=body.include_www,
            apex_forward=body.apex_forward,
            verification_txt=body.verification_txt,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except GoDaddyError as exc:
        raise HTTPException(502, f"{exc}" + (f" — {exc.body}" if exc.body else "")) from exc

    plan = result["plan"]
    job = P().publish_jobs.create(
        {
            "domain": plan["domain"],
            "studio_host": plan["studio"]["host"],
            "studio_url": plan["studio"]["canonical_url"],
            "site_url": body.site_url,
            "dry_run": body.dry_run,
            "status": result["status"],
            "credentials_configured": result["credentials_configured"],
            "plan": plan,
            "application": result["application"],
            # never persist secrets
        }
    )
    P().audit.append(
        "domain_publish",
        VP_RD_ID,
        {
            "job_id": job["id"],
            "domain": plan["domain"],
            "studio_host": plan["studio"]["host"],
            "dry_run": body.dry_run,
            "status": result["status"],
        },
    )
    # Notify devops channel on live publish
    if not body.dry_run:
        P().messages.post(
            "devops",
            VP_RD_ID,
            ROSTER[VP_RD_ID].name,
            (
                f"Domain publish {result['status']}: {plan['domain']} → {plan['studio']['host']} "
                f"(job {job['id']}). Public: {plan['public_urls']['www']}"
            ),
            mentions=["devops-tl", "pm-devops", CEO_ID],
            priority="high",
            attachments=[{"job_id": job["id"], "domain": plan["domain"]}],
        )
    return {**result, "job": job}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

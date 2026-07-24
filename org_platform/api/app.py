"""FastAPI application — enterprise org + real-time meeting room."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from org_platform.agents.engine import generate_live_responses
from org_platform.agents.roster import ROSTER, SUPER_ADMIN_ID, public_roster
from org_platform.store import meetings as meeting_store

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Insightful Data Technologies — Enterprise Agent Org",
    version="1.0.0",
    description="Multi-agent organization with VP R&D Super Admin and real-time meeting room.",
)

rooms: Dict[str, Set[WebSocket]] = {}


class CreateMeetingRequest(BaseModel):
    title: str = Field(default="Executive Delivery Sync")
    chair_id: str = Field(default=SUPER_ADMIN_ID)
    participant_ids: Optional[List[str]] = None
    seed_intro: bool = True


class ChatRequest(BaseModel):
    text: str
    sender_name: str = "Human Operator"
    sender_id: str = "human-operator"


class EscalateRequest(BaseModel):
    from_agent_id: str = SUPER_ADMIN_ID
    reason: str = "Operator-requested escalation"


def _store():
    return meeting_store.STORE


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "org-platform",
        "super_admin": SUPER_ADMIN_ID,
        "ceo": "ceo-chanan",
        "agents": len(ROSTER),
        "store": _store().backend_info(),
        "project_target": os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0386540117"),
    }


@app.get("/api/org")
def org() -> Dict[str, Any]:
    return {
        "company": "Insightful Data Technologies",
        "ceo": "Chanan Zevin",
        "super_admin": "VP R&D (Super Admin)",
        "approval_policy": "VP R&D Super Admin may approve all team actions; CEO for strategic/final escalation.",
        "roster": public_roster(),
    }


@app.get("/api/meetings")
def list_meetings() -> Dict[str, Any]:
    return {"meetings": _store().list_meetings()}


@app.post("/api/meetings")
async def create_meeting(body: CreateMeetingRequest) -> Dict[str, Any]:
    if body.chair_id not in ROSTER:
        raise HTTPException(400, f"Unknown chair_id {body.chair_id}")
    participants = body.participant_ids or list(ROSTER.keys())
    for pid in participants:
        if pid not in ROSTER:
            raise HTTPException(400, f"Unknown participant {pid}")
    meeting = _store().create_meeting(
        title=body.title,
        chair_id=body.chair_id,
        participant_ids=participants,
        created_by="human-operator",
    )
    if body.seed_intro:
        replies, events = generate_live_responses(
            message="Open the meeting and confirm all teams are present.",
            meeting_title=meeting["title"],
            chair_id=meeting["chair_id"],
        )
        _store().append_message(
            meeting["id"],
            {
                "kind": "human",
                "sender_id": "human-operator",
                "sender_name": "Human Operator",
                "text": "Open the meeting and confirm all teams are present.",
            },
        )
        for r in replies:
            _store().append_message(
                meeting["id"],
                {
                    "kind": "agent",
                    "sender_id": r["agent_id"],
                    "sender_name": r["agent_name"],
                    "text": r["text"],
                    "meta": r,
                },
            )
        _store().append_events(meeting["id"], events)
        meeting = _store().get(meeting["id"])
    return {"meeting": meeting}


@app.get("/api/meetings/{meeting_id}")
def get_meeting(meeting_id: str) -> Dict[str, Any]:
    meeting = _store().get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return {"meeting": meeting}


@app.post("/api/meetings/{meeting_id}/messages")
async def post_message(meeting_id: str, body: ChatRequest) -> Dict[str, Any]:
    meeting = _store().get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.get("status") != "live":
        raise HTTPException(400, "Meeting is not live")

    human = _store().append_message(
        meeting_id,
        {
            "kind": "human",
            "sender_id": body.sender_id,
            "sender_name": body.sender_name,
            "text": body.text,
        },
    )
    replies, events = generate_live_responses(
        message=body.text,
        meeting_title=meeting["title"],
        chair_id=meeting["chair_id"],
    )
    agent_msgs = []
    for r in replies:
        agent_msgs.append(
            _store().append_message(
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
    _store().append_events(meeting_id, events)
    payload = {
        "human": human,
        "replies": agent_msgs,
        "events": events,
        "meeting": _store().get(meeting_id),
    }
    await broadcast(meeting_id, {"type": "chat_burst", **payload})
    return payload


@app.post("/api/meetings/{meeting_id}/escalate")
async def escalate(meeting_id: str, body: EscalateRequest) -> Dict[str, Any]:
    meeting = _store().get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    text = f"ESCALATE TO CEO: {body.reason}"
    return await post_message(
        meeting_id,
        ChatRequest(text=text, sender_name="VP R&D Super Admin", sender_id=body.from_agent_id),
    )


@app.post("/api/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str) -> Dict[str, Any]:
    meeting = _store().get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    ended = _store().end_meeting(meeting_id)
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
    meeting = _store().get(meeting_id)
    if not meeting:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    rooms.setdefault(meeting_id, set()).add(websocket)
    await websocket.send_json({"type": "snapshot", "meeting": meeting, "roster": public_roster()})
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
                await escalate(
                    meeting_id,
                    EscalateRequest(reason=data.get("reason", "Operator escalation")),
                )
    except WebSocketDisconnect:
        pass
    finally:
        rooms.get(meeting_id, set()).discard(websocket)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/meeting/{meeting_id}")
def meeting_page(meeting_id: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "meeting.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

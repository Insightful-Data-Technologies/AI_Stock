"""SRS organizational roster — Insightful Data Technologies – 2.o AI."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


COMPANY = {
    "legal_name": "Insightful Data Technologies – 2.o AI",
    "short_name": "Insightful Data Technologies",
    "ceo": "Chanan Zevin",
    "tagline": "AI Risk Management | Hedging | Exposure | Predictive Strategy",
    "project": "AI Capital Enterprise Team",
    "platform": "Google Cloud Enterprise / Vertex AI Agent Platform",
    "gcp_project": "gen-lang-client-0386540117",
}


class Team(str, Enum):
    EXECUTIVE = "executive"
    PMO = "pmo"
    DEVELOPMENT = "development"
    QA = "qa"
    DEVOPS = "devops"
    IT = "it"


class Role(str, Enum):
    CEO = "ceo"
    EXECUTIVE_ASSISTANT = "executive_assistant"
    VP_RD = "vp_rd"
    MAIN_PM = "main_pm"
    DEV_PM = "dev_pm"
    DEVOPS_PM = "devops_pm"
    DEV_TL = "dev_tl"
    DEVELOPER = "developer"
    QA_TL = "qa_tl"
    QA_AGENT = "qa_agent"
    DEVOPS_TL = "devops_tl"
    DEVOPS_AGENT = "devops_agent"
    IT_TL = "it_tl"
    IT_AGENT = "it_agent"


@dataclass(frozen=True)
class OrgAgent:
    id: str
    name: str
    title: str
    role: Role
    team: Team
    reports_to: Optional[str]
    can_approve: bool
    voice_persona: str
    color: str
    avatar_initials: str
    email: str
    specialties: List[str] = field(default_factory=list)
    system_prompt: str = ""
    is_human_ceo: bool = False
    photo: str = ""
    voice_gender: str = "male"
    join_seat: str = ""


ESCALATION_CHAIN: Dict[str, Optional[str]] = {}


def _a(**kwargs) -> OrgAgent:
    return OrgAgent(**kwargs)


def _build() -> Dict[str, OrgAgent]:
    agents = [
        _a(
            id="ceo-chanan",
            name="Chanan Zevin",
            title="Chief Executive Officer",
            role=Role.CEO,
            team=Team.EXECUTIVE,
            reports_to=None,
            can_approve=True,
            voice_persona="confident executive",
            color="#C4A35A",
            avatar_initials="CZ",
            email="chanan.zevin@insightfuldata.ai",
            specialties=["strategy", "capital", "executive approval", "escalations"],
            system_prompt="You are Chanan Zevin, CEO. Strategy and high-impact approvals only.",
            is_human_ceo=True,
            photo="/static/assets/portraits/ceo-chanan.png",
            voice_gender="male",
            join_seat="me",
        ),
        _a(
            id="ea-sofia",
            name="Sofia Marchetti",
            title="Executive Assistant to the CEO",
            role=Role.EXECUTIVE_ASSISTANT,
            team=Team.EXECUTIVE,
            reports_to="ceo-chanan",
            can_approve=False,
            voice_persona="warm polished professional woman",
            color="#B08D57",
            avatar_initials="SM",
            email="sofia.marchetti@insightfuldata.ai",
            specialties=["CEO agenda", "executive summaries", "decision tracking", "escalation filter"],
            system_prompt=(
                "You are Sofia Marchetti, Executive Assistant to CEO Chanan Zevin, alongside VP R&D. "
                "Prepare polished executive summaries and protect the CEO from routine noise."
            ),
            photo="/static/assets/portraits/ea-sofia.png",
            voice_gender="female",
        ),
        _a(
            id="vp-rd",
            name="VP R&D (You)",
            title="VP Research & Development — Super Admin",
            role=Role.VP_RD,
            team=Team.EXECUTIVE,
            reports_to="ceo-chanan",
            can_approve=True,
            voice_persona="decisive technical executive",
            color="#3D7EA6",
            avatar_initials="VP",
            email="vp.rd@insightfuldata.ai",
            specialties=["engineering leadership", "cross-team resolution", "evidence gate"],
            system_prompt="You are VP R&D Super Admin. Lead Dev/QA/DevOps/IT and escalate only genuine CEO decisions.",
            photo="/static/assets/portraits/vp-rd.png",
            voice_gender="male",
            join_seat="you",
        ),
        _a(
            id="pm-main",
            name="Alex Rivera",
            title="Main Project Manager",
            role=Role.MAIN_PM,
            team=Team.PMO,
            reports_to="vp-rd",
            can_approve=True,
            voice_persona="structured program lead",
            color="#6B8F71",
            avatar_initials="AR",
            email="pm.main@insightfuldata.ai",
            specialties=["master plan", "dependencies", "daily meetings"],
            system_prompt="You are Main PM. Coordinate departments and daily meetings.",
            photo="/static/assets/portraits/pm-main.png",
            voice_gender="female",
        ),
        _a(
            id="pm-dev-claude",
            name="Claude",
            title="Development Project Manager",
            role=Role.DEV_PM,
            team=Team.PMO,
            reports_to="pm-main",
            can_approve=True,
            voice_persona="hands-on development PM",
            color="#7C6BB0",
            avatar_initials="CL",
            email="claude.dpm@insightfuldata.ai",
            specialties=["requirements", "architecture review", "QA handoff"],
            system_prompt="You are Claude, Development PM. Hands-on delivery ownership.",
            photo="/static/assets/portraits/pm-claude.png",
            voice_gender="male",
        ),
        _a(
            id="pm-devops",
            name="Morgan Blake",
            title="DevOps Project Manager",
            role=Role.DEVOPS_PM,
            team=Team.PMO,
            reports_to="pm-main",
            can_approve=True,
            voice_persona="release operations lead",
            color="#2F6F6A",
            avatar_initials="MB",
            email="pm.devops@insightfuldata.ai",
            specialties=["deployments", "SSL/domains", "rollback"],
            system_prompt="You are DevOps PM. Require public deployment evidence.",
            photo="/static/assets/portraits/pm-devops.png",
            voice_gender="female",
        ),
        _a(
            id="dev-tl-cursor",
            name="Cursor",
            title="Development Team Leader",
            role=Role.DEV_TL,
            team=Team.DEVELOPMENT,
            reports_to="pm-dev-claude",
            can_approve=True,
            voice_persona="hands-on engineering lead",
            color="#4A6FA5",
            avatar_initials="CU",
            email="cursor.devtl@insightfuldata.ai",
            specialties=["codebase", "reviews", "build/test gate"],
            system_prompt="You are Cursor, Dev Team Leader managing three Ultra developers.",
            photo="/static/assets/portraits/dev-cursor.png",
            voice_gender="male",
        ),
        _a(
            id="dev-ultra-1",
            name="Nova Ultra",
            title="Development Agent — Ultra 1",
            role=Role.DEVELOPER,
            team=Team.DEVELOPMENT,
            reports_to="dev-tl-cursor",
            can_approve=False,
            voice_persona="focused fullstack engineer",
            color="#5B7DB1",
            avatar_initials="U1",
            email="dev.ultra1@insightfuldata.ai",
            specialties=["frontend", "API", "tests"],
            system_prompt="Ultra developer 1.",
            photo="/static/assets/portraits/dev-ultra1.png",
            voice_gender="female",
        ),
        _a(
            id="dev-ultra-2",
            name="Orion Ultra",
            title="Development Agent — Ultra 2",
            role=Role.DEVELOPER,
            team=Team.DEVELOPMENT,
            reports_to="dev-tl-cursor",
            can_approve=False,
            voice_persona="backend systems engineer",
            color="#6C8BC0",
            avatar_initials="U2",
            email="dev.ultra2@insightfuldata.ai",
            specialties=["backend", "data", "integrations"],
            system_prompt="Ultra developer 2.",
            photo="/static/assets/portraits/dev-ultra2.png",
            voice_gender="male",
        ),
        _a(
            id="dev-ultra-3",
            name="Sage Ultra",
            title="Development Agent — Ultra 3",
            role=Role.DEVELOPER,
            team=Team.DEVELOPMENT,
            reports_to="dev-tl-cursor",
            can_approve=False,
            voice_persona="integration engineer",
            color="#7A98CF",
            avatar_initials="U3",
            email="dev.ultra3@insightfuldata.ai",
            specialties=["realtime", "WebRTC", "tests"],
            system_prompt="Ultra developer 3.",
            photo="/static/assets/portraits/dev-ultra3.png",
            voice_gender="female",
        ),
        _a(
            id="qa-tl",
            name="Sam Ortiz",
            title="QA Team Leader",
            role=Role.QA_TL,
            team=Team.QA,
            reports_to="pm-main",
            can_approve=True,
            voice_persona="independent quality gate",
            color="#A67C52",
            avatar_initials="SO",
            email="qa.lead@insightfuldata.ai",
            specialties=["PASS/FAIL/BLOCKED", "release gate"],
            system_prompt="QA Team Leader. Independent verification only.",
            photo="/static/assets/portraits/qa-tl.png",
            voice_gender="female",
        ),
        _a(
            id="qa-1",
            name="Tess Okonkwo",
            title="QA Agent 1 — Functional/UI",
            role=Role.QA_AGENT,
            team=Team.QA,
            reports_to="qa-tl",
            can_approve=False,
            voice_persona="functional tester",
            color="#B8906A",
            avatar_initials="Q1",
            email="qa1@insightfuldata.ai",
            specialties=["functional", "UI", "mobile/desktop"],
            system_prompt="QA Agent 1.",
            photo="/static/assets/portraits/qa-1.png",
            voice_gender="female",
        ),
        _a(
            id="qa-2",
            name="Priya Nair",
            title="QA Agent 2 — API/Integration",
            role=Role.QA_AGENT,
            team=Team.QA,
            reports_to="qa-tl",
            can_approve=False,
            voice_persona="api integration tester",
            color="#C4A07A",
            avatar_initials="Q2",
            email="qa2@insightfuldata.ai",
            specialties=["API", "integration", "regression"],
            system_prompt="QA Agent 2.",
            photo="/static/assets/portraits/qa-2.png",
            voice_gender="female",
        ),
        _a(
            id="qa-3",
            name="Evan Cole",
            title="QA Agent 3 — Security/Production",
            role=Role.QA_AGENT,
            team=Team.QA,
            reports_to="qa-tl",
            can_approve=False,
            voice_persona="security and smoke tester",
            color="#D0B08A",
            avatar_initials="Q3",
            email="qa3@insightfuldata.ai",
            specialties=["security", "DNS/SSL", "prod smoke"],
            system_prompt="QA Agent 3.",
            photo="/static/assets/portraits/qa-3.png",
            voice_gender="male",
        ),
        _a(
            id="devops-tl",
            name="Kai Nakamura",
            title="DevOps Team Leader",
            role=Role.DEVOPS_TL,
            team=Team.DEVOPS,
            reports_to="pm-devops",
            can_approve=True,
            voice_persona="reliability lead",
            color="#2F6F6A",
            avatar_initials="KN",
            email="devops.lead@insightfuldata.ai",
            specialties=["deploy", "rollback", "health"],
            system_prompt="DevOps Team Leader.",
            photo="/static/assets/portraits/devops-tl.png",
            voice_gender="male",
        ),
        _a(
            id="devops-1",
            name="Lee Vargas",
            title="DevOps Agent 1 — Cloud Run/CI",
            role=Role.DEVOPS_AGENT,
            team=Team.DEVOPS,
            reports_to="devops-tl",
            can_approve=False,
            voice_persona="cloud run operator",
            color="#3A8580",
            avatar_initials="D1",
            email="devops1@insightfuldata.ai",
            specialties=["Cloud Run", "CI/CD"],
            system_prompt="DevOps Agent 1.",
            photo="/static/assets/portraits/devops-1.png",
            voice_gender="male",
        ),
        _a(
            id="devops-2",
            name="Riley Cho",
            title="DevOps Agent 2 — Domains/TLS",
            role=Role.DEVOPS_AGENT,
            team=Team.DEVOPS,
            reports_to="devops-tl",
            can_approve=False,
            voice_persona="edge networking specialist",
            color="#459A94",
            avatar_initials="D2",
            email="devops2@insightfuldata.ai",
            specialties=["domains", "DNS", "HTTPS"],
            system_prompt="DevOps Agent 2.",
            photo="/static/assets/portraits/devops-2.png",
            voice_gender="female",
        ),
        _a(
            id="devops-3",
            name="Casey Brooks",
            title="DevOps Agent 3 — Observability",
            role=Role.DEVOPS_AGENT,
            team=Team.DEVOPS,
            reports_to="devops-tl",
            can_approve=False,
            voice_persona="observability engineer",
            color="#50AFA8",
            avatar_initials="D3",
            email="devops3@insightfuldata.ai",
            specialties=["logs", "alerts", "dashboards"],
            system_prompt="DevOps Agent 3.",
            photo="/static/assets/portraits/devops-3.png",
            voice_gender="male",
        ),
        _a(
            id="it-tl",
            name="Ava Moretti",
            title="IT Team Leader",
            role=Role.IT_TL,
            team=Team.IT,
            reports_to="pm-main",
            can_approve=True,
            voice_persona="identity and access lead",
            color="#7A5C8A",
            avatar_initials="AM",
            email="it.lead@insightfuldata.ai",
            specialties=["identities", "groups", "comm access"],
            system_prompt="IT Team Leader.",
            photo="/static/assets/portraits/it-tl.png",
            voice_gender="female",
        ),
        _a(
            id="it-1",
            name="Ben Haas",
            title="IT Agent 1 — Identity/Email",
            role=Role.IT_AGENT,
            team=Team.IT,
            reports_to="it-tl",
            can_approve=False,
            voice_persona="identity specialist",
            color="#8E6F9C",
            avatar_initials="I1",
            email="it1@insightfuldata.ai",
            specialties=["identities", "email"],
            system_prompt="IT Agent 1.",
            photo="/static/assets/portraits/it-1.png",
            voice_gender="male",
        ),
        _a(
            id="it-2",
            name="Dana Weiss",
            title="IT Agent 2 — Slack/Meeting Room",
            role=Role.IT_AGENT,
            team=Team.IT,
            reports_to="it-tl",
            can_approve=False,
            voice_persona="collaboration systems specialist",
            color="#A182B0",
            avatar_initials="I2",
            email="it2@insightfuldata.ai",
            specialties=["Slack", "meeting room", "voice tests"],
            system_prompt="IT Agent 2.",
            photo="/static/assets/portraits/it-2.png",
            voice_gender="female",
        ),
    ]
    for a in agents:
        ESCALATION_CHAIN[a.id] = a.reports_to
    return {a.id: a for a in agents}


ROSTER: Dict[str, OrgAgent] = _build()
CEO_ID = "ceo-chanan"
EA_ID = "ea-sofia"
VP_RD_ID = "vp-rd"
MAIN_PM_ID = "pm-main"
DEV_PM_ID = "pm-dev-claude"
DEV_TL_ID = "dev-tl-cursor"


def escalate_from(agent_id: str) -> Optional[OrgAgent]:
    nxt = ESCALATION_CHAIN.get(agent_id)
    return ROSTER.get(nxt) if nxt else None


def escalation_path(agent_id: str) -> List[str]:
    path = [agent_id]
    cur = agent_id
    while ESCALATION_CHAIN.get(cur):
        cur = ESCALATION_CHAIN[cur]
        path.append(cur)
    return path


def public_roster() -> List[dict]:
    return [
        {
            "id": a.id,
            "name": a.name,
            "title": a.title,
            "role": a.role.value,
            "team": a.team.value,
            "reports_to": a.reports_to,
            "can_approve": a.can_approve,
            "color": a.color,
            "avatar_initials": a.avatar_initials,
            "email": a.email,
            "specialties": a.specialties,
            "photo": a.photo,
            "voice_gender": a.voice_gender,
            "join_seat": a.join_seat,
            "is_ceo": a.id == CEO_ID,
            "is_vp_rd": a.id == VP_RD_ID,
            "is_ea": a.id == EA_ID,
        }
        for a in ROSTER.values()
    ]


def hierarchy_edges() -> List[dict]:
    return [
        {"from": a.reports_to, "to": a.id}
        for a in ROSTER.values()
        if a.reports_to
    ] + [{"from": "ceo-chanan", "to": "ea-sofia", "relation": "alongside"}]

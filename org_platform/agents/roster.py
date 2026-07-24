"""Enterprise multi-agent organization roster and escalation graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Team(str, Enum):
    EXECUTIVE = "executive"
    PMO = "pmo"
    ENGINEERING = "engineering"
    QA = "qa"
    DEVOPS = "devops"
    IT = "it"


class Role(str, Enum):
    CEO = "ceo"
    VP_RD = "vp_rd"
    PROJECT_MANAGER = "project_manager"
    DEV_LEAD = "dev_lead"
    DEVELOPER = "developer"
    QA_LEAD = "qa_lead"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_LEAD = "devops_lead"
    DEVOPS_ENGINEER = "devops_engineer"
    IT_LEAD = "it_lead"
    IT_SPECIALIST = "it_specialist"


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
    specialties: List[str] = field(default_factory=list)
    system_prompt: str = ""


# Escalation: agent_id -> next approver agent_id (toward CEO)
ESCALATION_CHAIN: Dict[str, Optional[str]] = {}


def _build_roster() -> Dict[str, OrgAgent]:
    agents = [
        OrgAgent(
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
            specialties=["strategy", "capital", "final approval", "escalation"],
            system_prompt=(
                "You are Chanan Zevin, CEO of Insightful Data Technologies. "
                "Speak with executive clarity. Approve or redirect strategic decisions. "
                "Escalate only when legal/compliance risk requires external counsel."
            ),
        ),
        OrgAgent(
            id="vp-rd-super",
            name="VP R&D (Super Admin)",
            title="VP Research & Development — Super Admin",
            role=Role.VP_RD,
            team=Team.EXECUTIVE,
            reports_to="ceo-chanan",
            can_approve=True,
            voice_persona="decisive technical executive",
            color="#3D7EA6",
            avatar_initials="VR",
            specialties=[
                "architecture",
                "all approvals",
                "platform",
                "agent orchestration",
                "meeting control",
            ],
            system_prompt=(
                "You are VP R&D Super Admin. You have blanket approval authority across Dev, QA, "
                "DevOps, IT, and PMO. Chair meetings, unblock teams, and escalate to CEO Chanan Zevin "
                "only for company-level strategy or irreversible risk."
            ),
        ),
        OrgAgent(
            id="pm-nova",
            name="Nova Hale",
            title="Senior Project Manager",
            role=Role.PROJECT_MANAGER,
            team=Team.PMO,
            reports_to="vp-rd-super",
            can_approve=True,
            voice_persona="organized facilitator",
            color="#6B8F71",
            avatar_initials="NH",
            specialties=["roadmap", "dependencies", "status", "stakeholder sync"],
            system_prompt=(
                "You are Nova Hale, Senior PM. Keep scope, owners, and dates crisp. "
                "Escalate blockers to VP R&D Super Admin."
            ),
        ),
        OrgAgent(
            id="pm-eli",
            name="Eli Sark",
            title="Project Manager — Delivery",
            role=Role.PROJECT_MANAGER,
            team=Team.PMO,
            reports_to="vp-rd-super",
            can_approve=False,
            voice_persona="calm delivery lead",
            color="#5C7A6E",
            avatar_initials="ES",
            specialties=["sprints", "risk register", "cross-team coordination"],
            system_prompt=(
                "You are Eli Sark, Delivery PM. Track execution risks and coordinate Dev/QA/DevOps."
            ),
        ),
        OrgAgent(
            id="dev-lead-mira",
            name="Mira Chen",
            title="Engineering Lead",
            role=Role.DEV_LEAD,
            team=Team.ENGINEERING,
            reports_to="vp-rd-super",
            can_approve=True,
            voice_persona="pragmatic engineer",
            color="#4A6FA5",
            avatar_initials="MC",
            specialties=["backend", "APIs", "code review", "technical design"],
            system_prompt=(
                "You are Mira Chen, Engineering Lead. Propose concrete implementation plans and owners."
            ),
        ),
        OrgAgent(
            id="dev-jordan",
            name="Jordan Blake",
            title="Senior Developer",
            role=Role.DEVELOPER,
            team=Team.ENGINEERING,
            reports_to="dev-lead-mira",
            can_approve=False,
            voice_persona="focused builder",
            color="#5B7DB1",
            avatar_initials="JB",
            specialties=["fullstack", "websockets", "integrations"],
            system_prompt="You are Jordan Blake, Senior Developer. Provide implementation detail and estimates.",
        ),
        OrgAgent(
            id="dev-rina",
            name="Rina Adler",
            title="Developer",
            role=Role.DEVELOPER,
            team=Team.ENGINEERING,
            reports_to="dev-lead-mira",
            can_approve=False,
            voice_persona="curious engineer",
            color="#6C8BC0",
            avatar_initials="RA",
            specialties=["frontend", "UX", "accessibility"],
            system_prompt="You are Rina Adler, Developer. Focus on UI/UX feasibility and frontend delivery.",
        ),
        OrgAgent(
            id="qa-lead-sam",
            name="Sam Ortiz",
            title="QA Lead",
            role=Role.QA_LEAD,
            team=Team.QA,
            reports_to="vp-rd-super",
            can_approve=True,
            voice_persona="skeptical quality advocate",
            color="#A67C52",
            avatar_initials="SO",
            specialties=["test strategy", "release gates", "regression"],
            system_prompt=(
                "You are Sam Ortiz, QA Lead. Demand evidence, define acceptance criteria, block unsafe releases."
            ),
        ),
        OrgAgent(
            id="qa-tess",
            name="Tess Okonkwo",
            title="QA Engineer",
            role=Role.QA_ENGINEER,
            team=Team.QA,
            reports_to="qa-lead-sam",
            can_approve=False,
            voice_persona="detail-oriented tester",
            color="#B8906A",
            avatar_initials="TO",
            specialties=["e2e", "automation", "bug triage"],
            system_prompt="You are Tess Okonkwo, QA Engineer. Translate requirements into test cases.",
        ),
        OrgAgent(
            id="devops-lead-kai",
            name="Kai Nakamura",
            title="DevOps Lead",
            role=Role.DEVOPS_LEAD,
            team=Team.DEVOPS,
            reports_to="vp-rd-super",
            can_approve=True,
            voice_persona="reliability-minded operator",
            color="#2F6F6A",
            avatar_initials="KN",
            specialties=["CI/CD", "Cloud Run", "observability", "rollbacks"],
            system_prompt=(
                "You are Kai Nakamura, DevOps Lead. Own deployability, SLOs, and infrastructure safety."
            ),
        ),
        OrgAgent(
            id="devops-lee",
            name="Lee Vargas",
            title="DevOps Engineer",
            role=Role.DEVOPS_ENGINEER,
            team=Team.DEVOPS,
            reports_to="devops-lead-kai",
            can_approve=False,
            voice_persona="ops specialist",
            color="#3A8580",
            avatar_initials="LV",
            specialties=["containers", "secrets", "networking"],
            system_prompt="You are Lee Vargas, DevOps Engineer. Detail pipelines, secrets, and runtime config.",
        ),
        OrgAgent(
            id="it-lead-ava",
            name="Ava Moretti",
            title="IT Lead",
            role=Role.IT_LEAD,
            team=Team.IT,
            reports_to="vp-rd-super",
            can_approve=True,
            voice_persona="security-aware IT lead",
            color="#7A5C8A",
            avatar_initials="AM",
            specialties=["identity", "devices", "access", "compliance"],
            system_prompt=(
                "You are Ava Moretti, IT Lead. Cover identity, access control, and workplace systems."
            ),
        ),
        OrgAgent(
            id="it-ben",
            name="Ben Haas",
            title="IT Specialist",
            role=Role.IT_SPECIALIST,
            team=Team.IT,
            reports_to="it-lead-ava",
            can_approve=False,
            voice_persona="helpful IT specialist",
            color="#8E6F9C",
            avatar_initials="BH",
            specialties=["accounts", "VPN", "endpoint support"],
            system_prompt="You are Ben Haas, IT Specialist. Resolve access and workstation issues quickly.",
        ),
    ]
    roster = {a.id: a for a in agents}
    for a in agents:
        ESCALATION_CHAIN[a.id] = a.reports_to
    return roster


ROSTER: Dict[str, OrgAgent] = _build_roster()
SUPER_ADMIN_ID = "vp-rd-super"
CEO_ID = "ceo-chanan"


def escalate_from(agent_id: str) -> Optional[OrgAgent]:
    nxt = ESCALATION_CHAIN.get(agent_id)
    return ROSTER.get(nxt) if nxt else None


def next_approver(agent_id: str) -> Optional[OrgAgent]:
    current = ROSTER.get(agent_id)
    while current:
        nxt = escalate_from(current.id)
        if nxt is None:
            return None
        if nxt.can_approve:
            return nxt
        current = nxt
    return None


def team_members(team: Team) -> List[OrgAgent]:
    return [a for a in ROSTER.values() if a.team == team]


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
            "specialties": a.specialties,
            "is_super_admin": a.id == SUPER_ADMIN_ID,
            "is_ceo": a.id == CEO_ID,
        }
        for a in ROSTER.values()
    ]

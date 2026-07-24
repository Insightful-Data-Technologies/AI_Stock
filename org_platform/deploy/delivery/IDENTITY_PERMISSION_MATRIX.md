# Identity & Permission Matrix — AI Capital Enterprise Team

| ID | Name | Role | Reports to | Approve | Channels (primary) | Email |
|----|------|------|------------|---------|--------------------|-------|
| ceo-chanan | Chanan Zevin | CEO | — | Yes (executive) | #executive-management | chanan.zevin@insightfuldata.ai |
| ea-jordan | Jordan Ellis | Executive Assistant | CEO (alongside VP) | No | #executive-management | ea@insightfuldata.ai |
| vp-rd | VP R&D (Codex) | VP R&D | CEO | Yes (ops) | #executive-management, #project-management | vp.rd@insightfuldata.ai |
| pm-main | Alex Rivera | Main PM | VP R&D | Yes | #project-management | pm.main@insightfuldata.ai |
| pm-dev-claude | Claude | Development PM | Main PM | Yes | #development, #project-management | claude.dpm@insightfuldata.ai |
| pm-devops | Morgan Blake | DevOps PM | Main PM | Yes | #devops, #release-approvals | pm.devops@insightfuldata.ai |
| dev-tl-cursor | Cursor | Dev Team Leader | Claude | Yes | #development | cursor.devtl@insightfuldata.ai |
| dev-ultra-1..3 | Nova/Orion/Sage Ultra | Developers | Cursor | No | #development | dev.ultraN@insightfuldata.ai |
| qa-tl | Sam Ortiz | QA Team Leader | Main PM | Yes (PASS/FAIL/BLOCKED) | #qa | qa.lead@insightfuldata.ai |
| qa-1..3 | Tess/Priya/Evan | QA Agents | QA TL | No | #qa | qaN@insightfuldata.ai |
| devops-tl | Kai Nakamura | DevOps TL | DevOps PM | Yes | #devops | devops.lead@insightfuldata.ai |
| devops-1..3 | Lee/Riley/Casey | DevOps Agents | DevOps TL | No | #devops, #production-incidents | devopsN@insightfuldata.ai |
| it-tl | Ava Moretti | IT TL | Main PM | Yes | #it-support | it.lead@insightfuldata.ai |
| it-1..2 | Ben/Dana | IT Agents | IT TL | No | #it-support | itN@insightfuldata.ai |

Escalation path: Worker → Team Leader → Project Manager → VP R&D → CEO  
Urgent security/financial/legal/production may fast-path to CEO with mandatory audit logging.

Email identities are **SIMULATED** until Google Workspace/SMTP secrets are available in Secret Manager.

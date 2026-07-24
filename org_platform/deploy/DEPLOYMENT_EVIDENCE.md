# Deployment Evidence — Enterprise Org + Meeting Room

**Timestamp (UTC):** 2026-07-24T13:41:35Z

## Live URL (Cloudflare quick tunnel → local Cloud Run-ready service)

- **Public base:** https://floor-students-estimated-apache.trycloudflare.com
- **Org home:** https://floor-students-estimated-apache.trycloudflare.com/
- **Sample meeting:** https://floor-students-estimated-apache.trycloudflare.com/meeting/
- **Health:** https://floor-students-estimated-apache.trycloudflare.com/api/health

## Local service

- Host: `0.0.0.0:8080`
- Health: OK — 13 agents, VP R&D Super Admin, CEO Chanan Zevin
- E2E: HTTP + WebSocket passed (see `/opt/cursor/artifacts/e2e_meeting_room_report.txt`)
- Pytest: 6 passed

## GCP Cloud Run (`gen-lang-client-0386540117`)

- Attempted via `org_platform/deploy/deploy_cloud_run.sh`
- **Blocked:** no authenticated gcloud account in this environment
- Script is ready; re-run after `gcloud auth login` or service-account ADC

## Features verified

- Team roster: CEO, VP R&D Super Admin (all approvals), PMs, Dev, QA, DevOps, IT
- Meeting room: visible participants, live multi-agent replies, messaging, history, escalation to CEO
- Voice: browser neural TTS + push-to-talk speech recognition in UI

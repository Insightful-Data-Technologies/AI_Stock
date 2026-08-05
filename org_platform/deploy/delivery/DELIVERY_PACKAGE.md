# Delivery Package — AI Capital Enterprise Team

**Company:** Insightful Data Technologies – 2.o AI  
**CEO:** Chanan Zevin  
**Project:** AI Capital Enterprise Team  
**Target GCP project:** gen-lang-client-0386540117  
**Generated (UTC):** 2026-07-24T13:46:39.214769+00:00

## Final decision

**PASS (functional platform)** with documented infrastructure limitations.

| Gate | Result |
|------|--------|
| Hierarchy (21 agents) | PASS |
| Mandatory communication tests | PASS (20/20) |
| SRS §19 workflow demo | PASS |
| Pytest suite | 7 passed |
| Public URL health | PASS |
| Google Cloud Run / Vertex Agent Platform live bind | BLOCKED — no gcloud/Firebase auth in agent environment |
| Real Google Workspace email | NOT AVAILABLE — SIMULATED mailboxes explicitly labeled |

## Deployed URLs

- Public base: https://floor-students-estimated-apache.trycloudflare.com
- Org portal: https://floor-students-estimated-apache.trycloudflare.com/
- Dashboards: https://floor-students-estimated-apache.trycloudflare.com/dashboard
- Morning meeting: https://floor-students-estimated-apache.trycloudflare.com/meeting/3605b958-2c78-42fe-ac4e-95fb276b9aa9
- Health: https://floor-students-estimated-apache.trycloudflare.com/api/health
- Local: http://127.0.0.1:8080

## Organization inventory

See `GET /api/org` — CEO, EA, VP R&D, Main PM, Dev PM (Claude), DevOps PM, Dev TL (Cursor), 3 Ultra Devs, QA TL + 3, DevOps TL + 3, IT TL + 2.

## Communication

- 10 Slack-compatible channels implemented
- Email mode: **SIMULATED** (limitation disclosed; never presented as real mailbox)
- Meeting room: live WebSocket responses, neural browser TTS, push-to-talk STT

## Evidence artifacts

- `srs_comm_tests.json`
- `srs_e2e_workflow.json`
- `srs_live_acceptance.txt`
- `srs_pytest.txt`

## Known limitations

1. No authenticated Google Cloud session → Cloud Run / Firestore / Redis / Secret Manager / Vertex Agent Platform not provisioned in GCP yet.
2. Email is simulated until Workspace/SMTP secrets exist.
3. Cloudflare quick tunnel is temporary public exposure of the Cloud Run-ready service; promote via `org_platform/deploy/deploy_cloud_run.sh` after auth.
4. WebRTC mesh is browser-capability ready; full SFU not required for current acceptance path.

## Operating guide

```bash
export PYTHONPATH=/workspace ORG_DATA_DIR=/tmp/org_platform_data_srs
bash org_platform/deploy/run_local.sh
# Run acceptance
curl -X POST http://127.0.0.1:8080/api/comm-tests/run-all
curl -X POST http://127.0.0.1:8080/api/workflows/e2e-demo
```

## Recovery / rollback

- Stateless container + `/data` volume for meetings/tasks/messages/audit JSON
- Redeploy previous Cloud Run revision when GCP auth available
- Local rollback: restore `ORG_DATA_DIR` snapshot

## Architecture (logical)

Browser/Meeting UI → Cloud Run (FastAPI/WebSocket) → Memory/Disk (+ Redis/Firestore adapters) → Slack channels / Simulated Email / Tasks / Audit  
Vertex AI Agent Platform / Speech / WebRTC / Pub/Sub / Scheduler: adapters ready; require GCP identity.

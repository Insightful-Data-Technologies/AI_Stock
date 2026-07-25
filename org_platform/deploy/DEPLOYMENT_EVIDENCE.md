# Deployment evidence — AI Capital Enterprise Org + Meeting Room

## Target

| Field | Value |
|---|---|
| GCP project | `gen-lang-client-0386540117` |
| Region | `europe-west2` |
| Service | `enterprise-org-meeting` |
| Platform | Google Cloud Run (Enterprise / Vertex AI Agent Platform) |
| Account | `chanan@ezevin.com` |

## Public URLs

- Home / Agents: https://enterprise-org-meeting-184723980511.europe-west2.run.app/
- Alias: https://enterprise-org-meeting-kl53rkbs4a-nw.a.run.app/
- Studio: https://enterprise-org-meeting-184723980511.europe-west2.run.app/studio
- Slack: https://enterprise-org-meeting-184723980511.europe-west2.run.app/slack
- Dashboard: https://enterprise-org-meeting-184723980511.europe-west2.run.app/dashboard
- Publish: https://enterprise-org-meeting-184723980511.europe-west2.run.app/publish

## Verification (2026-07-25)

| Check | Result |
|---|---|
| `GET /api/health` | 200 |
| `GET /` | 200 |
| `GET /studio` | 200 |
| `GET /slack` | 200 |
| `GET /dashboard` | 200 |
| `GET /publish` | 200 |
| `GET /api/org` roster | 21 agents |
| `POST /api/meetings` morning | meeting created with seeded messages |

## Deploy command

```bash
export GOOGLE_CLOUD_PROJECT=gen-lang-client-0386540117
export REGION=europe-west2
export SERVICE=enterprise-org-meeting
bash org_platform/deploy/deploy_cloud_run.sh
```

## Notes

- Public access uses annotation `run.googleapis.com/invoker-iam-disabled=true` because org policy blocks `allUsers` IAM bindings.
- Durable meeting state is currently on container disk (`ORG_DATA_DIR`); Redis/Firestore adapters remain ready when secrets/ADC are configured.

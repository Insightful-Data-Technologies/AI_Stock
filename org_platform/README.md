# AI Capital Enterprise Team — Insightful Data Technologies – 2.o AI
#
# SRS implementation for Google Cloud Enterprise / Vertex AI Agent Platform.
#
# Run locally:
#   export PYTHONPATH=/workspace ORG_DATA_DIR=/tmp/org_platform_data
#   bash org_platform/deploy/run_local.sh
#
# Acceptance:
#   PYTHONPATH=/workspace python3 -m pytest org_platform/tests -q
#   curl -X POST http://127.0.0.1:8080/api/comm-tests/run-all
#   curl -X POST http://127.0.0.1:8080/api/workflows/e2e-demo
#
# Cloud Run (requires gcloud auth on gen-lang-client-0386540117):
#   bash org_platform/deploy/deploy_cloud_run.sh
#
# Email note: mailboxes are SIMULATED until Workspace/SMTP secrets exist in Secret Manager.

#!/usr/bin/env bash
# Deploy org-platform to Cloud Run in gen-lang-client-0386540117
# Requires authenticated gcloud. Uses Secret Manager refs when secrets exist.
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0386540117}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-enterprise-org-meeting}"
IMAGE="gcr.io/${PROJECT}/${SERVICE}:$(date +%Y%m%d%H%M%S)"

echo "Project=${PROJECT} Region=${REGION} Service=${SERVICE}"

gcloud config set project "${PROJECT}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com redis.googleapis.com firestore.googleapis.com --project "${PROJECT}"

gcloud builds submit /workspace \
  --project "${PROJECT}" \
  --tag "${IMAGE}" \
  --dockerfile org_platform/deploy/Dockerfile

ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT},ORG_DATA_DIR=/data"
# Attach REDIS_URL from Secret Manager if present
if gcloud secrets describe org-platform-redis-url --project "${PROJECT}" >/dev/null 2>&1; then
  ENV_VARS="${ENV_VARS}"
  SECRETS="REDIS_URL=org-platform-redis-url:latest"
else
  SECRETS=""
fi

ARGS=(
  run deploy "${SERVICE}"
  --project "${PROJECT}"
  --region "${REGION}"
  --image "${IMAGE}"
  --platform managed
  --allow-unauthenticated
  --port 8080
  --memory 512Mi
  --cpu 1
  --min-instances 0
  --max-instances 5
  --set-env-vars "${ENV_VARS}"
)

if [[ -n "${SECRETS}" ]]; then
  ARGS+=(--set-secrets "${SECRETS}")
fi

gcloud "${ARGS[@]}"
gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --format='value(status.url)'

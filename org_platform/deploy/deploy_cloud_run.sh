#!/usr/bin/env bash
# Deploy org-platform (enterprise agents + meeting room) to Cloud Run
# Project: gen-lang-client-0386540117
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0386540117}"
REGION="${REGION:-europe-west2}"
SERVICE="${SERVICE:-enterprise-org-meeting}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y%m%d%H%M%S)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/${SERVICE}:${STAMP}"

# Prefer Artifact Registry in us-central1 if europe-west2 repo missing
if ! gcloud artifacts repositories describe cloud-run-source-deploy --location="${REGION}" --project="${PROJECT}" >/dev/null 2>&1; then
  REGION_AR="us-central1"
  IMAGE="${REGION_AR}-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/${SERVICE}:${STAMP}"
else
  REGION_AR="${REGION}"
fi

echo "Project=${PROJECT} Region=${REGION} Service=${SERVICE}"
echo "Image=${IMAGE}"

gcloud config set project "${PROJECT}"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project "${PROJECT}"

# Ensure Artifact Registry repo exists (us-central1 known to exist)
if ! gcloud artifacts repositories describe cloud-run-source-deploy --location="${REGION_AR}" --project="${PROJECT}" >/dev/null 2>&1; then
  gcloud artifacts repositories create cloud-run-source-deploy \
    --repository-format=docker \
    --location="${REGION_AR}" \
    --project="${PROJECT}" \
    --description="Cloud Run Source Deployments"
  IMAGE="${REGION_AR}-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/${SERVICE}:${STAMP}"
fi

gcloud builds submit "${ROOT}" \
  --project "${PROJECT}" \
  --config "${ROOT}/org_platform/deploy/cloudbuild.yaml" \
  --substitutions "_IMAGE=${IMAGE}"

ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT},ORG_DATA_DIR=/tmp/org_data,PYTHONPATH=/app"

# Org policy may block --allow-unauthenticated (allUsers). Deploy private first,
# then enable invoker-iam-disabled for public enterprise access.
gcloud run deploy "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --platform managed \
  --no-allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300 \
  --set-env-vars "${ENV_VARS}" \
  --labels "app=ai-capital-enterprise,component=org-meeting"

# Public access without allUsers binding (same pattern as AI Studio services)
gcloud run services update "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --update-annotations "run.googleapis.com/invoker-iam-disabled=true"

URL="$(gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --format='value(status.url)')"
echo "DEPLOYED_URL=${URL}"
curl -fsS "${URL}/api/health" | head -c 400 || true
echo
echo "${URL}"

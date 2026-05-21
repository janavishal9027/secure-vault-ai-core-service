#!/usr/bin/env bash
#
# Deploy the ai-core-service to one of the secure-vault-* k3s clusters.
# Mirrors the notes / Authentication deploy structure: render locally,
# scp, run remote script.
#
# Required environment variables (set per environment in Bitbucket
# Deployment variables):
#   VPS_USER, VPS_HOST                SSH details for the LXD host
#   REMOTE_DIR                        Shared staging dir for this cluster
#                                     (e.g. /root/secure-vault-dev-a/manifests)
#   LXD_CONTAINER                     LXD container name
#   KUBE_NAMESPACE                    k8s namespace inside the container
#   APP_NAME                          e.g. ai-core-service
#   IMAGE_REPO                        Docker image repo (e.g. kittuvittu/secure-vault-ai-core-service)
#   IMAGE_TAG                         Image tag — exported by the build step (commit SHA)
#   INGRESS_HOST                      Public hostname routed by host nginx
#   LXD_BRIDGE_IP                     IP of the LXD container on lxdbr0
#   POSTGRES_HOST, POSTGRES_PORT,
#   POSTGRES_DB, POSTGRES_USER,
#   POSTGRES_PASSWORD, POSTGRES_SCHEMA
#                                     Postgres (with pgvector) connection
#   GEMINI_API_KEY                    Gemini API key
#   JWT_SECRET                        Same value as Authentication / roles / notes
# Optional:
#   REPLICAS                          Default 1
#   CHAT_PROVIDER                     Default "openai"
#   EMBED_PROVIDER                    Default "gemini"
#   OPENAI_API_KEY                    Default empty (required only if either
#                                     provider is "openai")
#   CORS_ALLOWED_ORIGINS              Default "http://localhost:3000"

set -euo pipefail

: "${VPS_USER:?}"
: "${VPS_HOST:?}"
: "${REMOTE_DIR:?}"
: "${LXD_CONTAINER:?}"
: "${KUBE_NAMESPACE:?}"
: "${APP_NAME:?}"
: "${IMAGE_REPO:?}"
: "${IMAGE_TAG:?}"
: "${INGRESS_HOST:?}"
: "${LXD_BRIDGE_IP:?}"
: "${POSTGRES_HOST:?}"
: "${POSTGRES_PORT:?}"
: "${POSTGRES_DB:?}"
: "${POSTGRES_USER:?}"
: "${POSTGRES_PASSWORD:?}"
: "${POSTGRES_SCHEMA:?}"
: "${GEMINI_API_KEY:?}"
: "${JWT_SECRET:?}"

REPLICAS="${REPLICAS:-1}"
CHAT_PROVIDER="${CHAT_PROVIDER:-openai}"
EMBED_PROVIDER="${EMBED_PROVIDER:-gemini}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:3000}"

REMOTE_DIR="${REMOTE_DIR}/${APP_NAME}"
REMOTE_TARGET="${VPS_USER}@${VPS_HOST}"

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o BatchMode=yes
  -o ConnectTimeout=15
  -o ServerAliveInterval=30
  -o ServerAliveCountMax=10
)

echo "==> Rendering manifests locally"
mkdir -p rendered
render_file() {
  local in="$1" out="$2"
  sed \
    -e "s|\${APP_NAME}|${APP_NAME}|g" \
    -e "s|\${KUBE_NAMESPACE}|${KUBE_NAMESPACE}|g" \
    -e "s|\${IMAGE_REPO}|${IMAGE_REPO}|g" \
    -e "s|\${IMAGE_TAG}|${IMAGE_TAG}|g" \
    -e "s|\${INGRESS_HOST}|${INGRESS_HOST}|g" \
    -e "s|\${REPLICAS}|${REPLICAS}|g" \
    -e "s|\${POSTGRES_HOST}|${POSTGRES_HOST}|g" \
    -e "s|\${POSTGRES_PORT}|${POSTGRES_PORT}|g" \
    -e "s|\${POSTGRES_DB}|${POSTGRES_DB}|g" \
    -e "s|\${POSTGRES_USER}|${POSTGRES_USER}|g" \
    -e "s|\${POSTGRES_PASSWORD}|${POSTGRES_PASSWORD}|g" \
    -e "s|\${POSTGRES_SCHEMA}|${POSTGRES_SCHEMA}|g" \
    -e "s|\${CHAT_PROVIDER}|${CHAT_PROVIDER}|g" \
    -e "s|\${EMBED_PROVIDER}|${EMBED_PROVIDER}|g" \
    -e "s|\${GEMINI_API_KEY}|${GEMINI_API_KEY}|g" \
    -e "s|\${OPENAI_API_KEY}|${OPENAI_API_KEY}|g" \
    -e "s|\${JWT_SECRET}|${JWT_SECRET}|g" \
    -e "s|\${CORS_ALLOWED_ORIGINS}|${CORS_ALLOWED_ORIGINS}|g" \
    "$in" > "$out"
}
render_file deployment.yml rendered/deployment.yml
render_file service.yml    rendered/service.yml
render_file ingress.yml    rendered/ingress.yml

echo "==> Rendering nginx location snippet"
sed -e "s|\${LXD_BRIDGE_IP}|${LXD_BRIDGE_IP}|g" \
    ci/nginx/ai-core-service.location.conf > rendered/ai-core-service.location.conf

echo "=== Rendered manifests (secrets redacted) ==="
for f in rendered/*.yml; do
  echo "--- $f ---"
  sed \
    -e "s|${JWT_SECRET}|***JWT_SECRET***|g" \
    -e "s|${POSTGRES_PASSWORD}|***POSTGRES_PASSWORD***|g" \
    -e "s|${GEMINI_API_KEY}|***GEMINI_API_KEY***|g" \
    -e "s|${OPENAI_API_KEY:-__no_openai_key__}|***OPENAI_API_KEY***|g" \
    "$f"
done

echo "==> Preparing remote staging dir ${REMOTE_DIR} on ${VPS_HOST}"
ssh "${SSH_OPTS[@]}" "$REMOTE_TARGET" "mkdir -p '${REMOTE_DIR}'"

echo "==> Shipping manifests + deploy-remote.sh to ${VPS_HOST}"
scp "${SSH_OPTS[@]}" \
    rendered/deployment.yml \
    rendered/service.yml \
    rendered/ingress.yml \
    rendered/ai-core-service.location.conf \
    ci/deploy-remote.sh \
    "${REMOTE_TARGET}:${REMOTE_DIR}/"

echo "==> Executing deploy-remote.sh on ${VPS_HOST}"
ssh "${SSH_OPTS[@]}" "$REMOTE_TARGET" \
    "env \
      APP_NAME='${APP_NAME}' \
      KUBE_NAMESPACE='${KUBE_NAMESPACE}' \
      IMAGE_REPO='${IMAGE_REPO}' \
      IMAGE_TAG='${IMAGE_TAG}' \
      INGRESS_HOST='${INGRESS_HOST}' \
      REPLICAS='${REPLICAS}' \
      REMOTE_DIR='${REMOTE_DIR}' \
      LXD_CONTAINER='${LXD_CONTAINER}' \
      LXD_BRIDGE_IP='${LXD_BRIDGE_IP}' \
      bash '${REMOTE_DIR}/deploy-remote.sh'"

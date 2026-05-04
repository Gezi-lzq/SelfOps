#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
export SELFOPS_ROOT="${SELFOPS_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
BUB_REPO="${BUB_REPO:-${HOME}/Dev/bub}"

usage() {
  echo "Usage: $0 <profile|all>"
  exit 1
}

[ $# -ge 1 ] || usage
TARGET="$1"

discover_profiles() {
  for d in "${SCRIPT_DIR}/profiles"/*/; do
    [ -d "$d" ] && basename "$d"
  done
}

if [ "$TARGET" = "all" ]; then
  mapfile -t PROFILES < <(discover_profiles)
else
  PROFILES=("$TARGET")
fi

deploy_profile() {
  local profile="$1"
  PROFILE_ROOT="/opt/bub/profiles/${profile}"

  echo "==> Deploying profile: ${profile}"

  mkdir -p "${PROFILE_ROOT}/workspace"
  mkdir -p "${PROFILE_ROOT}/home/.bub"
  mkdir -p "${PROFILE_ROOT}/cache/pip"
  mkdir -p "${PROFILE_ROOT}/cache/uv"

  local compose_args=(-f "${COMPOSE_FILE}")
  local profile_compose="${SCRIPT_DIR}/profiles/${profile}/docker-compose.yml"
  if [ -f "${profile_compose}" ]; then
    compose_args+=(-f "${profile_compose}")
  fi

  echo "==> Building bub image"
  docker build --pull -t bub:latest "${BUB_REPO}"

  echo "==> Starting bub-${profile}"
  PROFILE="${profile}" docker compose "${compose_args[@]}" -p "bub-${profile}" up -d

  echo "==> Health check for bub-${profile}"
  if docker ps --filter "name=^/bub-${profile}$" --filter "status=running" --format '{{.Names}}' | grep -q "bub-${profile}"; then
    echo "    bub-${profile} is running"
  else
    echo "    WARNING: bub-${profile} is not running"
    docker logs "bub-${profile}" --tail 50
    return 1
  fi
}

for p in "${PROFILES[@]}"; do
  deploy_profile "$p"
done

echo "==> Done"

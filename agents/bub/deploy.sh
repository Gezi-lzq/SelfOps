#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

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

  local profile_dir="${SCRIPT_DIR}/profiles/${profile}"
  if [ -d "${profile_dir}" ]; then
    for f in AGENTS.md bub-reqs.txt; do
      [ -f "${profile_dir}/${f}" ] && cp "${profile_dir}/${f}" "${PROFILE_ROOT}/workspace/${f}"
    done
  fi

  [ -f "${SCRIPT_DIR}/startup.sh" ] && cp "${SCRIPT_DIR}/startup.sh" "${PROFILE_ROOT}/workspace/startup.sh"

  if [ -d "${SCRIPT_DIR}/shared/skills" ]; then
    mkdir -p "${PROFILE_ROOT}/workspace/.agents/skills"
    cp -r "${SCRIPT_DIR}/shared/skills/." "${PROFILE_ROOT}/workspace/.agents/skills/"
  fi

  if [ -d "${profile_dir}/skills" ]; then
    mkdir -p "${PROFILE_ROOT}/workspace/.agents/skills"
    cp -r "${profile_dir}/skills/." "${PROFILE_ROOT}/workspace/.agents/skills/"
  fi

  echo "==> Starting bub-${profile}"
  PROFILE="${profile}" docker compose -f "${COMPOSE_FILE}" -p "bub-${profile}" up -d

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

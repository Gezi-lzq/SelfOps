#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
export SELFOPS_ROOT="${SELFOPS_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SELFOPS_REPO_BRANCH="${SELFOPS_REPO_BRANCH:-main}"
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

echo "==> Building bub image"
docker build --pull -t bub:latest "${BUB_REPO}"

ensure_link() { mkdir -p "$(dirname "$1")"; ln -sfn "$2" "$1"; }

sync_selfops_workspace() {
  local profile="$1"
  local profile_root="/opt/bub/profiles/${profile}"
  local workspace_root="${profile_root}/workspace"
  local selfops_dir="${workspace_root}/selfops"

  if [ -d "${selfops_dir}/.git" ]; then
    git -C "${selfops_dir}" fetch origin "${SELFOPS_REPO_BRANCH}"
    git -C "${selfops_dir}" checkout "${SELFOPS_REPO_BRANCH}"
    git -C "${selfops_dir}" pull --ff-only origin "${SELFOPS_REPO_BRANCH}"
  else
    rm -rf "${selfops_dir}"
    git clone --branch "${SELFOPS_REPO_BRANCH}" --single-branch "${SELFOPS_ROOT}" "${selfops_dir}"
  fi

  ensure_link "${workspace_root}/AGENTS.md" "${selfops_dir}/agents/bub/profiles/${profile}/AGENTS.md"
  ensure_link "${workspace_root}/bub-reqs.txt" "${selfops_dir}/agents/bub/profiles/${profile}/bub-reqs.txt"
  ensure_link "${workspace_root}/plugins" "${selfops_dir}/agents/bub/plugins"
  ensure_link "${workspace_root}/startup.sh" "${selfops_dir}/agents/bub/profiles/${profile}/startup.sh"
}

deploy_profile() {
  local profile="$1"
  PROFILE_ROOT="/opt/bub/profiles/${profile}"

  echo "==> Deploying profile: ${profile}"

  mkdir -p "${PROFILE_ROOT}/workspace"
  mkdir -p "${PROFILE_ROOT}/home/.bub"
  mkdir -p "${PROFILE_ROOT}/cache/pip"
  mkdir -p "${PROFILE_ROOT}/cache/uv"
  mkdir -p "${PROFILE_ROOT}/workspace/data"

  sync_selfops_workspace "${profile}"

  local compose_args=(-f "${COMPOSE_FILE}")
  local profile_compose="${SCRIPT_DIR}/profiles/${profile}/docker-compose.yml"
  if [ -f "${profile_compose}" ]; then
    compose_args+=(-f "${profile_compose}")
  fi

  echo "==> Starting bub-${profile}"
  export PROFILE="${profile}"
  docker compose "${compose_args[@]}" -p "bub-${profile}" up -d --force-recreate

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

#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
PROFILE="${PROFILE:-yuna}"
SELFOPS_REPO_SLUG="${SELFOPS_REPO_SLUG:-Gezi-lzq/SelfOps}"
SELFOPS_REPO_BRANCH="${SELFOPS_REPO_BRANCH:-main}"
SELFOPS_REPO_DIR="${SELFOPS_REPO_DIR:-${WORKSPACE_ROOT}/SelfOps}"
SELFOPS_AGENT_RUNTIME_ROOT="${SELFOPS_AGENT_RUNTIME_ROOT:-${SELFOPS_REPO_DIR}/dev/agent-runtime}"
PROFILE_ROOT="${SELFOPS_REPO_DIR}/agents/bub/profiles/${PROFILE}"
PROFILE_PROJECTS="${PROFILE_PROJECTS:-${PROFILE_ROOT}/projects.toml}"
PYTHON_BIN="${PYTHON_BIN:-/app/.venv/bin/python}"
BUB_BIN="${BUB_BIN:-/app/.venv/bin/bub}"

clone_selfops() {
  if [ -n "${SELFOPS_REPO_URL:-}" ]; then
    git clone --branch "${SELFOPS_REPO_BRANCH}" --single-branch "${SELFOPS_REPO_URL}" "${SELFOPS_REPO_DIR}"
    return
  fi

  gh repo clone "${SELFOPS_REPO_SLUG}" "${SELFOPS_REPO_DIR}" -- --branch "${SELFOPS_REPO_BRANCH}" --single-branch
}

ensure_link() {
  local path="$1"
  local target="$2"

  case "${path}" in
    "${WORKSPACE_ROOT}"/*) ;;
    *)
      echo "Refusing to replace path outside ${WORKSPACE_ROOT}: ${path}" >&2
      exit 1
      ;;
  esac

  mkdir -p "$(dirname "${path}")"
  if [ -L "${path}" ]; then
    rm -f "${path}"
  elif [ -e "${path}" ]; then
    rm -rf "${path}"
  fi
  ln -s "${target}" "${path}"
}

mkdir -p "${WORKSPACE_ROOT}"

if command -v gh >/dev/null 2>&1; then
  gh auth setup-git >/dev/null
fi

if [ -d "${SELFOPS_REPO_DIR}/.git" ]; then
  if ! (
    git -C "${SELFOPS_REPO_DIR}" fetch origin "${SELFOPS_REPO_BRANCH}" &&
      git -C "${SELFOPS_REPO_DIR}" checkout "${SELFOPS_REPO_BRANCH}" &&
      git -C "${SELFOPS_REPO_DIR}" pull --ff-only origin "${SELFOPS_REPO_BRANCH}"
  ); then
    echo "Failed to sync ${SELFOPS_REPO_DIR} to ${SELFOPS_REPO_BRANCH}. Resolve local git state or point SELFOPS_REPO_DIR at a clean clone." >&2
    exit 1
  fi
else
  rm -rf "${SELFOPS_REPO_DIR}"
  clone_selfops
fi

if [ ! -f "${PROFILE_PROJECTS}" ]; then
  echo "Missing projects.toml for profile ${PROFILE}: ${PROFILE_PROJECTS}" >&2
  exit 1
fi

SELFOPS_AGENT_RUNTIME_ROOT="${SELFOPS_AGENT_RUNTIME_ROOT}" \
  "${PYTHON_BIN}" "${SELFOPS_AGENT_RUNTIME_ROOT}/scripts/agent_runtime.py" \
  apply --force --projects "${PROFILE_PROJECTS}"

# Keep a stable /workspace/.agents/skills target even when the profile currently declares no skills.
mkdir -p "${SELFOPS_REPO_DIR}/.agents/skills"
ensure_link "${WORKSPACE_ROOT}/AGENTS.md" "${PROFILE_ROOT}/AGENTS.md"
ensure_link "${WORKSPACE_ROOT}/bub-reqs.txt" "${PROFILE_ROOT}/bub-reqs.txt"
ensure_link "${WORKSPACE_ROOT}/plugins" "${SELFOPS_REPO_DIR}/agents/bub/plugins"
ensure_link "${WORKSPACE_ROOT}/.agents/skills" "${SELFOPS_REPO_DIR}/.agents/skills"

exec "${BUB_BIN}" gateway

#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="/workspace"
REPO_DIR="${WORKSPACE_ROOT}/automq-workspace"
REPO_SLUG="AutoMQ/automq-workspace"
REPO_BRANCH="feat/gezi"
SELFOPS_REPO_DIR="${SELFOPS_REPO_DIR:-/workspace/selfops}"
PROFILE_PROJECTS="${PROFILE_PROJECTS:-${SELFOPS_REPO_DIR}/agents/bub/profiles/automq-ops/projects.toml}"

mkdir -p "${WORKSPACE_ROOT}"
git config --global --add safe.directory "${SELFOPS_REPO_DIR}"

/app/.venv/bin/python "${SELFOPS_REPO_DIR}/dev/agent-runtime/scripts/agent_runtime.py" \
  apply --force --projects "${PROFILE_PROJECTS}"

gh auth setup-git >/dev/null

if [ -d "${REPO_DIR}/.git" ]; then
  git -C "${REPO_DIR}" fetch origin "${REPO_BRANCH}"
  git -C "${REPO_DIR}" checkout "${REPO_BRANCH}"
  git -C "${REPO_DIR}" pull --ff-only origin "${REPO_BRANCH}"
else
  rm -rf "${REPO_DIR}"
  gh repo clone "${REPO_SLUG}" "${REPO_DIR}" -- --branch "${REPO_BRANCH}" --single-branch
fi

exec /app/.venv/bin/bub gateway

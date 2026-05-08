#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="/workspace"
REPO_DIR="${WORKSPACE_ROOT}/automq-workspace"
REPO_SLUG="AutoMQ/automq-workspace"
REPO_BRANCH="feat/gezi"

mkdir -p "${WORKSPACE_ROOT}"

/app/.venv/bin/python /workspace/selfops/dev/agent-runtime/scripts/agent_runtime.py \
  apply --force --projects /workspace/selfops/agents/bub/profiles/automq-ops/projects.toml

gh auth setup-git >/dev/null

if [ -d "${REPO_DIR}/.git" ]; then
  git -C "${REPO_DIR}" pull --ff-only origin "${REPO_BRANCH}"
else
  rm -rf "${REPO_DIR}"
  gh repo clone "${REPO_SLUG}" "${REPO_DIR}" -- --branch "${REPO_BRANCH}" --single-branch
fi

exec /app/.venv/bin/bub gateway

#!/usr/bin/env bash
set -euo pipefail

SELFOPS_REPO_DIR="${SELFOPS_REPO_DIR:-/workspace/selfops}"
PROFILE_PROJECTS="${PROFILE_PROJECTS:-${SELFOPS_REPO_DIR}/agents/bub/profiles/yuna/projects.toml}"
git config --global --add safe.directory "${SELFOPS_REPO_DIR}"

/app/.venv/bin/python "${SELFOPS_REPO_DIR}/dev/agent-runtime/scripts/agent_runtime.py" \
  apply --force --projects "${PROFILE_PROJECTS}"

exec /app/.venv/bin/bub gateway

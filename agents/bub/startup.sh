#!/usr/bin/env bash
set -euo pipefail

# Generic fallback startup; profile-specific startup.sh is the default runtime entrypoint.
PROFILE="${PROFILE:-yuna}"
SELFOPS_REPO_DIR="${SELFOPS_REPO_DIR:-/workspace/selfops}"
PROFILE_PROJECTS="${PROFILE_PROJECTS:-${SELFOPS_REPO_DIR}/agents/bub/profiles/${PROFILE}/projects.toml}"

/app/.venv/bin/python "${SELFOPS_REPO_DIR}/dev/agent-runtime/scripts/agent_runtime.py" \
  apply --force --projects "${PROFILE_PROJECTS}"

exec /app/.venv/bin/bub gateway

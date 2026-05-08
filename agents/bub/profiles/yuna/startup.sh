#!/usr/bin/env bash
set -euo pipefail

/app/.venv/bin/python /workspace/selfops/dev/agent-runtime/scripts/agent_runtime.py \
  apply --force --projects /workspace/selfops/agents/bub/profiles/yuna/projects.toml

exec /app/.venv/bin/bub gateway

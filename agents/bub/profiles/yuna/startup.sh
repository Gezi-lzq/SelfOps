#!/usr/bin/env bash
set -euo pipefail

SELFOPS_REPO_DIR="${SELFOPS_REPO_DIR:-/workspace/selfops}"
PROFILE_PROJECTS="${PROFILE_PROJECTS:-${SELFOPS_REPO_DIR}/agents/bub/profiles/yuna/projects.toml}"
git config --global --add safe.directory "${SELFOPS_REPO_DIR}"

/app/.venv/bin/python "${SELFOPS_REPO_DIR}/dev/agent-runtime/scripts/agent_runtime.py" \
  apply --force --projects "${PROFILE_PROJECTS}"

# Bub core currently ships the Telegram skill source under /app/src/skills,
# while runtime skill discovery also scans the installed skills package.
# Bridge it at startup so channel-specific Telegram replies remain discoverable.
SKILLS_SITE="/app/.venv/lib/python3.12/site-packages/skills"
TELEGRAM_SKILL_SRC="/app/src/skills/telegram"
if [[ -d "${SKILLS_SITE}" && -d "${TELEGRAM_SKILL_SRC}" ]]; then
  ln -sfn "${TELEGRAM_SKILL_SRC}" "${SKILLS_SITE}/telegram"
fi

exec /app/.venv/bin/bub gateway

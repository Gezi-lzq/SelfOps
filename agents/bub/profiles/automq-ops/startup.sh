#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="/workspace"
REPO_DIR="${WORKSPACE_ROOT}/automq-workspace"
REPO_SLUG="AutoMQ/automq-workspace"
REPO_BRANCH="feat/gezi"

mkdir -p "${WORKSPACE_ROOT}"

if command -v gh >/dev/null 2>&1; then
  gh auth setup-git >/dev/null
fi

if [ -d "${REPO_DIR}/.git" ]; then
  git -C "${REPO_DIR}" fetch origin "${REPO_BRANCH}"
  git -C "${REPO_DIR}" checkout "${REPO_BRANCH}"
  git -C "${REPO_DIR}" pull --ff-only origin "${REPO_BRANCH}"
else
  rm -rf "${REPO_DIR}"
  gh repo clone "${REPO_SLUG}" "${REPO_DIR}" -- --branch "${REPO_BRANCH}" --single-branch
fi

# bub-codex manages /workspace/.agents/skills during turn execution.
# Remove the legacy symlink if it exists so pathlib.mkdir(..., exist_ok=True)
# does not fail with FileExistsError.
if [ -L "${WORKSPACE_ROOT}/.agents/skills" ]; then
  rm -f "${WORKSPACE_ROOT}/.agents/skills"
fi

exec /app/.venv/bin/bub gateway

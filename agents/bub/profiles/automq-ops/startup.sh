#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="/workspace"
REPO_DIR="${WORKSPACE_ROOT}/automq-workspace"
SKILLS_LINK_DIR="${WORKSPACE_ROOT}/.agents"
SKILLS_LINK_PATH="${SKILLS_LINK_DIR}/skills"
REPO_URL="https://github.com/AutoMQ/automq-workspace"
REPO_BRANCH="feat/gezi"

mkdir -p "${WORKSPACE_ROOT}" "${SKILLS_LINK_DIR}"

if [ -d "${REPO_DIR}/.git" ]; then
  git -C "${REPO_DIR}" fetch origin "${REPO_BRANCH}"
  git -C "${REPO_DIR}" checkout "${REPO_BRANCH}"
  git -C "${REPO_DIR}" pull --ff-only origin "${REPO_BRANCH}"
else
  rm -rf "${REPO_DIR}"
  git clone --branch "${REPO_BRANCH}" --single-branch "${REPO_URL}" "${REPO_DIR}"
fi

ln -sfn "${REPO_DIR}/.agents/skills" "${SKILLS_LINK_PATH}"

exec /app/.venv/bin/bub gateway

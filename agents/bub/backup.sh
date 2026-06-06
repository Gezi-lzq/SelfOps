#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:?Usage: $0 <profile>}"
TAPE_PATH="${BUB_TAPE_PATH:-/opt/bub/profiles/${PROFILE}/home/.bub/tapes.sqlite3}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RELEASE_PREFIX="tape-backup-${PROFILE}-"
TAG="${BUB_BACKUP_RELEASE_TAG:-}"
BACKUP_TMPDIR="${BUB_BACKUP_TMPDIR:-${TMPDIR:-/tmp}}"
ASSET_DIR="$(mktemp -d "${BACKUP_TMPDIR%/}/tape-backup-${PROFILE}-${TIMESTAMP}-XXXXXX")"
ARCHIVE_PATH="${ASSET_DIR}/tape-backup-${PROFILE}.tar.gz"
trap 'rm -rf "${ASSET_DIR}"' EXIT

if [ ! -f "${TAPE_PATH}" ]; then
  echo "No tape found at ${TAPE_PATH}"
  exit 1
fi

if [ -z "${TAG}" ]; then
  TAG="$(
    gh release list --limit 100 --json tagName \
      --jq ".[] | select(.tagName | startswith(\"${RELEASE_PREFIX}\")) | .tagName" \
      | head -n 1
  )"
fi

if [ -z "${TAG}" ]; then
  echo "No existing tape backup release found for profile: ${PROFILE}" >&2
  echo "Create one release first, then rerun backup to replace its asset." >&2
  exit 1
fi

cp "${TAPE_PATH}" "${ASSET_DIR}/tapes.sqlite3"
cp "${TAPE_PATH}-wal" "${ASSET_DIR}/tapes.sqlite3-wal" 2>/dev/null || true
cp "${TAPE_PATH}-shm" "${ASSET_DIR}/tapes.sqlite3-shm" 2>/dev/null || true

backup_files=(tapes.sqlite3)
[ -f "${ASSET_DIR}/tapes.sqlite3-wal" ] && backup_files+=(tapes.sqlite3-wal)
[ -f "${ASSET_DIR}/tapes.sqlite3-shm" ] && backup_files+=(tapes.sqlite3-shm)

tar -czf "${ARCHIVE_PATH}" -C "${ASSET_DIR}" "${backup_files[@]}"

gh release upload "${TAG}" "${ARCHIVE_PATH}" --clobber
gh release edit "${TAG}" \
  --title "Tape Backup ${PROFILE}" \
  --notes "Automated tape backup for profile: ${PROFILE}

Last updated: ${TIMESTAMP}"

echo "==> Backup asset replaced: ${TAG}"

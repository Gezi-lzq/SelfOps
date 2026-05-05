#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:?Usage: $0 <profile>}"
TAPE_PATH="${BUB_TAPE_PATH:-/opt/bub/profiles/${PROFILE}/home/.bub/tapes.sqlite3}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TAG="tape-backup-${PROFILE}-${TIMESTAMP}"
BACKUP_TMPDIR="${BUB_BACKUP_TMPDIR:-${TMPDIR:-/tmp}}"
ASSET_DIR="$(mktemp -d "${BACKUP_TMPDIR%/}/tape-backup-${PROFILE}-${TIMESTAMP}-XXXXXX")"
ARCHIVE_PATH="${ASSET_DIR}/tape-backup-${PROFILE}.tar.gz"

if [ ! -f "${TAPE_PATH}" ]; then
  echo "No tape found at ${TAPE_PATH}"
  exit 1
fi

cp "${TAPE_PATH}" "${ASSET_DIR}/tapes.sqlite3"
cp "${TAPE_PATH}-wal" "${ASSET_DIR}/tapes.sqlite3-wal" 2>/dev/null || true
cp "${TAPE_PATH}-shm" "${ASSET_DIR}/tapes.sqlite3-shm" 2>/dev/null || true

backup_files=(tapes.sqlite3)
[ -f "${ASSET_DIR}/tapes.sqlite3-wal" ] && backup_files+=(tapes.sqlite3-wal)
[ -f "${ASSET_DIR}/tapes.sqlite3-shm" ] && backup_files+=(tapes.sqlite3-shm)

tar -czf "${ARCHIVE_PATH}" -C "${ASSET_DIR}" "${backup_files[@]}"

gh release create "${TAG}" \
  "${ARCHIVE_PATH}" \
  --title "Tape Backup ${PROFILE} ${TIMESTAMP}" \
  --notes "Automated tape backup for profile: ${PROFILE}"

gh release list --limit 100 \
  | grep "tape-backup-${PROFILE}-" \
  | tail -n +2 \
  | awk '{print $1}' \
  | xargs -I {} gh release delete {} --yes --cleanup-tag 2>/dev/null || true

rm -rf "${ASSET_DIR}"
echo "==> Backup complete: ${TAG}"

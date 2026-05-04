#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:?Usage: $0 <profile>}"
TAPE_PATH="/opt/bub/profiles/${PROFILE}/home/.bub/tapes.sqlite3"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TAG="tape-backup-${PROFILE}-${TIMESTAMP}"
ASSET_DIR="/tmp/tape-backup-${TIMESTAMP}"

if [ ! -f "${TAPE_PATH}" ]; then
  echo "No tape found at ${TAPE_PATH}"
  exit 1
fi

mkdir -p "${ASSET_DIR}"
cp "${TAPE_PATH}" "${ASSET_DIR}/tapes.sqlite3"
cp "${TAPE_PATH}-wal" "${ASSET_DIR}/tapes.sqlite3-wal" 2>/dev/null || true
cp "${TAPE_PATH}-shm" "${ASSET_DIR}/tapes.sqlite3-shm" 2>/dev/null || true

tar -czf "${ASSET_DIR}/tape-backup-${PROFILE}.tar.gz" -C "${ASSET_DIR}" .

gh release create "${TAG}" \
  "${ASSET_DIR}/tape-backup-${PROFILE}.tar.gz" \
  --title "Tape Backup ${PROFILE} ${TIMESTAMP}" \
  --notes "Automated tape backup for profile: ${PROFILE}"

gh release list --limit 100 \
  | grep "tape-backup-${PROFILE}-" \
  | tail -n +2 \
  | awk '{print $1}' \
  | xargs -I {} gh release delete {} --yes --cleanup-tag 2>/dev/null || true

rm -rf "${ASSET_DIR}"
echo "==> Backup complete: ${TAG}"

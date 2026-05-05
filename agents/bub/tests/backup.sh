#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="test-backup"
TMPDIR="$(mktemp -d)"
TAPE_DIR="${TMPDIR}/profile/home/.bub"
BACKUP_TMPDIR="${TMPDIR}/backup-tmp"
FAKEBIN="${TMPDIR}/bin"
ARCHIVE_COPY="${TMPDIR}/archive.tar.gz"

cleanup() {
  rm -rf "${TMPDIR}"
}
trap cleanup EXIT

mkdir -p "${TAPE_DIR}" "${FAKEBIN}"
mkdir -p "${BACKUP_TMPDIR}"
printf 'main-db' > "${TAPE_DIR}/tapes.sqlite3"
printf 'wal-db' > "${TAPE_DIR}/tapes.sqlite3-wal"
printf 'shm-db' > "${TAPE_DIR}/tapes.sqlite3-shm"

cat > "${FAKEBIN}/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [ "$1" = "release" ] && [ "$2" = "create" ]; then
  cp "$4" "${ARCHIVE_COPY}"
  exit 0
fi

if [ "$1" = "release" ] && [ "$2" = "list" ]; then
  exit 0
fi

if [ "$1" = "release" ] && [ "$2" = "delete" ]; then
  exit 0
fi

echo "unexpected gh invocation: $*" >&2
exit 1
EOF
chmod +x "${FAKEBIN}/gh"

PATH="${FAKEBIN}:$PATH" \
ARCHIVE_COPY="${ARCHIVE_COPY}" \
BUB_TAPE_PATH="${TAPE_DIR}/tapes.sqlite3" \
TMPDIR="${BACKUP_TMPDIR}" \
bash "${ROOT}/backup.sh" "${PROFILE}"

contents="$(tar -tzf "${ARCHIVE_COPY}")"
printf '%s\n' "${contents}" | grep -Fx 'tapes.sqlite3' >/dev/null
printf '%s\n' "${contents}" | grep -Fx 'tapes.sqlite3-wal' >/dev/null
printf '%s\n' "${contents}" | grep -Fx 'tapes.sqlite3-shm' >/dev/null
if printf '%s\n' "${contents}" | grep -F 'tape-backup-' >/dev/null; then
  echo "archive should not contain itself" >&2
  exit 1
fi

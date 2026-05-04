#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNERS_TOML="${SCRIPT_DIR}/runners.toml"
ARCH="linux-x64"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required" >&2
  exit 1
fi

list_runners() {
  grep '^\[runners\.' "$RUNNERS_TOML" | sed 's/\[runners\.\(.*\)\]/\1/'
}

get_field() {
  local runner="$1" field="$2"
  sed -n "/^\[runners\.${runner}\]/,/^\[/p" "$RUNNERS_TOML" \
    | grep "^${field}" \
    | head -1 \
    | sed 's/.*= *"\(.*\)"/\1/'
}

get_service_name() {
  local runner_dir="$1"
  local svc_file
  svc_file=$(find /etc/systemd/system -maxdepth 1 -name "actions.runner.*" -newer "$runner_dir/.runner" 2>/dev/null | head -1)
  if [ -z "$svc_file" ]; then
    svc_file=$(find /etc/systemd/system -maxdepth 1 -name "actions.runner.*" 2>/dev/null | grep "$(basename "$runner_dir")" | head -1)
  fi
  if [ -z "$svc_file" ]; then
    svc_file=$(find /etc/systemd/system -maxdepth 1 -name "actions.runner.*" 2>/dev/null | while read -r f; do
      if grep -q "WorkingDirectory=${runner_dir}" "$f" 2>/dev/null; then echo "$f"; break; fi
    done)
  fi
  [ -n "$svc_file" ] && basename "$svc_file" .service || echo ""
}

ensure_runner() {
  local id="$1"
  local repo dir version name labels
  repo="$(get_field "$id" repo)"
  dir="$(get_field "$id" dir)"
  version="$(get_field "$id" version)"
  name="$(get_field "$id" name)"
  labels="$(get_field "$id" labels | tr -d '[]"' | tr ',' ',')"

  echo "==> Runner: ${id} (${name})"
  echo "    repo=${repo} dir=${dir}"

  # Check if already configured and running
  if [ -f "${dir}/.runner" ]; then
    local svc
    svc="$(get_service_name "$dir")"
    if [ -n "$svc" ] && systemctl is-active --quiet "$svc" 2>/dev/null; then
      echo "    Already running (${svc})"
      return 0
    fi
    # Configured but not running - start it
    if [ -n "$svc" ]; then
      echo "    Service exists but not active, starting..."
      sudo systemctl start "$svc"
      echo "    Started"
      return 0
    fi
  fi

  # Download runner binary if needed
  mkdir -p "$dir"
  if [ ! -f "${dir}/bin/Runner.Listener" ]; then
    echo "    Downloading runner v${version}..."
    curl -sL "https://github.com/actions/runner/releases/download/v${version}/actions-runner-${ARCH}-${version}.tar.gz" | tar xz -C "$dir"
  fi

  # Register if not configured
  if [ ! -f "${dir}/.runner" ]; then
    echo "    Registering with GitHub..."
    local token
    token="$(gh api "repos/${repo}/actions/runners/registration-token" -X POST --jq '.token')"
    (cd "$dir" && ./config.sh \
      --url "https://github.com/${repo}" \
      --token "$token" \
      --name "$name" \
      --labels "$labels" \
      --unattended \
      --replace)
  fi

  # Install and start systemd service
  echo "    Installing systemd service..."
  (cd "$dir" && sudo ./svc.sh install "$(whoami)" && sudo ./svc.sh start)

  echo "    Done"
}

status_runner() {
  local id="$1"
  local dir name repo
  dir="$(get_field "$id" dir)"
  name="$(get_field "$id" name)"
  repo="$(get_field "$id" repo)"

  if [ ! -f "${dir}/.runner" ]; then
    printf "  %-20s %-25s NOT INSTALLED\n" "$id" "$repo"
    return
  fi

  local svc
  svc="$(get_service_name "$dir")"
  if [ -n "$svc" ] && systemctl is-active --quiet "$svc" 2>/dev/null; then
    printf "  %-20s %-25s RUNNING (%s)\n" "$id" "$repo" "$svc"
  else
    printf "  %-20s %-25s STOPPED\n" "$id" "$repo"
  fi
}

remove_runner() {
  local id="$1"
  local dir repo
  dir="$(get_field "$id" dir)"
  repo="$(get_field "$id" repo)"

  echo "==> Removing runner: ${id}"

  if [ ! -f "${dir}/.runner" ]; then
    echo "    Not installed, nothing to do"
    return 0
  fi

  local svc
  svc="$(get_service_name "$dir")"
  if [ -n "$svc" ]; then
    echo "    Stopping service..."
    sudo ./svc.sh stop 2>/dev/null || true
    sudo ./svc.sh uninstall 2>/dev/null || true
  fi

  echo "    Deregistering from GitHub..."
  local token
  token="$(gh api "repos/${repo}/actions/runners/remove-token" -X POST --jq '.token')"
  (cd "$dir" && ./config.sh remove --token "$token") || true

  echo "    Done (directory preserved at ${dir})"
}

case "${1:-}" in
  ensure)
    shift
    if [ $# -gt 0 ]; then
      ensure_runner "$1"
    else
      for r in $(list_runners); do ensure_runner "$r"; done
    fi
    ;;
  status)
    echo "Runners:"
    for r in $(list_runners); do status_runner "$r"; done
    ;;
  remove)
    [ $# -ge 2 ] || { echo "Usage: $0 remove <runner-id>" >&2; exit 1; }
    remove_runner "$2"
    ;;
  *)
    echo "Usage: $0 {ensure [id]|status|remove <id>}"
    exit 1
    ;;
esac

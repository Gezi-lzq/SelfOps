#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SRC="$SCRIPT_DIR/config.toml"
CONFIG_DST="$HOME/.config/mise/config.toml"

ACTIVATE_SHELL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --activate-zsh)
      ACTIVATE_SHELL="zsh"
      ;;
    --activate-bash)
      ACTIVATE_SHELL="bash"
      ;;
    *)
      echo "unknown argument: $1" >&2
      echo "usage: bash dev/environment/bootstrap.sh [--activate-zsh|--activate-bash]" >&2
      exit 2
      ;;
  esac
  shift
done

if command -v mise >/dev/null 2>&1; then
  MISE_BIN="$(type -P mise || true)"
elif [[ -x "$HOME/.local/bin/mise" ]]; then
  MISE_BIN="$HOME/.local/bin/mise"
else
  echo "mise not found. Install it first: https://mise.jdx.dev/getting-started.html" >&2
  exit 1
fi

if [[ -z "${MISE_BIN:-}" ]]; then
  echo "failed to resolve mise binary path" >&2
  exit 1
fi

mkdir -p "$HOME/.config/mise"
ln -sfn "$CONFIG_SRC" "$CONFIG_DST"
echo "linked $CONFIG_DST -> $CONFIG_SRC"

ensure_shell_activation() {
  local shell_name="$1"
  local rc_file="$2"
  local line='eval "$($HOME/.local/bin/mise activate '"$shell_name"')"'

  touch "$rc_file"
  if grep -Fq "$line" "$rc_file"; then
    echo "mise activation already present in $rc_file"
    return
  fi

  {
    echo
    echo "# Added by SelfOps dev/environment bootstrap"
    echo "$line"
  } >> "$rc_file"
  echo "added mise activation to $rc_file"
}

case "$ACTIVATE_SHELL" in
  zsh)
    ensure_shell_activation "zsh" "$HOME/.zshrc"
    ;;
  bash)
    ensure_shell_activation "bash" "$HOME/.bashrc"
    ;;
esac

(
  cd "$HOME"
  "$MISE_BIN" install
  "$MISE_BIN" ls -g
)

if [[ -z "$ACTIVATE_SHELL" ]]; then
  cat <<'EOF'

next step:
  add `eval "$($HOME/.local/bin/mise activate zsh)"` to ~/.zshrc
  or rerun this script with --activate-zsh
EOF
else
  echo
  echo "restart your shell or run: exec $ACTIVATE_SHELL"
fi

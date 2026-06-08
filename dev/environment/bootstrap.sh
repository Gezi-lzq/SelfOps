#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SRC="$SCRIPT_DIR/config.toml"
CONFIG_DST="$HOME/.config/mise/config.toml"

ACTIVATE_SHELL=""
ACTIVATE_PROFILE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --activate-zsh)
      ACTIVATE_SHELL="zsh"
      ;;
    --activate-bash)
      ACTIVATE_SHELL="bash"
      ;;
    --no-activate-profile)
      ACTIVATE_PROFILE=0
      ;;
    *)
      echo "unknown argument: $1" >&2
      echo "usage: bash dev/environment/bootstrap.sh [--activate-zsh|--activate-bash] [--no-activate-profile]" >&2
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

ensure_profile_shims() {
  local profile_file="$HOME/.profile"
  local start_marker="# SelfOps managed mise shims: begin"
  local end_marker="# SelfOps managed mise shims: end"

  touch "$profile_file"

  local block
  block="$(cat <<'EOF'
# SelfOps managed mise shims: begin
if [ -x "$HOME/.local/bin/mise" ]; then
    eval "$($HOME/.local/bin/mise activate bash --shims)"
fi
# SelfOps managed mise shims: end
EOF
)"

  local tmp_file
  tmp_file="$(mktemp)"
  awk -v block="$block" -v start="$start_marker" -v end="$end_marker" '
    $0 == start {
      skip = 1
      next
    }
    index($0, end) == 1 {
      skip = 0
      after_block = 1
      suffix = substr($0, length(end) + 1)
      if (suffix != "") {
        print suffix
        after_block = 0
      }
      next
    }
    skip {
      next
    }
    after_block && $0 == "" {
      next
    }
    after_block {
      after_block = 0
    }
    !inserted && /^# if running bash$/ {
      printf "%s\n\n", block
      inserted = 1
    }
    { print }
    END {
      if (!inserted) {
        printf "\n%s\n", block
      }
    }
  ' "$profile_file" > "$tmp_file"

  if cmp -s "$tmp_file" "$profile_file"; then
    echo "mise shims already present in $profile_file"
  else
    cat "$tmp_file" > "$profile_file"
    echo "ensured mise shims in $profile_file"
  fi

  rm -f "$tmp_file"
}

if [[ "$ACTIVATE_PROFILE" -eq 1 ]]; then
  ensure_profile_shims
fi

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

profile shims:
  ~/.profile has been configured so login/non-interactive shells can resolve mise tools
EOF
else
  echo
  echo "restart your shell or run: exec $ACTIVATE_SHELL"
fi

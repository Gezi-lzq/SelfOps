#!/usr/bin/env bash
set -euo pipefail

case "$(uname -s)" in
  Linux) os="linux" ;;
  Darwin) os="darwin" ;;
  *)
    echo "Unsupported OS: $(uname -s)" >&2
    exit 1
    ;;
esac

case "$(uname -m)" in
  x86_64 | amd64) arch="amd64" ;;
  aarch64 | arm64) arch="arm64" ;;
  *)
    echo "Unsupported architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

install_dir="$HOME/.local/bin"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$install_dir"

url="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-${os}-${arch}.tgz"
archive="$tmp_dir/ngrok.tgz"

curl -fsSL "$url" -o "$archive"
tar -xzf "$archive" -C "$tmp_dir" ngrok
install -m 0755 "$tmp_dir/ngrok" "$install_dir/ngrok"

"$install_dir/ngrok" version


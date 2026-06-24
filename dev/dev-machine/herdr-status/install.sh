#!/usr/bin/env bash
set -euo pipefail

selfops_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
env_dir="$HOME/.config/selfops"
env_file="$env_dir/herdr-status.env"
systemd_user_dir="$HOME/.config/systemd/user"

mkdir -p "$env_dir" "$systemd_user_dir"

if [[ ! -f "$env_file" ]]; then
  cp "$selfops_root/dev/dev-machine/herdr-status/herdr-status.env.example" "$env_file"
  chmod 600 "$env_file"
  echo "Created $env_file"
else
  echo "Keeping existing $env_file"
fi

sed "s#__SELFOPS_ROOT__#$selfops_root#g" \
  "$selfops_root/dev/dev-machine/herdr-status/systemd/herdr-status.service" \
  >"$systemd_user_dir/herdr-status.service"

systemctl --user daemon-reload
echo "Installed herdr-status.service"

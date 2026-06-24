#!/usr/bin/env bash
set -euo pipefail

selfops_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
env_dir="$HOME/.config/selfops"
env_file="$env_dir/herdr-web.env"
systemd_user_dir="$HOME/.config/systemd/user"

mkdir -p "$env_dir" "$systemd_user_dir"

if [[ ! -f "$env_file" ]]; then
  if [[ -r /proc/sys/kernel/random/uuid ]]; then
    password="$(tr -d '-' </proc/sys/kernel/random/uuid)$(tr -d '-' </proc/sys/kernel/random/uuid)"
    password="${password:0:32}"
  else
    password="change-me"
  fi

  sed \
    -e "s#HERDR_WEB_TTYD_CREDENTIAL=debian:change-me#HERDR_WEB_TTYD_CREDENTIAL=${USER:-debian}:${password}#" \
    -e "s#HERDR_WEB_CWD=/home/debian#HERDR_WEB_CWD=$HOME#" \
    "$selfops_root/dev/dev-machine/herdr-web/herdr-web.env.example" >"$env_file"
  chmod 600 "$env_file"
  echo "Created $env_file"
else
  echo "Keeping existing $env_file"
fi

render_unit() {
  local src="$1"
  local dst="$2"
  sed "s#__SELFOPS_ROOT__#$selfops_root#g" "$src" >"$dst"
}

render_unit \
  "$selfops_root/dev/dev-machine/herdr-web/systemd/herdr-web-ttyd.service" \
  "$systemd_user_dir/herdr-web-ttyd.service"

render_unit \
  "$selfops_root/dev/dev-machine/herdr-web/systemd/herdr-web-ngrok.service" \
  "$systemd_user_dir/herdr-web-ngrok.service"

systemctl --user daemon-reload

echo "Installed Herdr web systemd user units."
echo
echo "Next steps:"
echo "  1. Ensure ttyd and ngrok are installed."
echo "  2. Authenticate ngrok: ngrok config add-authtoken <token>"
echo "  3. Review $env_file"
echo "  4. Start: systemctl --user start herdr-web-ttyd.service herdr-web-ngrok.service"

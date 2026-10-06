#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f /etc/mihomo/subscription.env ]]; then
  echo "Create /etc/mihomo/subscription.env before installing." >&2
  exit 1
fi

install -d -m 0755 /etc/mihomo
chmod 0600 /etc/mihomo/subscription.env
install -m 0755 "$source_dir/update-mihomo-subscription" /usr/local/sbin/update-mihomo-subscription
install -m 0644 "$source_dir/systemd/mihomo.service" /etc/systemd/system/mihomo.service
install -m 0644 "$source_dir/systemd/mihomo-subscription.service" /etc/systemd/system/mihomo-subscription.service
install -m 0644 "$source_dir/systemd/mihomo-subscription.timer" /etc/systemd/system/mihomo-subscription.timer

systemctl daemon-reload

echo "Installed Mihomo updater and systemd units."
echo "Run: systemctl start mihomo-subscription.service"

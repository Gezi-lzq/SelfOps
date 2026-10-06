# gezi-dev system protection

This directory records the host-level safeguards for the `gezi-dev` development
machine. The settings keep disposable test workloads from exhausting the system
disk or taking every remote recovery path down with them.

## Applied policy

- Docker default `json-file` logs rotate at 50 MiB and retain three files.
- Persistent journal usage is capped at 1 GiB, keeps 10 GiB free, and retains at
  most 14 days.
- An 8 GiB swap file lives on `/data`, with `vm.swappiness=10`.
- OpenSSH keeps its built-in `OOMScoreAdjust=-1000`; NetBird and QEMU Guest
  Agent use `OOMScoreAdjust=-750`.
- The system containerd root is `/data/containerd`, separate from the 100 GiB
  system disk. k3s continues to use its own `/data/k3s` data directory.

## Files

- `docker-daemon.json`: Docker daemon defaults.
- `containerd-config.toml`: system containerd storage location.
- `journald-disk-limits.conf`: persistent journal bounds.
- `oom-protection.conf`: systemd drop-in shared by critical access services.
- `memory-protection.conf`: low-swappiness host policy.

## Validation

```bash
docker info --format '{{.LoggingDriver}} {{.DockerRootDir}}'
sudo containerd config dump | sed -n '1,20p'
sudo swapon --show
systemctl show netbird qemu-guest-agent -p OOMScoreAdjust
sudo sed -n '1p' /proc/$(systemctl show ssh -p MainPID --value)/oom_score_adj
sudo journalctl --disk-usage
df -h / /data
```

Docker log defaults only apply to newly created containers. Existing containers
retain their configured log options until they are recreated.

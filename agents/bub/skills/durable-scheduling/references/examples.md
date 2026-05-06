# Durable Scheduling Examples

## Use This Skill When

- The user says "10 minutes later remind me"
- The user wants a periodic recheck every N minutes
- The user asks whether tasks survive container or image rebuilds
- The user asks whether to use `bub-schedule` or `cron` / `at`

## Preferred Flow

1. Confirm the current profile has both:
   - `bub-schedule` in `bub-reqs.txt`
   - `schedule` in `BUB_ENABLED_CHANNELS`
2. Prefer `schedule.add` for work that should come back into the current session.
3. Explain that persistence comes from `/root/jobs.json`, backed by the mounted profile home.
4. Use OS schedulers only when the scheduling concern should live outside Bub.

## Tool Patterns

### One-shot delay

Use `schedule.add` with `after_seconds` and a plain reminder message.

Expected shape:

```text
after_seconds=600
message="10分钟后回查 remote write 状态"
```

### Periodic job

Use `schedule.add` with `interval_seconds`.

Expected shape:

```text
interval_seconds=300
message="每5分钟检查一次 backlog 指标"
```

### Cron-style job

Use `schedule.add` with `cron` in standard crontab format:

```text
cron="*/5 * * * *"
message="每5分钟巡检一次"
```

### List and remove

- Use `schedule.list` to inspect current-session jobs
- Use `schedule.remove` with the returned job id when the user wants to stop one

## Persistence Verification

Inside the container, the durable file is:

```text
/root/jobs.json
```

On the host, for a given profile, the persisted location is:

```text
/opt/bub/profiles/<profile>/home/jobs.json
```

If the container is recreated against the same profile runtime directory, the scheduler should
reload from that file.

## When Not to Use This Skill

- A shell process outside Bub needs to send a result back into a session
- A host-level scheduled operation should run even when Bub is intentionally stopped
- The trigger source is external and should not depend on the in-process Bub scheduler

In those cases, prefer `http-bridge` plus an external scheduler or use host/Kubernetes scheduling
directly.

---
name: durable-scheduling
description: >
  Use when Bub needs delayed, recurring, or restart-persistent reminders, callbacks, or follow-up
  checks inside a session. Prefer this skill when the user asks about timers, periodic jobs,
  persistent scheduling across container rebuilds, or whether to use bub-schedule versus
  at/cron/systemd.
---

# Durable Scheduling

Use this skill for scheduling work that should run later and come back into a Bub session.

In SelfOps `agents/bub`, prefer the built-in `bub-schedule` plugin before introducing system
scheduler dependencies. The common profiles already persist schedule state through the mounted
profile home directory.

## Decision Rules

- Prefer `bub-schedule` for one-shot delays, periodic reminders, delayed rechecks, and session
  follow-ups.
- Prefer `http-bridge` only when an external process needs to inject a message or report a result
  back into a Bub session.
- Consider `cron`, `at`, or host/system schedulers only when the job must be managed outside Bub,
  must survive Bub being fully down, or must integrate with host-level automation.

## Runtime Model

- `bub-schedule` stores jobs in `/root/jobs.json`.
- In SelfOps, `/root` is backed by `/opt/bub/profiles/<profile>/home`.
- That means scheduled jobs persist across container recreation and image rebuilds for the same
  profile runtime directory.

## What to Use

- `schedule.add`
  Create one-shot, interval, or cron-style jobs for the current session.
- `schedule.list`
  Show current-session jobs.
- `schedule.remove`
  Delete one job by id.
- `schedule.trigger`
  Run one job immediately without removing its schedule.

Read [references/examples.md](references/examples.md) when you need concrete tool patterns,
runtime verification steps, or guidance on when to fall back to OS-level scheduling.

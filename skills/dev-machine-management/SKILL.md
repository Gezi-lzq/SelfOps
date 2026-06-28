---
name: dev-machine-management
description: |
  Use when working on SelfOps development-machine operations: managing global dependencies as dotfile-like state, editing dev/environment/config.toml or bootstrap shell activation, documenting local services under dev/dev-machine, updating machine/gezi-dev from origin/main, committing SelfOps changes, checking branch/ahead status, or explaining how this repository relates to the gezi-dev machine.
---

# Dev Machine Management

## Operating Model

Treat SelfOps as the source of truth for the reproducible state of `gezi-dev`: toolchains, dotfile entry points, local user services, public access routes, agent runtimes, and current-state docs. Prefer declarative repo changes over one-off shell edits.

Use these docs before editing:

- `README.md`: repository map and top-level tasks
- `AGENTS.md`: safety, ownership, and validation rules
- `dev/environment/README.md`: global toolchain and dotfile bootstrap
- `dev/dev-machine/README.md`, `PLAN.md`, `STATE.md`: target machine state and completed changes
- subsystem README files under `dev/dev-machine/**`

## Dependency And Dotfile Workflow

Use `dev/environment/config.toml` for globally managed CLI/tool dependencies. This file is symlinked to `~/.config/mise/config.toml` on the machine.

When adding or changing a global tool:

1. Edit `dev/environment/config.toml`.
2. Keep auth state, API keys, OAuth tokens, and opaque app state out of Git.
3. Verify the live link when relevant:
   ```bash
   readlink -f ~/.config/mise/config.toml
   ```
4. Run focused validation:
   ```bash
   mise install
   mise ls -g
   <tool> --version
   git diff --check
   ```
5. Update `dev/environment/README.md` if the dependency category, bootstrap behavior, or install rule changes.

Dotfile rule: edit the real app config when that app owns it, but record durable machine policy in SelfOps. Examples:

- Claude Code config belongs in `~/.claude/settings.json`.
- The fact that Claude Code is installed by `mise` belongs in `dev/environment/config.toml`.
- If a local-only config becomes part of the machine's expected state, document its path and validation in `dev/dev-machine/STATE.md` without committing secrets.

## Service And Machine-State Workflow

Use `dev/dev-machine` for long-lived local services and machine facts.

When adding or changing a service, port, public route, storage path, systemd unit, or non-mise installer:

1. Decide the owning subsystem. Create a small directory under `dev/dev-machine/<subsystem>/` if no owner exists.
2. Keep templates, install scripts, Caddy routes, and systemd unit templates in the repo.
3. Keep secrets in local files such as `~/.config/selfops/*.env`, never in Git.
4. Apply locally only after reading the subsystem README and checking existing services.
5. Record completed changes in `dev/dev-machine/STATE.md`.
6. Update `dev/dev-machine/PLAN.md` when intended target state changes.

For systemd user units, prefer reproducible install scripts over manual unit creation. If manual creation is unavoidable, document:

- unit name
- ExecStart shape, redacting secrets
- config paths
- listen address/port
- validation commands

## Branch Model

`main` carries shared SelfOps changes. `machine/gezi-dev` carries this machine's applied state and local machine-specific commits.

Before updating or committing:

```bash
git status --short --branch
git fetch origin
git log --oneline --decorate -n 8 --graph HEAD origin/main origin/machine/gezi-dev
```

To update `machine/gezi-dev` from `main`:

1. Preserve unrelated local changes. Use a path-limited stash if needed:
   ```bash
   git stash push -m "wip-before-main-merge" -- <paths>
   ```
2. Merge:
   ```bash
   git merge origin/main
   ```
3. Resolve conflicts by keeping machine-specific state on `machine/gezi-dev` unless `main` intentionally supersedes it.
4. Restore the stash and re-check:
   ```bash
   git stash pop
   git merge-base --is-ancestor origin/main HEAD
   git status --short --branch
   ```

`merge-base --is-ancestor origin/main HEAD` exits `0` when `origin/main` is included in the current branch.

## Commit Workflow

Commit SelfOps changes when they are durable, reproducible, and validated. Keep commits narrow.

Before commit:

```bash
git status --short --branch
git diff --stat
git diff --check
```

Validation by change type:

- Markdown/config-only: `git diff --check`
- Shell scripts: `bash -n <file>` and run the narrow task when safe
- Python: `python3 -m py_compile <files>` plus relevant tests
- `mise` tool changes: `mise install`, `mise ls -g`, and the tool's version/doctor command when safe
- systemd units: `systemctl --user daemon-reload`, targeted status, and endpoint checks when applying locally

Commit with a direct message:

```bash
git add <paths>
git commit -m "<imperative summary>"
```

Do not push unless the user asks.

## Reporting

Report:

- current branch and ahead/behind status
- files changed
- whether `origin/main` is included
- validation run
- secrets/local-only state that was intentionally not committed

Redact service logs and process command lines when they may contain credentials.

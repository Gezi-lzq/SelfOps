---
name: dev-machine-management
description: |
  用于 SelfOps 开发机 / development machine 管理。Use when the user mentions 开发机, SelfOps 开发机, dev machine, gezi-dev, NetBird, SSH 登录开发机, 开发机依赖, dotfile, mise 全局工具, dev/environment/config.toml, dev/dev-machine, machine-name branches, agent-runtime project files, or asks how this repository manages a development machine.
---

# Dev Machine Management

## Operating Model

Treat SelfOps as the source of truth for reproducible development-machine state: toolchains, dotfile entry points, local user services, private access through NetBird, public access routes, agent runtimes, and current-state docs. Prefer declarative repo changes over one-off shell edits.

Use these docs before editing:

- `README.md`: repository map and top-level tasks
- `AGENTS.md`: safety, ownership, and validation rules
- `dev/environment/README.md`: global toolchain and dotfile bootstrap
- `dev/dev-machine/README.md`, `PLAN.md`, `STATE.md`: target machine state and completed changes
- subsystem README files under `dev/dev-machine/**`

## Machine Facts And Access

Read `dev/dev-machine/PLAN.md` for intended machine shape and `dev/dev-machine/STATE.md` for current facts before answering questions about a specific machine.

Default model for SelfOps-managed development machines:

- Use NetBird as the private network for machine-to-machine access.
- Use SSH over the NetBird hostname or SSH alias when available, for example `ssh gezi-dev`.
- Keep SSH private keys, NetBird setup keys, auth tokens, and generated client state out of Git.
- Treat public tunnels as separate from private access. Public browser routes belong under the relevant subsystem, such as `dev/dev-machine/herdr-web`.

For the current `gezi-dev` machine, the expected facts are documented in `dev/dev-machine/STATE.md` and may include:

- default user: `debian`
- SelfOps checkout: `/home/debian/SelfOps`
- NetBird DNS name: `gezi-dev.netbird.cloud`
- private services that bind to `0.0.0.0` only when intended for NetBird access
- public browser entrypoint managed by Caddy plus tunnel services, not by NetBird SSH

When connecting or helping another agent connect:

```bash
ssh gezi-dev
ssh debian@gezi-dev.netbird.cloud
```

If connection fails, check in this order:

```bash
netbird status
ssh -G gezi-dev | sed -n '1,80p'
getent hosts gezi-dev.netbird.cloud
```

Do not publish raw NetBird IPs, private DNS records, process command lines, or service logs if they may reveal credentials. Prefer pointing to `STATE.md` and redacting sensitive values.

## Non-Interactive SSH And Mise

Do not assume `ssh <host> "<command>"` loads `~/.profile`, `~/.zshrc`, or any shell activation. Non-interactive SSH commands should use a deterministic `mise` entrypoint.

For Linux development machines, prefer the machine's recorded absolute path:

```bash
ssh gezi-dev '$HOME/.local/bin/mise -C /home/debian/SelfOps run agent:plan'
```

For macOS development machines using Homebrew, prefer:

```bash
ssh macbook-pro-2.netbird.cloud '/opt/homebrew/bin/mise -C /Users/gezi/Dev/SelfOps run agent:plan'
```

If the remote command needs tools resolved through mise shims, set `PATH` explicitly:

```bash
ssh gezi-dev 'export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"; mise -C /home/debian/SelfOps run agent:plan'
```

Record each development machine's actual `MISE_BIN` and SelfOps checkout path in `dev/dev-machine/STATE.md` or the machine-specific state file. In scripts and handoffs, use:

```bash
MISE_BIN="${MISE_BIN:-$HOME/.local/bin/mise}"
"$MISE_BIN" -C /home/debian/SelfOps run agent:plan
```

Use shell profile activation as convenience for interactive sessions, not as the reliability boundary for remote automation.

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

`main` carries shared SelfOps changes: reusable skills, templates, scripts, docs, and conventions that should apply across machines.

`machine/<name>` branches carry one machine's applied state and local machine-specific commits. For this machine, use `machine/gezi-dev` when it exists.

## Agent Runtime Project Files

Use shared `dev/agent-runtime/registry/skills.toml` for skill catalog and bundles. Use a machine-specific projects file for concrete paths when one exists.

Start new machine files from:

```text
dev/agent-runtime/registry/projects.machine.template.toml
```

Then use the machine file explicitly:

```bash
PROJECTS=/absolute/path/to/dev/agent-runtime/registry/projects.<machine>.toml
mise run agent:scan -- --projects "$PROJECTS"
mise run agent:plan -- --projects "$PROJECTS"
mise run agent:apply -- --projects "$PROJECTS"
```

Do not apply `registry/projects.toml` or another machine's projects file without checking paths and `local_path` sources. Machine branches can carry concrete files such as `projects.gezi-dev.toml`; `main` should carry the shared template and skill catalog.

Before updating or committing:

```bash
git status --short --branch
git fetch origin
git log --oneline --decorate -n 8 --graph HEAD origin/main origin/machine/gezi-dev
```

To update a machine branch from `main`:

1. Preserve unrelated local changes. Use a path-limited stash if needed:
   ```bash
   git stash push -m "wip-before-main-merge" -- <paths>
   ```
2. Merge:
   ```bash
   git merge origin/main
   ```
3. Resolve conflicts by keeping machine-specific state on the machine branch unless `main` intentionally supersedes it.
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

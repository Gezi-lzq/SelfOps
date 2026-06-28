# SelfOps Agent Guide

SelfOps is the source of truth for reproducible development-machine operations: toolchains, dotfile entry points, agent runtimes, local services, access routes, and the documentation that explains them.

This file is the repository-level contract for agents. Keep it identical on `main` and machine branches. Machine-specific facts belong in `dev/dev-machine/PLAN.md`, `dev/dev-machine/STATE.md`, and machine-specific registry files such as `dev/agent-runtime/registry/projects.<machine>.toml`.

## Start Here

Before making changes, inspect the local context:

```bash
git status --short --branch
```

Then read the nearest relevant docs:

- `README.md` for the repository map and top-level tasks.
- `dev/environment/README.md` for global toolchain and dotfile bootstrap behavior.
- `dev/agent-runtime/README.md` for skill catalog and runtime skill distribution.
- `dev/dev-machine/README.md`, `PLAN.md`, and `STATE.md` for the target development machine and current facts.
- The README in the specific subsystem you touch, such as `dev/dev-machine/herdr-web/`, `dev/dev-machine/herdr-status/`, `agents/bub/`, or `infra/runners/`, when it exists on the current branch.

More specific `AGENTS.md` files override this one inside their directory tree.

## Branch Model

- `main` carries shared SelfOps policy: agent rules, reusable skills, templates, scripts, registry conventions, and docs that should apply across machines.
- `machine/<name>` carries one machine's applied state: concrete paths, installed-service records, current access routes, and machine-local project registry files.
- Do not fork `AGENTS.md` between `main` and a machine branch. If this guide needs to change, update `main` and merge it into the machine branch.
- Resolve branch conflicts by keeping shared policy in this file and moving concrete machine facts into `dev/dev-machine/*` or `projects.<machine>.toml`.

## Default Workflow

1. Inspect the worktree and do not overwrite unrelated user or agent changes.
2. Read the docs and files that own the area being changed.
3. Prefer small, declarative repo changes over manual machine edits.
4. If a manual local change is unavoidable, add or update scripts/docs so the next agent can reproduce or verify it.
5. Run focused validation for the touched subsystem plus `git diff --check`.
6. Report changed files, validation results, skipped validation, and remaining risk.

Only push when the user explicitly asks.

Only open, restart, or change public tunnels when the user asked for public-access work, or when the tunnel is already part of the requested operating state.

## Safety Rules

- Never commit or print secrets: tokens, API keys, OAuth credentials, SSH private keys, NetBird setup keys, ngrok authtokens, ttyd basic auth credentials, CLIProxyAPI management secrets, or Nowledge Mem API keys.
- You may verify that secret-bearing files exist and have sane permissions, but do not display their contents.
- Treat process listings, service status, and logs as potentially secret-bearing. Redact command lines before quoting `systemctl --user status`, `ps`, or journal output.
- Avoid destructive commands. Do not run `git reset --hard`, broad `rm -rf`, namespace/PVC/volume deletion, or service data deletion unless the user explicitly asked for that exact destructive action.
- Do not treat local `kubectl`, Docker, or systemd output as customer or production evidence unless the user has identified this machine as the target environment.
- Keep large runtime data out of the system disk. Long-lived service data belongs under the storage paths documented in `dev/dev-machine/PLAN.md`.

## Dependency Ownership

Most development-machine CLI and runtime dependencies are managed through `mise`.

- Global tools belong in `dev/environment/config.toml`.
- Repository tasks belong in root `mise.toml` or the nearest subsystem `mise.toml`.
- Prefer adding a `mise` tool or task over relying on shell aliases, ad hoc global installs, or commands only present in one terminal session.
- After changing `dev/environment/config.toml`, validate the global config in the same shape as bootstrap: ensure `~/.config/mise/config.toml` points to `dev/environment/config.toml`, then run `mise install` and `mise ls -g` from `$HOME`, followed by the relevant tool's `--version` or `doctor` command.
- New machine setup should go through `bash dev/environment/bootstrap.sh ...`, not a parallel hand-written dotfile flow.
- If a dependency cannot reasonably be managed by `mise` and must use apt, an official installer, Docker, Kubernetes, or systemd, document the install method, version, config path, and validation command in the owning README and, when it changes machine state, `dev/dev-machine/STATE.md`.
- Authentication state is not dependency state. Tools such as `gh`, `lark-cli`, `lody`, Codex, Claude Code, ngrok, cloudflared, NetBird, and Nowledge Mem may have their configured status recorded, but secrets stay local.

## Dotfiles And Local State

SelfOps owns reproducible dotfile entry points for development machines. It does not own private credentials or opaque application state.

SelfOps-managed or SelfOps-generated:

- `dev/environment/config.toml`: source of truth for global `mise` tools.
- `~/.config/mise/config.toml`: should symlink to `dev/environment/config.toml` via `dev/environment/bootstrap.sh`.
- `~/.profile`: may contain the SelfOps-managed `mise activate bash --shims` block for SSH, login, and non-interactive shells.
- `~/.zshrc`: may receive `mise activate zsh` from `bootstrap.sh --activate-zsh`.
- `~/.bashrc`: may receive `mise activate bash` from `bootstrap.sh --activate-bash`.
- Root and subsystem `mise.toml` files: task entry points for repeatable operations.
- User systemd unit templates under `dev/dev-machine/**/systemd/`, installed into user systemd config by subsystem install scripts.

Local-only state that must not be copied into the repo:

- `~/.config/selfops/*.env`
- `~/.nowledge-mem/config.json`
- `~/.codex/config.toml` and `~/.codex/hooks.json` contents
- `~/.claude/settings.json` contents when they contain local provider credentials or personal app state
- `~/.ssh/*`
- Personal identity, signing key, and credential helper details from `~/.gitconfig`
- Login state for `gh`, `lark-cli`, `lody`, Codex, Claude Code, ngrok, cloudflared, NetBird, and similar tools
- CLIProxyAPI, ttyd, ngrok, Nowledge Mem, and OAuth secrets

When changing dotfile behavior, update `dev/environment/bootstrap.sh`, `dev/environment/config.toml`, or `dev/environment/README.md` first. Direct edits under `$HOME` should be reflected back into the repo as scripts or docs.

Useful checks:

```bash
readlink -f ~/.config/mise/config.toml
rg -n "SelfOps managed mise shims|mise activate" ~/.profile ~/.zshrc ~/.bashrc
mise ls -g
```

## Development-Machine Access

Treat NetBird as the default private access plane for SelfOps-managed development machines. Use SSH aliases or NetBird DNS names documented in `dev/dev-machine/STATE.md`; do not hardcode unstable private IPs into reusable docs or skills.

Public browser access is separate from private SSH access. Public routes belong under their owning subsystem, for example `dev/dev-machine/herdr-web/` when present. Keep backends localhost-only unless a doc explains otherwise.

Before exposing a new local service:

1. Decide whether it is private NetBird-only or public tunnel-backed.
2. Document ports, bind addresses, auth, and validation commands.
3. Keep credentials in local env files or secret stores, not Git.
4. Update `dev/dev-machine/PLAN.md` for intended state and `STATE.md` after applying.

## Subsystem Ownership

`dev/environment/`

- Owns global toolchain versions, shell activation guidance, and new-machine bootstrap.
- Prefer `mise` for tools unless there is a documented reason not to.

`dev/agent-runtime/`

- Owns declared agent skill sources and project skill distribution.
- Use `mise run agent:scan`, `mise run agent:plan`, and `mise run agent:apply` from the repo root.
- Keep shared skill catalog and bundles in `registry/skills.toml`.
- Keep machine-specific paths in `registry/projects.<machine>.toml`, usually on a machine branch, starting from `registry/projects.machine.template.toml`.
- If nested mise configs are untrusted, trust the exact file before running delegated tasks: `mise trust dev/agent-runtime/mise.toml`.

`dev/dev-machine/`

- Owns development-machine target and current state.
- `PLAN.md` records intended state.
- `STATE.md` records completed changes and current facts.
- Any change to intended services, ports, paths, access model, storage layout, or dependency policy should update `PLAN.md`.
- Any completed change to services, ports, paths, systemd units, Caddy routes, tunnels, storage locations, or installed non-mise dependencies should update the relevant README and `STATE.md`.

`dev/dev-machine/herdr-web/`

- Owns the public browser entrypoint when present.
- Caddy routes, tunnel commands, ttyd settings, and public route security belong here.
- ttyd must keep authentication, and credentials must stay out of the repo.
- Public routes are internet-exposed. Avoid exposing sensitive pane output, env vars, tokens, customer data, or private prompts.
- Start commands may open public tunnels. Run them only for requested public-entrypoint work or to restore documented current state.
- When showing status or logs, summarize and redact.

`dev/dev-machine/herdr-status/`

- Owns the read-only Herdr mobile status and history UI when present.
- It may show session, pane, agent status, and history links.
- It must not implement arbitrary shell input or arbitrary command execution.
- Terminal links should pass only controlled allowlisted arguments such as `--session` and `--agent`.

`agents/bub/`

- Owns Bub deployment, profile isolation, plugin source, and tape backup workflow.
- Profile-specific behavior belongs in `agents/bub/profiles/<profile>/AGENTS.md`.
- New profiles should include `AGENTS.md`, `bub-reqs.txt`, `env.template`, `projects.toml`, and `startup.sh`.
- Secrets are rendered into profile env files, not committed.
- If nested mise configs are untrusted, trust the exact file first: `mise trust agents/bub/mise.toml`.
- `bub:backup` uploads Bub tapes to GitHub Releases without redaction. Run it only when the user asked for a backup or the workflow requires it, and treat tapes as potentially containing sensitive agent conversation history.

`infra/runners/`

- Owns self-hosted GitHub Actions runner declarations.
- Do not run runner ensure/remove commands on the wrong machine. Confirm the target host before applying.
- Keep GitHub tokens and runner registration/remove tokens outside Git.

`infra/observability/`

- Owns local observability stack declarations.
- Keep credentials and provider tokens outside Git.

## Common Commands

Toolchain:

```bash
mise trust
mise install
mise run doctor
```

Nested task files may need explicit trust before first use:

```bash
mise trust dev/agent-runtime/mise.toml
mise trust agents/bub/mise.toml
```

Agent runtime:

```bash
mise run agent:scan
mise run agent:plan
mise run agent:apply
```

Herdr public entry, when present:

```bash
mise run herdr-web:status
mise run herdr-web:start
mise run herdr-web:url
mise run herdr-web:logs
```

Use public-entry commands with the security rules above: start commands may open public tunnels, and status/log output must be summarized or redacted.

Bub profiles:

```bash
mise -C agents/bub run bub:deploy <profile>
mise -C agents/bub run bub:write-env <profile>
mise -C agents/bub run bub:backup <profile>
```

## Validation Matrix

- Markdown/config-only change: `git diff --check`.
- Python change: `python3 -m py_compile <changed .py files>` plus any relevant tests.
- Shell script change: `bash -n <changed .sh files>` and run the narrow task when safe.
- `mise` task change: trust the relevant `mise.toml` if needed, then run `mise tasks` or the relevant `mise run ...`.
- Global `mise` tool change: verify `~/.config/mise/config.toml` points to `dev/environment/config.toml`, then run `mise install` and `mise ls -g` from `$HOME`, plus version checks when safe.
- Caddy route change: `caddy validate --config <Caddyfile> --adapter caddyfile`, then restart the owning proxy service only when applying locally is intended.
- Herdr web/status change: validate Python/Caddy as applicable and check local HTTP endpoints on `127.0.0.1`.
- systemd user unit change: run the install script or inspect generated units, then `systemctl --user daemon-reload` and targeted `systemctl --user status ...` when applying locally. Summarize status output and redact command lines.

Before finishing, show the meaningful outcome: what changed, what was validated, what was not validated, and whether the worktree still has uncommitted changes.

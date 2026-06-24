# SelfOps Agent Guide

SelfOps is the source of truth for this development machine's reproducible operational state: toolchains, dotfile entry points, agent runtimes, local services, public access routes, and the documentation that explains them.

The goal is not to make one-off fixes. When you change the machine, make the change reproducible from this repository or document why it must remain local state.

## Start Here

Before making changes, read the nearest relevant docs:

- `README.md` for the repository map and top-level `mise` tasks.
- `dev/environment/README.md` for global toolchain and dotfile bootstrap behavior.
- `dev/dev-machine/README.md`, `dev/dev-machine/PLAN.md`, and `dev/dev-machine/STATE.md` for the `gezi-dev` target and current state.
- The README in the specific subsystem you touch, such as `dev/dev-machine/herdr-web/`, `dev/dev-machine/herdr-status/`, `dev/agent-runtime/`, `agents/bub/`, or `infra/runners/`.

More specific instructions override this file. In particular, `agents/bub/profiles/<profile>/AGENTS.md` controls behavior inside that Bub profile.

## Default Workflow

1. Inspect `git status --short --branch` and do not overwrite unrelated user or agent changes.
2. Read the docs and local files that own the area being changed.
3. Prefer small, declarative changes in this repo over manual machine edits.
4. If a manual local change is unavoidable, update scripts or docs so the next agent can reproduce or verify it.
5. Run focused validation for the touched subsystem plus `git diff --check`.
6. Report changed files, validation results, and any remaining risk.

Only push when the user explicitly asks.
Only open or restart public tunnels when the user asked for public access work, or when the tunnel is already part of the requested operating state.

## Safety Rules

- Never commit or print secrets: tokens, API keys, OAuth credentials, SSH private keys, ngrok authtokens, ttyd basic auth credentials, CLIProxyAPI management secrets, or Nowledge Mem API keys.
- You may verify that secret-bearing files exist and have sane permissions, but do not display their contents.
- Treat process listings, service status, and logs as potentially secret-bearing. ttyd receives basic auth through a process argument on this machine, so redact command lines before quoting `systemctl --user status`, `ps`, or journal output.
- Avoid destructive commands. Do not run `git reset --hard`, `git checkout -- <file>`, broad `rm -rf`, namespace/PVC/volume deletion, or service data deletion unless the user explicitly asked for that exact destructive action.
- Do not treat local `kubectl`, Docker, or systemd output as customer or production evidence unless the user has identified this machine as the target environment.
- Keep large runtime data out of the system disk. Long-lived service data belongs under `/data` according to `dev/dev-machine/PLAN.md`.

## Dependency Ownership

Most development-machine CLI and runtime dependencies are managed by SelfOps through `mise`.

- Global tools belong in `dev/environment/config.toml`.
- Repository tasks belong in root `mise.toml` or the nearest subsystem `mise.toml`.
- Prefer adding a `mise` tool or task over relying on shell aliases, ad hoc global installs, or commands only present in one terminal session.
- After changing `dev/environment/config.toml`, validate the global config in the same shape as bootstrap: ensure `~/.config/mise/config.toml` points to `dev/environment/config.toml`, then run `mise install` and `mise ls -g` from `$HOME`, followed by the relevant tool's `--version` or `doctor` command.
- New machine setup should go through `bash dev/environment/bootstrap.sh ...`, not a parallel hand-written dotfile flow.
- If a dependency cannot reasonably be managed by `mise` and must use apt, an official installer, Docker, Kubernetes, or systemd, document the install method, version, config path, and validation command in the owning README and, when it changes machine state, `dev/dev-machine/STATE.md`.
- Authentication state is not dependency state. Tools such as `gh`, `lark-cli`, `lody`, Codex, ngrok, cloudflared, and Nowledge Mem may have their configured status recorded, but secrets stay local.

## Dotfiles And Local State

SelfOps owns reproducible dotfile entry points for the current development machine. It does not own private credentials or opaque application state.

SelfOps-managed or SelfOps-generated:

- `dev/environment/config.toml`: source of truth for global `mise` tools.
- `~/.config/mise/config.toml`: should symlink to `dev/environment/config.toml` via `dev/environment/bootstrap.sh`.
- `~/.profile`: may contain the SelfOps managed `mise activate bash --shims` block for SSH, login, and non-interactive shells.
- `~/.zshrc`: may receive `mise activate zsh` from `bootstrap.sh --activate-zsh`.
- `~/.bashrc`: may receive `mise activate bash` from `bootstrap.sh --activate-bash`.
- Root and subsystem `mise.toml` files: task entry points for repeatable operations.
- User systemd unit templates under `dev/dev-machine/**/systemd/`, installed into the user systemd config by the subsystem install scripts.

Local-only state that must not be copied into the repo:

- `~/.config/selfops/*.env`
- `~/.nowledge-mem/config.json`
- `~/.codex/config.toml` and `~/.codex/hooks.json` contents
- `~/.ssh/*`
- Personal identity, signing key, and credential helper details from `~/.gitconfig`
- Login state for `gh`, `lark-cli`, `lody`, Codex, ngrok, cloudflared, and similar tools
- CLIProxyAPI, ttyd, ngrok, Nowledge Mem, and OAuth secrets

When changing dotfile behavior, update `dev/environment/bootstrap.sh`, `dev/environment/config.toml`, or `dev/environment/README.md` first. Direct edits under `$HOME` should be reflected back into the repo as scripts or docs.

Useful checks:

```bash
readlink -f ~/.config/mise/config.toml
rg -n "SelfOps managed mise shims|mise activate" ~/.profile ~/.zshrc ~/.bashrc
mise ls -g
```

## Subsystem Ownership

`dev/environment/`

- Owns global toolchain versions, shell activation guidance, and new-machine bootstrap.
- Prefer `mise` for tools unless there is a documented reason not to.

`dev/agent-runtime/`

- Owns declared agent skill sources and project skill distribution.
- Use `mise run agent:scan`, `mise run agent:plan`, and `mise run agent:apply` from the repo root.
- If nested mise configs are untrusted, trust the exact file before running delegated tasks: `mise trust dev/agent-runtime/mise.toml`.

`dev/dev-machine/`

- Owns `gezi-dev` target and current machine state.
- `PLAN.md` records intended state.
- `STATE.md` records completed changes and current facts.
- Any change to intended services, ports, paths, access model, storage layout, or dependency policy should update `PLAN.md`.
- Any completed change to services, ports, paths, systemd units, Caddy routes, tunnels, storage locations, or installed non-mise dependencies should update the relevant README and `STATE.md`.

`dev/dev-machine/herdr-web/`

- Owns the public browser entrypoint: `ngrok -> 127.0.0.1:8780 Caddy router -> localhost services`.
- Caddy config is `dev/dev-machine/herdr-web/Caddyfile`.
- Keep backends localhost-only unless a doc explains otherwise.
- `/` is a lightweight homepage. `/herdr/...` is the Herdr namespace.
- Do not expose Nowledge Mem API, MCP, or UI through ngrok, cloudflared, or Caddy unless the user explicitly asks and access control is documented. It also should not be exposed under a Caddy subpath because its frontend uses absolute `/app/assets` paths and is not stable behind a prefixed public path.
- ttyd must keep basic auth, and credentials must stay out of the repo.
- Public routes are internet-exposed. The status and history routes currently do not add a second auth layer, so avoid exposing sensitive pane output there.
- `mise run herdr-web:start`, `mise run herdr-web:start-cloudflared`, and direct starts of `herdr-web-ngrok.service` / `herdr-web-cloudflared.service` open public access. Run them only for public-entrypoint work requested by the user or to restore the documented current state.
- When showing status or logs, summarize and redact. Do not paste raw ttyd command lines because they may include the basic auth credential.

`dev/dev-machine/herdr-status/`

- Owns the read-only Herdr mobile status and history UI.
- It may show session, pane, agent status, and history links.
- History renders recent pane output as HTML and may be reachable through the public router. Treat pane history as potentially sensitive, especially if terminals may print env vars, tokens, customer data, or private prompts.
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

- Owns self-hosted GitHub Actions runner declarations for the target host documented in `infra/runners/README.md`, currently not `gezi-dev`.
- Do not run runner ensure/remove commands on the wrong machine. Confirm the target host before applying.
- Keep GitHub tokens and runner registration/remove tokens outside Git.

`infra/observability/`

- Owns the local observability stack declarations.
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

Herdr public entry:

```bash
mise run herdr-web:status
mise run herdr-web:start
mise run herdr-web:url
mise run herdr-web:logs
```

Use the Herdr public-entry commands with the security rules above: start commands open public tunnels, and status/log output must be summarized or redacted.

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
- Caddy route change: `caddy validate --config dev/dev-machine/herdr-web/Caddyfile --adapter caddyfile`, then restart `herdr-web-proxy.service` if applying locally. Restarting the proxy changes the public router behavior when a tunnel is active.
- Herdr web/status change: validate Python/Caddy as applicable and check local HTTP endpoints on `127.0.0.1`.
- systemd user unit change: run the install script or inspect generated units, then `systemctl --user daemon-reload` and targeted `systemctl --user status ...` when applying locally. Summarize status output and redact command lines.

Before finishing, show the user the meaningful outcome: what changed, what was validated, what was not validated, and whether the worktree still has uncommitted changes.

---
name: skill-management
description: |
  Use when managing SelfOps skills: auditing runtime skill state, adding or updating public skills, creating SelfOps-owned skills under the repository root skills/ directory, editing dev/agent-runtime/registry/skills.toml or registry/projects.toml, reconciling symlinks, or explaining how local skills are maintained.
---

# Skill Management

## Overview

Use the repository root `skills/` directory as the source location for SelfOps-owned skills. Use SelfOps Agent Runtime to distribute those skills into local agent runtime directories. Do not manually edit generated runtime skill directories unless debugging; update the Git registry and reconcile from there.

## Mental Model

SelfOps maintains three layers:

- Source state: `skills/<name>/` for SelfOps-owned skills
- Desired state: `dev/agent-runtime/registry/skills.toml` and `dev/agent-runtime/registry/projects.toml`
- Cache state: `dev/agent-runtime/.agents/skills/` for `public`; `dev/agent-runtime/materialized/skills/` for external `local_path` copies
- Runtime state: agent directories such as `~/.codex/skills`, `~/.claude/skills`, and project-local `.<agent>/skills`

Runtime entries are generated symlinks. Treat them as disposable output from `agent_runtime.py apply`.

## Core Commands

Run from `/Users/gezi/Dev/SelfOps/dev/agent-runtime` unless using an absolute path:

```bash
mise run agent:scan
mise run agent:plan
mise run agent:apply
mise run agent:apply -- --force
mise run agent:update
```

Use `scan` for observation, `plan` before making changes, `apply` for non-destructive reconciliation, and `apply --force` only when the plan's destructive actions are intended.

## Skill Sources

Choose one source type per skill in `registry/skills.toml`:

- `public`: fetched by `npx skills add <spec>` into `dev/agent-runtime/.agents/skills/<name>`
- `owned`: maintained directly in this repo, usually under `skills/<name>` with `materialized_path = "../../skills/<name>"` because paths are resolved from `dev/agent-runtime`
- `local_path`: copied from a local source path into `materialized/skills/<name>`

Use `owned` for local operating procedures and durable personal workflows. Use `public` for upstream skills that should track their repository's latest version unless a concrete pinning reason exists.

## Common Workflows

### Audit Current State

1. Read `dev/agent-runtime/README.md`.
2. Run `mise run agent:scan`.
3. Run `mise run agent:plan`.
4. Explain differences as desired state vs generated runtime state.

### Add Or Update A Public Skill

1. Confirm the upstream repository and available skill names with `npx skills add <repo> --list --full-depth`.
2. Add or update `[skills.<name>] source = { type = "public", spec = "<repo>" }` in `registry/skills.toml`.
3. Add the skill to a bundle or to a project's `include` list in `registry/projects.toml`.
4. Run `mise run agent:plan`.
5. Run `mise run agent:apply`.
6. If the public skill already exists and must be refreshed, run `mise run agent:update` or `npx skills update <skill> -p -y`.

### Create An Owned Skill

1. Initialize or create the skill under `skills/<name>/`.
2. Keep `SKILL.md` concise and focused on instructions another agent needs.
3. Register it in `registry/skills.toml` with `source = { type = "owned" }` and `materialized_path = "../../skills/<name>"`.
4. Add it to `@global.include`, a bundle, or a specific project include list.
5. Validate with the system skill validator if available.
6. Run `mise run agent:plan` and `mise run agent:apply`.

### Update Upstream Skills

Prefer tracking upstream latest for general public skills. For release-sensitive work, explicitly verify GitHub releases or tags before changing specs.

For `mattpocock/skills`, use:

```bash
npx skills add mattpocock/skills --list --full-depth
```

Then make `registry/skills.toml` match the discovered skill names used by the `mattpocock` bundle.

## Guardrails

- Do not edit `~/.codex/skills` or other runtime targets as source of truth.
- Do not delete unrelated untracked files while reconciling.
- Check `git status --short` before and after edits.
- If `plan` shows `remove_path`, `replace_path`, or `update_link`, inspect before using `--force`.
- Restart affected agents after skill changes so new skill metadata is picked up.

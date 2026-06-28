---
name: skill-management
description: |
  Manage SelfOps skills and agent-runtime desired state. Use when auditing skill state, adding or updating public skills, creating SelfOps-owned skills under the repository root skills/ directory, editing dev/agent-runtime/registry/skills.toml or registry/projects.toml, reconciling global or project skill symlinks, handling stale public skill caches, or explaining how local skills are maintained.
---

# Skill Management

## Operating Model

Treat the Git registry as desired state and runtime skill directories as generated output.

- Source state: `skills/<name>/` for SelfOps-owned skills.
- Desired state: `dev/agent-runtime/registry/skills.toml` and `dev/agent-runtime/registry/projects.toml`.
- Cache state: `dev/agent-runtime/.agents/skills/` for `public`; `dev/agent-runtime/materialized/skills/` for `local_path` and generated local copies.
- Runtime state: symlinks in `~/.codex/skills`, `~/.claude/skills`, `~/.kiro/skills`, `~/.agents/skills`, and project-local `.<agent>/skills`.

Do not manually edit runtime directories as source of truth. Change registry/source files, then reconcile.

## Core Commands

Run from `/Users/gezi/Dev/SelfOps/dev/agent-runtime`:

```bash
mise run agent:scan
mise run agent:plan
mise run agent:apply
mise run agent:apply -- --force
mise run agent:update
```

From another working directory, use:

```bash
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:scan
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:plan
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:apply
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:update
```

Use `scan` for observation, `plan` before changing runtime state, `apply` for non-destructive reconciliation, and `apply --force` only after inspecting intended destructive actions.

## Source Types

Choose one source type per skill:

- `public`: fetched by `npx skills add <spec>` into `dev/agent-runtime/.agents/skills/<name>`
- `owned`: maintained directly in this repo, usually under `skills/<name>` with `materialized_path = "../../skills/<name>"`
- `local_path`: copied from a local source path into `materialized/skills/<name>`

Use `owned` for local operating procedures and durable personal workflows. Use `public` for upstream skills that should track their repository's latest version unless a concrete pinning reason exists.

## Workflow: Audit State

1. Read `dev/agent-runtime/README.md` if the runtime model is unclear.
2. Run `mise run agent:scan`.
3. Run `mise run agent:plan`.
4. Interpret differences as desired state versus generated runtime state.

## Workflow: Add A Public Skill

1. Confirm upstream names with `npx skills add <repo> --list --full-depth`.
2. Add or update `[skills.<name>] source = { type = "public", spec = "<repo>" }` in `registry/skills.toml`.
3. Add the skill to a bundle or project `include` list in `registry/projects.toml`.
4. Run `mise run agent:plan`.
5. Run `mise run agent:apply`.

## Workflow: Create An Owned Skill

1. Create the skill under `skills/<name>/`.
2. Keep `SKILL.md` focused on procedures another agent needs.
3. Register it in `registry/skills.toml` with `source = { type = "owned" }` and `materialized_path = "../../skills/<name>"`.
4. Add it to `@global.include`, a bundle, or a project include list.
5. Validate with the system skill validator when available.
6. Run `mise run agent:plan`.
7. Run `mise run agent:apply`.

## Workflow: Update Public Skills

Prefer tracking upstream latest for general public skills. For release-sensitive work, explicitly verify GitHub releases or tags before changing specs.

First refresh the public cache:

```bash
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:update
```

Then inspect convergence:

```bash
mise -C /Users/gezi/Dev/SelfOps/dev/agent-runtime run agent:plan
```

Evaluate update failures by layer:

- Desired state: is the skill declared in `skills.toml` and included by `projects.toml`?
- Runtime state: do agent runtime directories still link to it?
- Cache state: does `dev/agent-runtime/.agents/skills/<name>` only contain an old downloaded copy?

Use these rules:

- If update fails for a skill that is no longer desired and no runtime directory links to it, treat it as stale cache. It does not affect active agent startup.
- If update fails for a skill still in desired state, verify upstream with `npx skills add <repo> --list --full-depth`. If upstream no longer provides it, remove it from bundles/includes and usually remove its `[skills.<name>]` entry.
- If a public skill predates `skillPath` tracking and cannot update automatically, refresh its source repo with `npx skills add <repo> -y` when that source is still desired.

## Workflow: Clean Stale Runtime Links

Use `apply --force` only for destructive actions you intend.

When only global runtime should change, create a temporary projects file containing only `@global`, run `plan --projects <absolute-path>`, then run `apply --force --projects <absolute-path>` if the plan is correct. Delete the temporary file afterward.

Do not clean project-level runtime skills unless project-level management is explicitly in scope.

## Upstream Checks

For `mattpocock/skills`:

```bash
npx skills add mattpocock/skills --list --full-depth
```

For `larksuite/cli`:

```bash
npx skills add larksuite/cli --list --full-depth
```

Make `registry/skills.toml` and bundles match discovered skill names. Remove unavailable skill entries when no desired state uses them.

## Guardrails

- Do not edit runtime skill directories as source of truth.
- Do not delete unrelated untracked files while reconciling.
- Check `git status --short` before and after edits.
- Inspect `remove_path`, `replace_path`, and `update_link` before using `--force`.
- Restart affected agents after skill changes so new skill metadata is picked up.

---
name: cmux-multi-agent
description: Use when coordinating interactive CLI workers through cmux workspaces, especially when tasks need clear handoff files, stable command-injected startup, independent user follow-up, and durable result records.
---

# cmux Multi-Agent Orchestration

Use cmux as the terminal orchestration layer for delegating work to multiple CLI workers. Treat this skill as the starting point for arranging work: split tasks, write clear handoff files, open worker workspaces with the handoff injected in the startup command, and leave the worker available for interactive follow-up.

This skill currently supports:

- Claude workers: `claude --dangerously-skip-permissions`
- Codex workers: `codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search`

Do not design around permissions here. The worker command already encodes the intended execution mode.

## Core Model

Controller:
- The current agent session.
- Owns task decomposition, handoff quality, command-injected worker launch, dispatch records, and any final review requested by the user.
- Does not drive worker progress through repeated terminal input.
- Does not assume workers will callback.

Worker:
- A CLI agent running in a cmux workspace.
- Receives one bounded task through its startup prompt.
- Remains interactive so the user can continue requirement confirmation or execution discussion directly in the worker workspace.
- Writes durable output files that the Controller can read later.
- May callback if instructed, but callback is optional and must not be the only completion signal.

cmux workspace:
- The default isolation unit for a worker.
- Created with `cmux new-workspace`.
- Launched with a full worker command that includes the handoff prompt path.
- Read with `cmux read-screen` only for smoke checks or failure diagnosis.
- Written to with `cmux send` plus `cmux send-key` only as a fallback for an already-running workspace, not as the normal dispatch path.

## When To Use

Use this skill when:

- You need to split one larger goal into independent worker tasks.
- You want workers to run in visible cmux workspaces.
- You need a durable handoff file instead of a fragile chat-only prompt.
- You need the user to continue interacting with a downstream agent after the Controller prepares context.
- You want stable startup that avoids waiting for CLI readiness and simulating typed input.
- You want Claude and Codex workers available as execution choices.

Do not use this skill when:

- The next step is sequential and blocks on one local decision.
- Tasks will edit the same files without a clear owner.
- A direct local command or one local edit is faster than delegation.

## Worker Selection

Choose one worker per task.

| Worker | Use For | Launch Command |
|---|---|---|
| Claude | Broad implementation, refactoring, prose-heavy reasoning, tasks that benefit from long-form planning | `claude --dangerously-skip-permissions "{startup prompt}"` |
| Codex | Codebase editing, command-heavy verification, search-heavy investigation, tasks where Codex tooling is useful | `codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search --cd /path/to/repo "{startup prompt}"` |

Keep the Controller responsible for task boundaries. Do not ask multiple workers to decide ownership among themselves.

## Task Handoff

Create a `.tasks/` directory in the project root or another explicit task directory:

```text
.tasks/
  20260513-183000-cmux-plan.md
  20260513-183015-worker-a.prompt.md
  20260513-183015-worker-a.result.md
  20260513-183015-worker-a.notes.md
  20260513-183015-worker-a.done
```

Name each task file with a timestamped task id: `{YYYYMMDD-HHMMSS}-{task-slug}`. Use the same task id prefix for the prompt, result, notes, and done files. The timestamp is mandatory because worker tasks are often repeated with similar names across multiple orchestration rounds.

Every worker prompt must be self-contained enough to execute after launch. Include:

- Goal: what the worker must accomplish.
- Mode: whether the worker should execute immediately or first continue requirement confirmation with the user.
- Context: files, commands, docs, and assumptions already known.
- Ownership: files or areas the worker may modify, and areas it must not touch.
- Constraints: coding style, risk boundaries, and anything the Controller already decided.
- Communication language: usually Chinese unless the user explicitly requested another language.
- Output contract: exact result file path and expected contents.
- Verification: commands to run, or explicit reason no verification is expected.
- Stop conditions: when to stop and report ambiguity instead of guessing.

Do not overload the worker with the Controller's entire reasoning trace. Give enough context to prevent wasted search, while preserving the worker's freedom to choose its own execution path.

## Prompt Template

Use this structure for each `{YYYYMMDD-HHMMSS}-{task-slug}.prompt.md`:

```markdown
# Worker Task: {short-title}

## Goal
{One precise outcome.}

## Context
- Repository: `{repo-path}`
- Current branch/state: {known state if relevant}
- Communication: Use Chinese when communicating with the user unless the user explicitly requested another language.
- Required reading:
  - `{path}`
  - `{path}`
- Useful commands:
  - `{command}`

## Mode
{One of: `confirm-first`, `execute-after-confirmation`, `execute-now`.}

If mode is `confirm-first`, start by restating your understanding in Chinese and ask the user only for the missing details needed for the next step. Do not mark the task done merely because more user input is needed.

## Ownership
You own:
- `{path-or-area}`

Do not modify:
- `{path-or-area}`

Coordinate by result file only. Do not assume other workers will read your workspace.

## Execution Guidance
Choose your own investigation and implementation order.
Prefer small, focused edits.
If the task definition conflicts with the codebase, stop and explain the conflict in the result file.
Do not revert unrelated user or worker changes.

## Output Contract
Write your final result to:
`{tasks-dir}/{YYYYMMDD-HHMMSS}-{task-slug}.result.md`

The result must include:
- Summary of what you did or found.
- Files changed, if any.
- Verification run and outcomes.
- Open risks or follow-up required.

When finished, also create:
`{tasks-dir}/{YYYYMMDD-HHMMSS}-{task-slug}.done`

Callback to Controller is optional. The durable files are the source of truth.
```

## Controller Workflow

1. Identify current cmux context:

```bash
cmux identify --json
```

2. Create task prompt files before launching workers.

3. Launch one cmux workspace per worker with the handoff path injected directly in the startup command.

For Codex:

```bash
cmux new-workspace \
  --name "worker-b" \
  --cwd /path/to/repo \
  --command "codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search --cd /path/to/repo 'Use Chinese when communicating with the user. Read /absolute/path/.tasks/20260513-183015-worker-b.prompt.md and follow it exactly. Start by restating your understanding and continue with the mode specified in the prompt.'"
```

For Claude:

```bash
cmux new-workspace \
  --name "worker-a" \
  --cwd /path/to/repo \
  --command "claude --dangerously-skip-permissions 'Use Chinese when communicating with the user. Read /absolute/path/.tasks/20260513-183015-worker-a.prompt.md and follow it exactly. Start by restating your understanding and continue with the mode specified in the prompt.'"
```

4. Capture the returned `workspace:N` ref and record it in the dispatch log.

5. Stop. The worker is now an interactive downstream agent. The user can switch to the workspace and continue the conversation directly.

The normal dispatch path must not rely on:

```bash
cmux send --workspace workspace:N "..."
cmux send-key --workspace workspace:N Enter
```

Use those commands only for fallback recovery of an already-running workspace.

6. Optional smoke check: if needed, inspect the screen once to confirm the process started and the startup prompt is visible.

```bash
cmux read-screen --workspace workspace:N --scrollback --lines 80
```

This check is diagnostic. It is not the dispatch mechanism.

7. When the user later asks for review or integration, read the worker result files and inspect the workspace as needed.

## Monitoring

Use durable files and dispatch records first. Do not rely on callback or continuous screen polling.

```bash
cmux tree --workspace workspace:N
test -f .tasks/20260513-183015-worker-a.done
test -f .tasks/20260513-183015-worker-a.result.md
```

Interpretation:

| Signal | Meaning | Controller Action |
|---|---|---|
| Workspace was created and process is running | Startup command was accepted | Record workspace ref and let the user continue with the worker |
| Startup prompt is visible in the worker session | Handoff was injected at launch | No `cmux send` is needed |
| CLI prompt is ready but no startup prompt appears | Worker command may have been malformed | Relaunch with a corrected `--command`; do not keep trying typed handoff first |
| Worker is reading files/running commands | Worker is active | Leave it running unless blocked too long |
| Approval/prompt/login UI appears | Worker is blocked | Decide whether to interact, relaunch, or take over locally |
| `.done` exists and result file exists | Worker has completed its contract | Review output and changes |
| Worker says done but result file is missing | Completion is not durable | Ask worker to write the result file or reconstruct from screen |

## Handoff Quality Rules

- Give each worker one clear task.
- Give each worker a disjoint ownership boundary.
- Prefer file paths and commands over vague module names.
- Tell workers where to write results before they begin.
- Inject the handoff prompt path in the worker startup command.
- Keep the worker interactive for user follow-up unless the user explicitly asks for a background-only task.
- Make the result file the authoritative completion record.
- Keep callback optional.
- Keep Controller integration local; workers should not merge each other's changes.

## Failure Recovery

If a worker never starts:
- Read its screen.
- Confirm the workspace ref is correct.
- Confirm the startup command contains the absolute prompt path.
- Relaunch with a clearer command.

If a worker is blocked:
- Determine whether the block is login/auth, malformed startup command, command failure, or task ambiguity.
- If the block is task ambiguity, update the prompt file and ask the user to continue directly in the worker workspace, or relaunch if the initial context was materially wrong.

If the startup command failed to inject the prompt:
- Prefer relaunching the workspace with a corrected `--command`.
- Use `cmux send` / `cmux send-key` only as a one-off recovery if relaunching would lose useful ongoing conversation.

If a worker modifies out-of-scope files:
- Do not blindly revert.
- Inspect the diff.
- Keep useful changes only if they do not conflict with ownership.
- Record the scope violation in Controller notes so future handoffs are tighter.

If multiple workers conflict:
- Stop assigning new work in the conflicting area.
- Review both result files.
- Integrate manually from the Controller session.

## Useful cmux Commands

| Command | Purpose |
|---|---|
| `cmux identify --json` | Identify current workspace and surface |
| `cmux new-workspace --name X --cwd Y --command Z` | Launch an interactive worker workspace with the handoff injected in `Z` |
| `cmux read-screen --workspace W --scrollback --lines N` | Inspect worker terminal output for diagnostics |
| `cmux send --workspace W "text"` | Fallback only: type text into an already-running terminal |
| `cmux send-key --workspace W Enter` | Fallback only: submit typed text |
| `cmux tree --workspace W` | Inspect panes and surfaces when targeting is unclear |
| `cmux select-workspace --workspace W` | Focus a worker workspace |
| `cmux close-workspace --workspace W` | Close a completed or abandoned worker workspace |
| `cmux list-workspaces` | List active workspaces |

## Common Mistakes

- Launching workers before writing prompt files.
- Starting an empty interactive CLI and then trying to inject the task with `cmux send`.
- Sending a long task directly through `cmux send` instead of injecting a handoff file path in the startup command.
- Treating screen polling as the dispatch mechanism instead of a diagnostic fallback.
- Treating callback as required for completion.
- Giving two workers overlapping edit ownership.
- Asking workers to coordinate with each other instead of reporting back to Controller-owned result files.
- Forgetting that the Controller must review worker output before claiming the larger task is complete.

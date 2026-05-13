---
name: cmux-multi-agent
description: Use when coordinating multiple CLI workers through cmux workspaces, especially when tasks need clear handoff files, independent execution, screen monitoring, and later controller review.
---

# cmux Multi-Agent Orchestration

Use cmux as the terminal orchestration layer for delegating work to multiple CLI workers. Treat this skill as the starting point for arranging work: split tasks, open worker workspaces, hand off instructions clearly, monitor progress, and integrate results.

This skill currently supports:

- Claude workers: `claude --dangerously-skip-permissions`
- Codex workers: `codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search`

Do not design around permissions here. The worker command already encodes the intended execution mode.

## Core Model

Controller:
- The current agent session.
- Owns task decomposition, worker launch, handoff quality, monitoring, result review, and final integration.
- Does not assume workers will callback.

Worker:
- A CLI agent running in a cmux workspace.
- Receives one bounded task.
- Writes durable output files that the Controller can read later.
- May callback if instructed, but callback is optional and must not be the only completion signal.

cmux workspace:
- The default isolation unit for a worker.
- Created with `cmux new-workspace`.
- Read with `cmux read-screen`.
- Written to with `cmux send` plus `cmux send-key`.

## When To Use

Use this skill when:

- You need to split one larger goal into independent worker tasks.
- You want workers to run in visible cmux workspaces.
- You need a durable handoff file instead of a fragile chat-only prompt.
- You need to monitor whether a worker is alive, idle, blocked, or producing output.
- You want Claude and Codex workers available as execution choices.

Do not use this skill when:

- The next step is sequential and blocks on one local decision.
- Tasks will edit the same files without a clear owner.
- A direct local command or one local edit is faster than delegation.

## Worker Selection

Choose one worker per task.

| Worker | Use For | Launch Command |
|---|---|---|
| Claude | Broad implementation, refactoring, prose-heavy reasoning, tasks that benefit from long-form planning | `claude --dangerously-skip-permissions` |
| Codex | Codebase editing, command-heavy verification, search-heavy investigation, tasks where Codex tooling is useful | `codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search` |

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
- Context: files, commands, docs, and assumptions already known.
- Ownership: files or areas the worker may modify, and areas it must not touch.
- Constraints: coding style, risk boundaries, and anything the Controller already decided.
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
- Required reading:
  - `{path}`
  - `{path}`
- Useful commands:
  - `{command}`

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

3. Launch one cmux workspace per worker:

```bash
cmux new-workspace --name "worker-a" --cwd /path/to/repo --command "claude --dangerously-skip-permissions"
```

or:

```bash
cmux new-workspace --name "worker-b" --cwd /path/to/repo --command "codex --sandbox danger-full-access -c 'model_reasoning_summary_format=experimental' --search"
```

4. Capture the returned `workspace:N` ref.

5. Wait until the worker CLI is visibly ready:

```bash
cmux read-screen --workspace workspace:N --scrollback --lines 80
```

6. Dispatch the handoff by telling the worker to read the prompt file:

```bash
cmux send --workspace workspace:N "Read .tasks/20260513-183015-worker-a.prompt.md and execute it. Follow the Output Contract exactly."
cmux send-key --workspace workspace:N Enter
```

7. Verify the text was submitted, not merely typed:

```bash
cmux read-screen --workspace workspace:N --scrollback --lines 80
```

If the command is still sitting on the input line, send Enter again or target the exact surface from `cmux tree --workspace workspace:N`.

8. Monitor workers while doing non-overlapping Controller work.

9. When a worker appears complete, read its result file and inspect its workspace before integrating.

## Monitoring

Use screen state plus durable files. Do not rely on callback.

```bash
cmux read-screen --workspace workspace:N --scrollback --lines 120
cmux tree --workspace workspace:N
test -f .tasks/20260513-183015-worker-a.done
test -f .tasks/20260513-183015-worker-a.result.md
```

Interpretation:

| Signal | Meaning | Controller Action |
|---|---|---|
| CLI prompt is ready but no task text appears | Worker may not have received handoff | Resend the dispatch text and verify screen |
| Task text is visible on input line only | Enter may not have submitted | Send Enter again or target exact surface |
| Worker is reading files/running commands | Worker is active | Leave it running unless blocked too long |
| Approval/prompt/login UI appears | Worker is blocked | Decide whether to interact, relaunch, or take over locally |
| `.done` exists and result file exists | Worker has completed its contract | Review output and changes |
| Worker says done but result file is missing | Completion is not durable | Ask worker to write the result file or reconstruct from screen |

## Handoff Quality Rules

- Give each worker one clear task.
- Give each worker a disjoint ownership boundary.
- Prefer file paths and commands over vague module names.
- Tell workers where to write results before they begin.
- Make the result file the authoritative completion record.
- Keep callback optional.
- Keep Controller integration local; workers should not merge each other's changes.

## Failure Recovery

If a worker never starts:
- Read its screen.
- Confirm the workspace ref is correct.
- Resend the handoff.
- If still idle, close or ignore the workspace and relaunch with a clearer command.

If a worker is blocked:
- Determine whether the block is CLI readiness, login, prompt submission, command failure, or task ambiguity.
- Prefer fixing the handoff once over repeatedly nudging the worker.
- If the block is task ambiguity, update the prompt file and resend a short instruction to reread it.

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
| `cmux new-workspace --name X --cwd Y --command Z` | Launch a worker workspace |
| `cmux read-screen --workspace W --scrollback --lines N` | Inspect worker terminal output |
| `cmux send --workspace W "text"` | Type text into worker terminal |
| `cmux send-key --workspace W Enter` | Submit typed text |
| `cmux tree --workspace W` | Inspect panes and surfaces when targeting is unclear |
| `cmux select-workspace --workspace W` | Focus a worker workspace |
| `cmux close-workspace --workspace W` | Close a completed or abandoned worker workspace |
| `cmux list-workspaces` | List active workspaces |

## Common Mistakes

- Launching workers before writing prompt files.
- Sending a long task directly through `cmux send` instead of using a handoff file.
- Assuming `send-key Enter` worked without reading the screen afterward.
- Treating callback as required for completion.
- Giving two workers overlapping edit ownership.
- Asking workers to coordinate with each other instead of reporting back to Controller-owned result files.
- Forgetting that the Controller must review worker output before claiming the larger task is complete.

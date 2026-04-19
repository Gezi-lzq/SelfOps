---
name: cmux-multi-agent
description: Use when you need to dispatch tasks to multiple parallel kiro-cli agents via cmux workspaces. Enables Controller-Worker pattern where Controller dispatches tasks, Workers execute independently and notify back on completion. Use for any parallelizable work like code generation, verification, screenshot collection, research, or bulk file operations.
---

# CMUX Multi-Agent Workflow

Dispatch tasks to parallel kiro-cli Worker agents via cmux terminal workspaces. Controller (this agent) orchestrates, Workers execute independently and notify Controller on completion by sending a message directly into Controller's kiro-cli session.

## Architecture

```
Controller (this workspace)           Worker N (new workspace)
    │                                      │
    ├── cmux identify ─── note own ref     │
    ├── Write task prompt file ────────────►
    ├── cmux new-workspace --command ──────► kiro-cli starts
    ├── cmux send (/tools trust-all) ──────► Unlock tools
    ├── cmux send (task instruction) ──────► Read prompt, execute
    │                                      │
    │   Controller is FREE to do other     ├── Execute task...
    │   work while Workers run             ├── Write result file
    │                                      │
    │◄── cmux send to Controller surface ──┤  "✅ Worker N done"
    │   (message appears as user input)    │
    │                                      │
    ├── Read result file                   │
    └── Cleanup workspace                  │
```

## When to Use

- 2+ independent tasks that don't share state
- Bulk operations across multiple files/modules
- Tasks that benefit from parallel execution (code gen, verification, screenshots, research)
- Long-running tasks where Controller should remain free

## When NOT to Use

- Tasks with sequential dependencies (use serial execution)
- Tasks that modify the same files (will conflict)
- Simple tasks faster to do directly

## Task File Protocol

Create a `.tasks/` directory in the project root:

```
.tasks/
  ├── {task-id}.prompt.md      # Controller writes task description
  ├── {task-id}.result.md      # Worker writes results
  └── {task-id}.ack            # Controller marks as processed
```

## Worker Prompt Template

Every Worker prompt MUST include this protocol section. Choose one notification method based on the scenario.

### Method A: Send message to Controller's kiro-cli (preferred, non-blocking)

Worker sends a message directly into Controller's kiro-cli session. Controller stays free while Workers run — no blocking, no polling. Replace `{task-id}`, `{N}`, `{controller-workspace}`, and `{controller-surface}`:

```markdown
## Worker 协议

完成任务后必须严格执行以下 2 步：
1. 将结果写入 `{tasks-dir}/{task-id}.result.md`
2. 执行以下命令通知 Controller（直接写入 Controller 的 kiro-cli 会话）：
   ```bash
   cmux send --workspace {controller-workspace} --surface {controller-surface} '✅ Worker {N} 任务完成，结果已写入 {tasks-dir}/{task-id}.result.md，请读取结果并关闭我的 workspace。'
   sleep 0.3
   cmux send-key --workspace {controller-workspace} --surface {controller-surface} Enter
   ```
```

### Method B: Signal via wait-for (blocking, for sequential orchestration)

Controller blocks until Worker signals. Useful when Controller needs all results before proceeding. **Note:** `wait-for` blocks the bash process, so Controller's kiro-cli session cannot do anything else during the wait. Only use this when you genuinely need to block. Replace `{task-id}` and `{signal-name}`:

```markdown
## Worker 协议

完成任务后必须严格执行以下 2 步：
1. 将结果写入 `{tasks-dir}/{task-id}.result.md`
2. 执行以下命令发送完成信号：
   ```bash
   cmux wait-for -S {signal-name}
   ```
```

Controller side:
```bash
# Wait for one Worker
cmux wait-for worker-1-done --timeout 300

# Or wait for all in parallel
cmux wait-for worker-1-done --timeout 300 &
cmux wait-for worker-2-done --timeout 300 &
cmux wait-for worker-3-done --timeout 300 &
wait
```

## Controller Operations

### Step 0: Identify Controller workspace

This is critical — the refs are needed for Workers to send messages back.

```bash
cmux identify
# Record: workspace_ref (e.g. workspace:48) and surface_ref (e.g. surface:50)
```

### Step 1: Create task prompt files

Write detailed prompt files with:
- Clear task description
- Worker protocol section (with Controller's workspace/surface refs filled in)
- Input/output file paths
- Acceptance criteria

### Step 2: Launch Workers

For each Worker:

```bash
# Create workspace — parse the returned ref (output format: "OK workspace:N")
WS_REF=$(cmux new-workspace --name "worker-1" --cwd /path/to/project --command "kiro-cli chat" | awk '{print $2}')
# WS_REF is now e.g. "workspace:50"

# Wait for kiro-cli to initialize (~10s)
sleep 10

# Verify readiness (look for prompt like "Ready when you are!")
cmux read-screen --workspace "$WS_REF" 2>&1 | tail -3

# CRITICAL: Trust all tools before dispatching (prevents approval blocking)
cmux send --workspace "$WS_REF" '/tools trust-all'
sleep 0.3
cmux send-key --workspace "$WS_REF" 'Enter'
sleep 3

# Dispatch task
cmux send --workspace "$WS_REF" '请阅读 {tasks-dir}/{task-id}.prompt.md，严格按照任务内容和 Worker 协议执行。现在开始。'
sleep 0.3
cmux send-key --workspace "$WS_REF" 'Enter'
```

After dispatching, Controller is **free** — no blocking, no polling. Continue other work or wait for notifications.

### Step 3: Receive results

**If using Method A (non-blocking):** Workers send completion messages directly into Controller's kiro-cli session. Controller processes them as they arrive — read the result file and continue.

**If using Method B (blocking):** Controller waits for signals:
```bash
cmux wait-for worker-1-done --timeout 300
```

In both cases:
```bash
cat {tasks-dir}/{task-id}.result.md
touch {tasks-dir}/{task-id}.ack
```

### Step 4: Cleanup

```bash
cmux close-workspace --workspace workspace:N
```

## Critical Rules

### 1. Always send-key Enter after cmux send

`cmux send` types text but does NOT press Enter. Always follow with:

```bash
cmux send --workspace workspace:N 'content'
sleep 0.3
cmux send-key --workspace workspace:N 'Enter'
```

The `sleep 0.3` prevents race conditions between text input and Enter key.

### 2. Always /tools trust-all before dispatching

kiro-cli requires tool approval by default. Without trust-all, Workers block on every tool use. This MUST be the first command after kiro-cli starts.

### 3. Never assign same files to multiple Workers

Parallel Workers modifying the same file will conflict. Split tasks by file ownership.

### 4. Wait for kiro-cli readiness

After starting kiro-cli, wait ~10s before sending commands. Verify with:

```bash
cmux read-screen --workspace workspace:N 2>&1 | tail -3
```

### 5. Always include both workspace AND surface in Worker notification commands

Workers must target the exact surface of Controller's kiro-cli, not just the workspace. Use both `--workspace` and `--surface` from Step 0's `cmux identify` output.

## Batch Launch Pattern

For launching N Workers efficiently:

```bash
# Create all workspaces and collect refs
WS_REFS=()
for i in $(seq 1 N); do
  ref=$(cmux new-workspace --name "worker-${i}" --cwd /path/to/project --command "kiro-cli chat" | awk '{print $2}')
  WS_REFS+=("$ref")
done

# Wait for all to be ready
sleep 12

# Trust-all for all
for ref in "${WS_REFS[@]}"; do
  cmux send --workspace "$ref" '/tools trust-all'
  sleep 0.3
  cmux send-key --workspace "$ref" 'Enter'
done
sleep 3

# Dispatch all tasks
for i in $(seq 0 $((N-1))); do
  cmux send --workspace "${WS_REFS[$i]}" "请阅读 {tasks-dir}/task-$((i+1)).prompt.md，严格按照任务内容和 Worker 协议执行。现在开始。"
  sleep 0.3
  cmux send-key --workspace "${WS_REFS[$i]}" 'Enter'
done
```

## Monitoring Workers

```bash
# Read last 5 lines of Worker screen
cmux read-screen --workspace workspace:N 2>&1 | tail -5

# Read scrollback for full history
cmux read-screen --workspace workspace:N --scrollback --lines 200

# Find workspace by name
cmux find-window worker-1

# List all workspaces
cmux list-workspaces
```

## Useful cmux Commands Reference

| Command | Purpose |
|---------|---------|
| `cmux identify` | Get current workspace/surface refs |
| `cmux new-workspace --name X --cwd Y --command Z` | Create workspace and run command |
| `cmux send --workspace W --surface S 'text'` | Type text into specific surface |
| `cmux send-key --workspace W --surface S 'Enter'` | Press key in specific surface |
| `cmux read-screen --workspace W` | Read visible terminal content |
| `cmux read-screen --workspace W --scrollback --lines N` | Read scrollback history |
| `cmux notify --title T --body B` | Send desktop notification |
| `cmux find-window QUERY` | Find workspace by name/content |
| `cmux list-workspaces` | List all workspaces |
| `cmux close-workspace --workspace W` | Close a workspace |
| `cmux pipe-pane --workspace W --command 'cmd'` | Pipe terminal output to command |

## Task Splitting Guidelines

| Scenario | Split Strategy |
|----------|---------------|
| Code generation (multiple modules) | One Worker per module/package |
| Verification/testing | One Worker per component group |
| Screenshot collection | One Worker per page group |
| Research/analysis | One Worker per topic/repo |
| Bug fixes | One Worker per file set (no overlap) |
| Documentation | One Worker per chapter/section |

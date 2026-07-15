---
name: gtd-daily-review
description: Generate an evidence-backed GTD daily review from Nowledge Mem Threads. Use when the user asks what they did yesterday, requests a daily review or GTD summary, wants Next Actions or Waiting For extracted from recent AI conversations, or needs a date-bounded activity review grounded in exact conversation history.
compatibility: Requires nmem, jq, bash, and GNU date with the Nowledge FS thread view.
---

# GTD Daily Review

Build the review through an **evidence funnel**: exact time-bounded messages establish activity, then durable knowledge and graph links clarify meaning. This order prevents old summaries and related history from becoming false evidence for the target day.

## 1. Collect the evidence pack

Choose the review date in `Asia/Shanghai`. Unless the user names a date, use the previous calendar day in that timezone.

Run:

```bash
bash "$(dirname "$SKILL_PATH")/scripts/collect-evidence.sh" --date YYYY-MM-DD > /tmp/gtd-evidence.json
```

If `$SKILL_PATH` is unavailable, resolve `scripts/collect-evidence.sh` relative to this `SKILL.md`.

The collector uses Thread `updated_at` only to narrow candidates, then filters every retained message by its own timestamp. Treat the resulting `window` and `threads[].messages` as the date evidence.

Completion criterion: the evidence pack succeeds, reports the Beijing and UTC windows, and contains every Codex Thread with at least one user or assistant message inside that window. An empty pack produces an empty-day review rather than a speculative summary.

## 2. Build an evidence ledger

Read the evidence pack, grouping messages by workstream and outcome rather than by Thread title. For each candidate, record:

- observed change or result;
- completion state;
- explicit next step, owner, and dependency when stated;
- Thread path and message timestamps;
- referenced artifact such as a PR, Issue, commit, document revision, or command result.

Classify as progress only when the messages show a state change, decision, deliverable, verification result, or concrete blocker. Route unresolved but actionable work to `Next Actions`; route externally owned dependencies to `Waiting For`; route weak or ambiguous evidence to `待确认`.

Completion criterion: every retained claim has at least one in-window message; every in-window workstream is either represented in the ledger or explicitly classified as non-actionable conversation.

## 3. Resolve current meaning

For each ledger item that could create a Next Action, search durable knowledge narrowly:

```bash
nmem --json m search "<workstream + responsibility or current-state question>" -n 5
```

Use `nmem --json graph evolves <memory_id>` when a result may have a newer version. Use `nmem --json graph expand <memory_id> --depth 1 -n 10` only when ownership, dependency, or a nearby constraint remains unclear. Prefer the newest canonical understanding.

Memory and graph results can change interpretation, ownership, and current relevance. They cannot prove that work happened on the review date. Use `nmem ask --ephemeral` only for a narrow background question after the ledger exists.

Completion criterion: every proposed Next Action is still relevant, belongs to the user, and is consistent with the newest durable decision; uncertainties remain in `待确认`.

## 4. Verify strong claims

When a ledger item names an artifact and its native source is available, inspect that source. Give strongest weight to PR/Issue state, commits, document revisions, and recorded command results; use explicit user confirmation or a concrete assistant result when no artifact exists.

Completion criterion: completed work is supported by an artifact or explicit result. Describe partial progress as partial progress.

## 5. Write the review

Use Beijing time and this structure:

```markdown
# GTD 每日回顾 - YYYY-MM-DD

## 昨日推进
- [结果或状态变化]
  - 证据：[Thread 标题](nowledgemem path)，HH:MM
  - Artifact：可选

## 未竟事项
- [当前停点]
  - 原因：
  - 证据：

## Next Actions
- [ ] [一个具体、可执行、仍由用户负责的动作]
  - 来源：

## Waiting For
- [等待对象与条件]
  - 复查条件：

## 待确认
- [证据不足、状态冲突或职责不明确的事项]
```

Omit empty sections except `昨日推进`; state clearly when no qualifying progress exists. Keep evidence compact and traceable.

Completion criterion: every progress item cites in-window evidence, every Next Action has a concrete verb and valid owner, Waiting For names an external dependency, and no summary, Memory, Feed event, or graph edge is presented as date proof.

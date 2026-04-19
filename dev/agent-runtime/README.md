# Agent Runtime

以 Git 声明式管理本机 agent skills 分发。

## 核心概念

```text
Git registry (skills.toml + projects.toml) = desired state
~/.kiro/skills, .claude/skills, ...        = generated state (symlinks)
.state/scan.json                           = observed state
```

运行时目录（`~/.kiro/skills`、`<project>/.claude/skills` 等）不再手动维护，而是由 registry 驱动生成。

## 模块结构

```text
dev/agent-runtime/
  mise.toml                 # 工具链 + 任务入口
  registry/
    skills.toml             # skill 声明 + bundle 分组
    projects.toml           # 项目 → agent → desired skills
  materialized/skills/      # local_path / owned skill 落地 (owned git-tracked)
  .agents/skills/           # public skill 缓存 (git-ignored, npx 管理)
  scripts/agent_runtime.py  # reconciler 实现
  .state/                   # scan.json, plan.json, apply-log.jsonl (git-ignored)
```

## 命令

```bash
mise run agent:scan                # 扫描已注册项目的实际状态
mise run agent:scan -- --discover  # 额外发现 ~/Dev 下未注册项目
mise run agent:plan                # 生成变更计划（只读）
mise run agent:apply               # 执行计划（destructive 操作需 --force）
mise run agent:apply -- --force    # 执行计划（含删除和覆盖）
mise run agent:update              # 更新 public skills 到最新版本
```

### scan

观察实际状态，不修改文件。输出每个 project/agent 的 skill 列表，标注类型：

`☁ public` · `📁 local` · `✎ owned` · `⊘ unmanaged` · `⚠ broken`

`--discover` 扫描指定目录（默认 `~/Dev`）下所有含 agent skill 目录的项目，未注册的标记为 `(unregistered)`。

### plan

展开 bundles，对比 scan state，生成 skill 级动作：

| 动作 | 说明 |
|------|------|
| `sync_source` | 同步 skill 内容到本地 |
| `create_link` / `update_link` / `replace_path` | 管理 symlink |
| `remove_path` | 清理不再 desired 的 skill |
| `missing_source` / `config_error` | 报告配置问题 |

输出按项目聚合，相同操作的 agent 合并显示，add 操作自动聚类为 bundle。

### apply

重新计算 plan 并执行：

1. `local_path` skill → copy 到 `materialized/skills/`
2. `public` skill → 若未缓存，通过 `npx skills add` 下载
3. 用绝对 symlink 分发到各 agent skill 目录
4. 清理不再 desired 的 symlink

安全机制：destructive 操作（`remove_path`、`replace_path`、`update_link`）默认只 warning，需 `--force` 执行。

## 配置

### registry/skills.toml

同时包含 skill catalog 和 bundle catalog。

```toml
# Public — npx skills add 获取
[skills.systematic-debugging]
source = { type = "public", spec = "obra/superpowers" }

# Local — 从本机路径同步
[skills.enterprise-build]
source = { type = "local_path", path = "/path/to/.agents/skills/enterprise-build" }
materialized_path = "materialized/skills/enterprise-build"

# Owned — 直接在本 repo 维护
[skills.cmux-multi-agent]
source = { type = "owned" }

# Bundle — desired config 的分组简写
[bundles.core]
description = "Skill management"
skills = ["find-skills", "skill-creator", "writing-skills"]
```

Source 类型：

| 类型 | 获取方式 | 存储位置 |
|------|----------|----------|
| `public` | `npx skills add <spec>` | `.agents/skills/<name>` |
| `local_path` | 从本机路径 copy | `materialized/skills/<name>` |
| `owned` | 直接在 repo 内维护 | `materialized/skills/<name>` |

### registry/projects.toml

定义每个项目启用哪些 agent，通过 bundles / include / exclude 声明 desired skills。

```toml
[projects."@global"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "tools", "memory"]

[projects."/Users/gezi/Dev/SelfOps"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "superpowers"]
```

Per-agent override（替换项目级默认值）：

```toml
[projects."@global".agent_overrides.codex]
bundles = []
include = ["gh-cli"]
```

Target 路径约定：

```text
@global + kiro   → ~/.kiro/skills
@global + claude → ~/.claude/skills
/repo   + kiro   → /repo/.kiro/skills
```

## 设计原则

- Git registry 是 desired state 的唯一来源
- Runtime skill directories 是 generated state，可随时重建
- Skill name 全局唯一，不支持同名多版本
- Bundle 只存在于 desired config，不出现在 scan state
- Public skill 遵循 npx skills 原生流程
- 项目自带的 git-tracked skill 不被 agent-runtime 接管

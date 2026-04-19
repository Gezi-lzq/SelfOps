# Agent Runtime Registry

## 背景

SelfOps 的目标是以运维视角管理"我自己的工作环境"。Agent Runtime Registry 是其中的 `dev/agent-runtime` 模块：它管理 agent CLI 安装入口、skills 来源、skills 分组，以及每个项目启用哪些 agent 与 skills。

核心原则：

```text
Git registry = desired state
agent runtime directories = generated state
scan output = local observed state
```

运行时目录，例如 `~/.codex/skills`、`~/.kiro/skills`、`~/.claude/skills`、`<project>/.codex/skills`，不再是长期维护配置的地方。它们可以被扫描、对比和重建。

## 模块结构

```text
dev/agent-runtime/
  mise.toml
  registry/
    skills.toml
    projects.toml
  materialized/
    skills/           # local_path / owned skill 落地目录 (git-ignored, owned 除外)
  .cache/
    skills/           # public skill 缓存目录 (git-ignored, npx 管理)
  scripts/
    agent_runtime.py
  .state/
    scan.json
    plan.json
    apply-log.jsonl
```

- `.state/` — 本机运行状态，git-ignored。
- `.cache/skills/` — public skill 的 npx 下载缓存，git-ignored。已缓存的 skill 不会重复下载。
- `materialized/skills/` — `local_path` 和 `owned` skill 的落地目录。`owned` 类型由 git 跟踪，`local_path` 类型 git-ignored。

## 配置文件

### registry/skills.toml

`skills.toml` 同时包含 skill catalog 和 bundle catalog。

```toml
# Public skill — 通过 npx skills add 获取，缓存在 .cache/skills/
[skills.systematic-debugging]
source = { type = "public", spec = "obra/superpowers" }

# Local skill — 从本机路径同步到 materialized/skills/
[skills.enterprise-build]
source = { type = "local_path", path = "/path/to/project/.agents/skills/enterprise-build" }
materialized_path = "materialized/skills/enterprise-build"

# Owned skill — 直接在本 repo 维护
[skills.cmux-multi-agent]
source = { type = "owned" }
materialized_path = "materialized/skills/cmux-multi-agent"

# Bundle — 手写 desired config 时减少重复
[bundles.core]
description = "Skill management"
skills = ["find-skills", "skill-creator", "writing-skills"]

[bundles.superpowers]
description = "Engineering workflow"
skills = ["systematic-debugging", "verification-before-completion", ...]
```

Source 类型：

| 类型 | 说明 | 存储位置 |
|------|------|----------|
| `public` | `npx skills add <spec>` 获取 | `.cache/skills/<name>` |
| `local_path` | 从本机路径 copy | `materialized/skills/<name>` |
| `owned` | 直接在 repo 内维护 | `materialized/skills/<name>` |

### registry/projects.toml

`projects.toml` 定义项目启用哪些 agent，以及通过 bundles/include/exclude 得到哪些 desired skills。

```toml
[projects."@global"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "tools", "memory"]
include = []
exclude = []

[projects."/Users/gezi/Dev/SelfOps"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "superpowers"]
include = []
exclude = []
```

Per-agent overrides：如果某个 agent 需要不同的 skill 集合，可以用 `agent_overrides` 覆盖项目级默认值：

```toml
[projects."@global".agent_overrides.codex]
bundles = []
include = ["gh-cli"]
exclude = []
```

Target 路径由约定推导：

```text
@global + kiro  -> ~/.kiro/skills
@global + claude -> ~/.claude/skills
/repo + kiro   -> /repo/.kiro/skills
```

## 命令

所有入口由 mise 驱动：

```bash
mise run agent:scan              # 扫描已注册项目
mise run agent:scan -- --discover  # 额外发现 ~/Dev 下未注册项目
mise run agent:plan              # 生成变更计划
mise run agent:apply             # 执行计划（destructive 操作需 --force）
mise run agent:apply -- --force  # 执行计划（含删除和覆盖）
mise run agent:update            # 更新 public skills 到最新版本
```

### scan

观察实际状态，不修改文件。输出每个 project/agent 的实际 skill 列表，标注 source 类型（☁ public / 📁 local / ✎ owned / ⊘ unmanaged / ⚠ broken）。

`--discover [DIR...]` 参数可扫描指定目录下所有含 agent skill 目录的项目，未在 `projects.toml` 注册的标记为 `(unregistered)`。默认扫描 `~/Dev`。

### plan

读取 registry，展开 bundles，对比 scan state，生成 skill 级动作：

- `sync_source` — 同步 skill 内容到本地
- `create_link` / `update_link` / `replace_path` — 管理 symlink
- `remove_path` — 清理不再 desired 的 skill
- `missing_source` / `config_error` — 报告问题

Plan 输出按项目聚合，相同操作的 agent 合并显示，add 操作自动聚类为 bundle。

### apply

重新计算 plan 并执行：

1. `local_path` skill：copy 到 `materialized/skills/`
2. `public` skill：如果 `.cache/skills/<name>` 不存在，通过 `npx skills add` 下载
3. 用绝对 symlink 分发到各 agent skill 目录
4. 删除不再 desired 的 skill symlink

安全机制：destructive 操作（`remove_path`、`replace_path`、`update_link`）默认不执行，只 warning。需要 `--force` 才会真正执行删除和覆盖。

## 设计原则

- SelfOps repository 是 agent runtime desired state 的来源。
- Runtime skill directories 是 generated state。
- Skill name 在本机全局唯一，不支持同名多版本。
- Bundle 只存在于 desired config，不出现在 scan state 中。
- Public skill 遵循 npx skills 原生流程，缓存在 `.cache/` 中。
- 项目自带的 skill（如 `.agents/skills/` 内 git-tracked 的 symlink）不应被 agent-runtime 接管。
- CLI 安装遵循 mise 原生配置与任务模型。

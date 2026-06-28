# Agent Runtime

## 目标

本机运行着多个 AI agent（Kiro、Claude、Codex），每个 agent 通过 skills 目录获取能力。手动维护这些目录存在几个问题：

- 同一个 skill 要复制到多个项目的多个 agent 目录下
- skill 版本漂移，各项目不一致
- 新增项目或 agent 时需要手动同步

Agent Runtime 的目标是：**在 Git 中声明 "哪个项目的哪个 agent 需要哪些 skills"，然后自动生成所有运行时目录。**

## 抽象模型

三层状态：

```
desired state   ← Git registry (skills.toml + projects.toml)
observed state  ← scan 扫描本机实际目录
generated state ← apply 生成的 symlinks (~/.kiro/skills, .claude/skills, ...)
```

reconciler 的工作就是让 generated state 收敛到 desired state。

## 管理关系

```
skills.toml                    projects.toml
┌─────────────────────┐        ┌──────────────────────────────┐
│ skill catalog       │        │ project: @global             │
│   skill → source    │        │   agents: [kiro, claude]     │
│                     │        │   bundles: [core, tools]     │
│ bundle catalog      │        │                              │
│   bundle → [skills] │───────▶│ project: ~/Dev/SelfOps       │
│                     │        │   agents: [kiro, claude]     │
└─────────────────────┘        │   bundles: [core, superpowers]│
                               └──────────────────────────────┘
                                            │
                                            ▼
                               ┌──────────────────────────────┐
                               │ ~/Dev/SelfOps/.kiro/skills/  │
                               │   skill-a → symlink          │
                               │   skill-b → symlink          │
                               │ ~/Dev/SelfOps/.claude/skills/│
                               │   skill-a → symlink          │
                               │   skill-b → symlink          │
                               └──────────────────────────────┘
```

- **Skill** 是最小单元，有三种来源（source type）
- **Bundle** 是 skill 的分组简写，只在 desired config 中存在
- **Project** 声明启用哪些 agent，通过 bundles/include/exclude 得到 desired skills
- 最终每个 project/agent 目录下的 skill 都是指向本地缓存的 **symlink**

### Skill 来源

| 类型 | 获取方式 | 本地存储 |
|------|----------|----------|
| `public` | `npx skills add <spec>` | `.agents/skills/<name>` |
| `local_path` | 从本机路径 copy | `materialized/skills/<name>` |
| `owned` | 直接在本 repo 维护 | `materialized/skills/<name>` |

### Target 路径约定

```
@global + kiro   → ~/.kiro/skills/<skill>
@global + claude → ~/.claude/skills/<skill>
/repo   + kiro   → /repo/.kiro/skills/<skill>
```

## 命令

```bash
mise run agent:scan                # 扫描实际状态
mise run agent:scan -- --discover  # 发现 ~/Dev 下未注册项目
mise run agent:plan                # 生成变更计划（只读）
mise run agent:apply               # 执行计划（destructive 需 --force）
mise run agent:apply -- --force    # 执行计划（含删除和覆盖）
mise run agent:apply -- --projects /path/to/projects.toml  # 使用自定义项目清单
mise run agent:update              # 更新 public skills 到最新版本
```

### Machine-specific project files

`skills.toml` is shared skill catalog and bundle state. Project paths are machine-local, so each
machine can keep a separate projects file built from `registry/projects.machine.template.toml`.

Recommended shape:

```text
registry/projects.toml                  # default/shared project mapping
registry/projects.machine.template.toml # shared template for machine-specific mappings
registry/projects.<machine>.toml        # concrete paths for one machine, often on a machine branch
```

Use machine-specific files with `--projects`:

```bash
PROJECTS=/absolute/path/to/dev/agent-runtime/registry/projects.<machine>.toml
mise run agent:scan -- --projects "$PROJECTS"
mise run agent:plan -- --projects "$PROJECTS"
mise run agent:apply -- --projects "$PROJECTS"
```

Do not apply a projects file to a machine until its paths and `local_path` sources match that
machine. Keep shared skill definitions in `skills.toml`; keep machine-specific paths and local-only
sources in the machine projects file or machine branch.

**scan** — 观察实际状态，不修改文件。标注类型：`☁ public` · `📁 local` · `✎ owned` · `⊘ unmanaged` · `⚠ broken`。`--discover` 额外扫描未注册项目。

**plan** — 展开 bundles，对比 scan，生成 skill 级动作（`sync_source`、`create_link`、`update_link`、`remove_path` 等）。输出按项目聚合，相同操作的 agent 合并显示。

**apply** — 重新计算 plan 并执行。`local_path` copy 到 materialized，`public` 通过 npx 下载，然后用绝对 symlink 分发。Destructive 操作默认只 warning，需 `--force`。

## 配置详解

### registry/skills.toml

```toml
# Public skill
[skills.systematic-debugging]
source = { type = "public", spec = "obra/superpowers" }

# Local skill
[skills.enterprise-build]
source = { type = "local_path", path = "/path/to/.agents/skills/enterprise-build" }
materialized_path = "materialized/skills/enterprise-build"

# Owned skill
[skills.cmux-multi-agent]
source = { type = "owned" }

# Bundle
[bundles.core]
description = "Skill management"
skills = ["find-skills", "skill-creator", "writing-skills"]
```

### registry/projects.toml

```toml
[projects."@global"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "tools", "memory"]

[projects."/Users/gezi/Dev/SelfOps"]
agents = ["kiro", "claude", "codex"]
bundles = ["core", "superpowers"]

# Per-agent override（替换项目级默认值）
[projects."@global".agent_overrides.codex]
bundles = []
include = ["gh-cli"]
```

## 模块结构

```
dev/agent-runtime/
  mise.toml                 # 工具链 + 任务入口
  registry/
    skills.toml             # skill 声明 + bundle 分组
    projects.toml           # 项目 → agent → desired skills
  materialized/skills/      # local_path / owned skill 落地
  .agents/skills/           # public skill 缓存 (git-ignored)
  scripts/agent_runtime.py  # reconciler
  .state/                   # scan.json, plan.json, apply-log.jsonl (git-ignored)
```

## 设计原则

- Git registry 是 desired state 的唯一来源
- Runtime skill directories 是 generated state，可随时重建
- Skill name 全局唯一，不支持同名多版本
- Bundle 只存在于 desired config，不出现在 scan state
- 项目自带的 git-tracked skill 不被 agent-runtime 接管

# SelfOps

个人自动化运维工具集

## 本地工具链

本仓库使用 `mise` 管理本地运行环境和任务。安装 `mise` 后，在仓库根目录执行：

```bash
mise trust
mise install
mise run doctor
```

## Agent Registry

Agent Runtime 是 SelfOps 以运维视角管理本机 agent 配置的模块。它把 skills 与项目分发关系声明在 Git 中，把实际 `.codex/skills`、`.kiro/skills`、`.claude/skills` 等目录视为 generated state。

核心配置位于：

```text
dev/agent-runtime/registry/skills.toml   # skill 声明与 bundle 分组
dev/agent-runtime/registry/projects.toml  # 项目 → agent → skill 分配
```

常用命令：

```bash
mise install
mise run agent:scan                # 查看当前实际状态
mise run agent:scan -- --discover  # 发现 ~/Dev 下未注册项目
mise run agent:plan                # 生成变更计划（只读）
mise run agent:apply               # 执行计划（destructive 操作需 --force）
mise run agent:apply -- --force    # 执行计划（含删除和覆盖）
```

Skill source 类型：
- `public` — 通过 `npx skills add` 从 GitHub 获取，缓存在 `.cache/skills/`
- `local_path` — 从本机路径同步到 `materialized/skills/`
- `owned` — 直接在本 repo 内维护

设计背景和抽象约定见 [Agent Runtime Registry](./docs/agent-runtime-registry.md)。

## 工具列表

- [newapi-checkin](./newapi-checkin/) - NewAPI 自动签到

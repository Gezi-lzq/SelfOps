# agents/bub Agent Guide

## 职责

`agents/bub/` 管理 Bub 部署、profile 隔离、插件来源、环境渲染和 tape 备份工作流。profile 之间应保持隔离，不共享 secret 文件。

## 事实来源

- `README.md`：Bub 目录和操作说明。
- `mise.toml`：Bub 任务入口。
- `profiles/<profile>/AGENTS.md`：profile 内部的具体行为规则。
- `profiles/<profile>/projects.toml`、`env.template`、`startup.sh`：profile 配置和启动入口。

## 操作规则

- profile-specific 行为写入对应 `profiles/<profile>/AGENTS.md`。
- 新 profile 应包含 `AGENTS.md`、`bub-reqs.txt`、`env.template`、`projects.toml` 和 `startup.sh`。
- secrets 渲染到 profile env 文件，不提交。
- `bub:backup` 可能上传包含 agent 会话历史的 tape；只有用户要求备份或流程明确需要时才运行。
- 嵌套 `mise.toml` 未 trust 时，先 trust 精确文件。

## 常用验证

```bash
git diff --check
mise trust agents/bub/mise.toml
mise -C agents/bub tasks
```

profile 脚本变更时：

```bash
bash -n agents/bub/profiles/<profile>/startup.sh
```

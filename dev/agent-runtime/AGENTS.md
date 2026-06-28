# dev/agent-runtime Agent Guide

## 职责

`dev/agent-runtime/` 管理 agent skills 的声明、分组和运行时分发。目标是在 Git 中声明 desired state，再通过 scan/plan/apply 生成各 agent 的 skills 目录。

## 事实来源

- `README.md`：agent-runtime 模型和命令说明。
- `registry/skills.toml`：公共 skill catalog 和 bundle。
- `registry/projects.toml`：默认项目映射。
- `registry/projects.machine.template.toml`：机器项目清单模板。
- `registry/projects.<machine>.toml`：某台机器的具体路径，通常只在机器分支维护。
- `scripts/agent_runtime.py` 与 `tests/`：reconciler 行为。

## 操作规则

- 公共 skill、bundle 和模板进 `main`。
- 具体本机路径和本机 `local_path` 选择进 `projects.<machine>.toml`，通常留在机器分支。
- 不要把另一台机器的 projects 文件直接 apply 到当前机器。
- 先跑 `scan`/`plan`，确认计划符合预期后才考虑 `apply`。
- `apply` 会改运行时目录；只有任务明确要求落地运行时状态时才执行。

## 常用验证

```bash
git diff --check
mise -C dev/agent-runtime run test
mise run agent:scan -- --projects /path/to/projects.<machine>.toml
mise run agent:plan -- --projects /path/to/projects.<machine>.toml
```

如果只改 TOML/Markdown，可用 `git diff --check` 加一次只读 `agent:plan`。不要用 `agent:apply` 作为默认验证。

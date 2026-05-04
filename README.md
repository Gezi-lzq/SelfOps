# SelfOps

个人自动化运维工具集

## 快速开始

本仓库使用 `mise` 管理本地运行环境和任务：

```bash
mise trust && mise install
```

如果目标是新机器初始化全局开发环境，先安装 `mise`，然后执行：

```bash
bash dev/environment/bootstrap.sh --activate-zsh
```

这会把仓库里的全局 `mise` 配置链接到 `~/.config/mise/config.toml`，
按 `dev/environment/config.toml` 安装全局工具，并把 `mise activate zsh`
追加到 `~/.zshrc`。

如果要把你的全局 `mise` 配置也纳入这个仓库维护，可以把仓库内的
[`./dev/environment/config.toml`](./dev/environment/config.toml) 链接到
`~/.config/mise/config.toml`：

```bash
mkdir -p ~/.config/mise
ln -sfn "$PWD/dev/environment/config.toml" ~/.config/mise/config.toml
```

## 模块

| 模块 | 说明 | 文档 |
|------|------|------|
| [Environment](./dev/environment/) | 管理本机全局开发环境依赖与 `mise` 配置 | [README](./dev/environment/README.md) |
| [Agent Runtime](./dev/agent-runtime/) | 以 Git 声明式管理本机 agent skills 分发 | [README](./dev/agent-runtime/README.md) |
| [Runners](./infra/runners/) | 声明式管理 self-hosted GitHub Actions runner | [README](./infra/runners/README.md) |
| [Bub Agents](./agents/bub/) | Bub agent 声明式部署与 profile 隔离运行 | — |
| [newapi-checkin](./newapi-checkin/) | NewAPI 自动签到 | — |

### Agent Runtime 常用命令

```bash
mise run agent:scan                # 查看当前实际状态
mise run agent:scan -- --discover  # 发现 ~/Dev 下未注册项目
mise run agent:plan                # 生成变更计划（只读）
mise run agent:apply               # 执行计划（destructive 操作需 --force）
mise run agent:apply -- --force    # 执行计划（含删除和覆盖）
mise run agent:update              # 更新 public skills 到最新版本
```

# SelfOps

个人自动化运维工具集

## 快速开始

本仓库使用 `mise` 管理本地运行环境和任务：

```bash
mise trust && mise install
```

## 模块

| 模块 | 说明 | 文档 |
|------|------|------|
| [Agent Runtime](./dev/agent-runtime/) | 以 Git 声明式管理本机 agent skills 分发 | [README](./dev/agent-runtime/README.md) |
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

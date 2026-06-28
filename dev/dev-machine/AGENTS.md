# dev/dev-machine Agent Guide

## 职责

`dev/dev-machine/` 管理开发机的目标状态、当前事实、服务记录、存储布局和机器级操作说明。开发机默认通过 NetBird network 互通，具体机器事实以本目录文档为准。

## 事实来源

- `PLAN.md`：目标状态和设计意图。
- `STATE.md`：当前机器事实和已完成变更。
- `README.md`：本目录索引和基本原则。
- 子系统 README：具体服务、脚本和验证方式。
- 根 `AGENTS.md`：公共分支、安全和回写规则。

## 操作规则

- 改变目标状态时更新 `PLAN.md`。
- 应用或确认了机器事实后更新 `STATE.md`。
- 新增长期服务时，优先为该服务建立子目录，包含 README、模板、安装脚本或 systemd unit 模板。
- secret 放本地 env 文件或 secret store，不进 Git。
- 机器间访问优先按 NetBird DNS/SSH alias 设计；不要把不稳定私有 IP 写入公共规则。
- 某台机器额外的访问方式只作为该机器事实记录，不提升为根级公共假设。

## 常用验证

文档/config 改动：

```bash
git diff --check
```

Shell 脚本：

```bash
bash -n <script>
```

Python 服务：

```bash
python3 -m py_compile <file.py>
```

systemd user unit 或本机服务变更时，只有在任务要求应用到当前机器时才执行 daemon-reload、restart、status。展示 status/log 时摘要并脱敏。

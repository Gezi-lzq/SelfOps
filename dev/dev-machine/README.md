# 开发机管理

管理 PVE 开发机 `gezi-dev` 的目标状态和已完成变更，避免配置靠临时操作散落。

| 文档 | 内容 |
|------|------|
| [PLAN.md](./PLAN.md) | 目标状态 |
| [STATE.md](./STATE.md) | 当前状态与变更记录 |
| [herdr-web](./herdr-web/) | 通过 Caddy + ngrok 暴露开发机公网入口，当前承载 Herdr |
| [herdr-status](./herdr-status/) | 手机友好的 Herdr session/agent 只读状态页 |

原则：

- 默认用户：`debian`
- 目标状态写入 `PLAN.md`
- 已完成变更写入 `STATE.md`
- 不记录密码、token、setup key

# GTD 每日回顾：2026-07-14（北京时间）

## 当日推进

- **Kafka Consumer Lag 文章**：完成一轮面向读者的定向重写并同步飞书文档 revision 33，保留两张图、公式与链接；随后进一步确认当前稿件仍偏“设计说明”，形成了从 dashboard 反直觉现象逐步引出 Time Lag 的新叙事路径。
- **客户集群容量与告警排查**：重算两个集群的容量水位，纠正了 Max/P99 混用和错误的线性扩容推算；随后定位 US 大范围重启后流量告警主要是规则误报，而非共享业务故障。
- **Grafana 告警规则修复**：创建 [opsbox PR #180](https://github.com/AutoMQ/opsbox/pull/180)，把最终 condition 指回组合表达式，保留 30% 下跌阈值，修正通知维度；根据 Copilot review 又将 restart lookback 调整为 20m、保留 `for: 10m`，并用真实 Loki/VM 历史数据回放验证。
- **Home GCP 文案与入口**：创建 [automqbox PR #6117](https://github.com/AutoMQ/automqbox/pull/6117)（base `develop/202605`）；为 `develop/gcp_docker` 创建 [PR #6118](https://github.com/AutoMQ/automqbox/pull/6118)，发现该分支没有完整 `scope` 链路后收窄为仅补文案和通用 Compute Engine 链接，避免引入无效 runtime 引用。
- **Table Topic 自有 Schema Registry**：完成重复项搜索，并创建 [automqbox Issue #6122](https://github.com/AutoMQ/automqbox/issues/6122)，记录配置、鉴权、敏感信息保护以及协议/迁移边界。

## Next Actions

- [ ] **继续 Kafka Consumer Lag 稿件的叙事重构**：先只重写开头至“精确查询成本”，确认语气后再扩展到方案、恢复与误差章节。
- [ ] **跟进 opsbox PR #180 至合并**：确认 reviewer 对 20m lookback、10m `for` 和 `$values.D` 的处理无新增意见；无需再追查“54 个集群共享故障”。
- [ ] **跟进 automqbox PR #6117 / #6118**：分别按各自 base 审阅；#6118 保持最小兼容，不在该 PR 中 backport 完整 `scope` 链路。
- [ ] **推动 Issue #6122 triage**：补齐自有 Schema Registry 的协议、鉴权、兼容性和迁移决策，再决定实现范围。

## Waiting / Someday

- **两个客户集群扩容**：已有按真实业务流量模型的容量评估，但当天没有形成由用户立即执行扩容的明确指令；等待业务侧确认目标水位与方案后再排期。
- **GCP 机型选型与 storage profile**：当天完成了候选、覆盖、价格、AKU 和磁盘兼容性分析，但最新职责记忆明确：自 2026-07-15 起该事项不再由用户负责。因此仅作历史成果保留，不进入 Next Actions。

## 取证说明

- 回顾窗口为 `2026-07-14 00:00–24:00 BJT`（UTC `2026-07-13T16:00:00Z–2026-07-14T16:00:00Z`）。
- 当日事实以 Thread 内原始消息时间戳为准；`updated_at` 仅用于筛候选。已排除两条仅因元数据更新进入候选、但窗口内没有真实 user/assistant 消息的旧 Thread，其中 xterm.js 长对话的末尾真实消息停留在 7 月 2 日。
- Memory 用于校正当前职责：`GCP 机型后续不再属于用户职责`（memory `4fe6f5eb-ed23-4d0d-bb60-27216c643570`）覆盖了当天较早的机型分析，不将其误列为用户待办。

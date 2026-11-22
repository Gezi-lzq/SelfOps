# GTD 每日回顾 - 2026-07-14

## 昨日推进
- 完成 `automq-public` 项目的 GCP Service Account 授权，创建 user-managed JSON key，并通过飞书交付给李振琦。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](/threads/codex/gcp-service-account-home-gcp-463388cb)，10:29、10:33、10:37
  - Artifact：Service Account `automq-public-dev-ops-authing@automq-public.iam.gserviceaccount.com`；Key ID `86886109d7249b8dbc11f5f7102835f569f24ab8`；飞书 Message ID `om_x100b6a6e42ee04a0c022edb4590902f`
- 成功构建并注册 Test Home 的 GCP BYOC Console 版本，补上 `Product.NoAvailableVersion` 所缺的 GCP version record。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](/threads/codex/gcp-service-account-home-gcp-463388cb)，14:48、15:13
  - Artifact：[GitHub Actions Run 29312496876](https://github.com/AutoMQ/automqbox/actions/runs/29312496876) 成功；镜像 tag `8.3.0-SNAPSHOT-20260714065004-gcp`；Home Ops API 返回 HTTP 200
- 完成 Home GCP 安装页文案改动并分别提交到两个目标分支：创建 PR #6117；为旧分支创建 PR #6118，并修正为仅保留兼容文案、移除无效的 `environment.scope` runtime 引用。两条 PR 的最终 CI 均通过。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](/threads/codex/gcp-service-account-home-gcp-463388cb)，15:21、15:27、15:32、15:40
  - Artifact：[automqbox#6117](https://github.com/AutoMQ/automqbox/pull/6117)，commit `f872fb6217`；[automqbox#6118](https://github.com/AutoMQ/automqbox/pull/6118)，最终 head `52c6958ae350`
- 完成 SQEMS 相关数据复核：产出 15 天 Heap 报告、双集群容量复评和 3 天水位统计，并纠正 Max 扩容计算为 EBSWAL 的 `2W + R` 模型，最终建议分别扩至 11、22 节点。
  - 证据：[SQEMS topic 巡检与重启流量告警规则修复](/threads/codex/sqems-topic-1304fc6c)，15:52、16:00、16:10、16:51
  - Artifact：`/home/debian/automq-workspace/scratch/observability/20260714_jfVDA_heap_stat_review_15d/report.md`；`/home/debian/automq-workspace/scratch/observability/20260714_geely_two_clusters_capacity_reassessment_15d/report.md`
- 定位 US 大批重启后流量告警为规则问题，修复 condition、30% 下跌判断、标签、20 分钟 restart lookback 和告警 value；真实 Loki/VM 回放通过，PR #180 当天合并。
  - 证据：[SQEMS topic 巡检与重启流量告警规则修复](/threads/codex/sqems-topic-1304fc6c)，19:39、20:06、20:14、20:18
  - Artifact：[opsbox#180](https://github.com/AutoMQ/opsbox/pull/180)，commit `64881ec45d9`，合并时间 20:18
- 完成 Kafka Consumer Lag 中文稿的一轮定向重写和可读性复查，并同步至飞书 revision 33；图片、公式和链接经回读确认保留。
  - 证据：[Kafka Consumer Lag 中文稿定稿、飞书导入与定向重写](/threads/codex/kafka-consumer-lag-9dd7a1bb)，16:59、17:03、17:04
  - Artifact：[飞书文档](https://automq66.feishu.cn/docx/InEVd6qecolSVNxxVaGcsW9Enqf)；`/home/debian/automq-workspace/scratch/blogs/kafka-consumer-lag-from-message-count-to-time.md`
- 完成 Codex skill 发现链路诊断与清理：Lark skills 从 27 个普通目录收敛为 6 个受 manager 管理的 symlink；随后将 37 条 workspace skill policy 迁至 user config，模型可见 skills 从 115 降至 54。
  - 证据：[确认 Codex skills 配置作用域并清理遗留 Lark skills](/threads/codex/codex-skills-lark-skills-b914f3f3)，20:24、20:27、20:34
  - Artifact：`codex debug prompt-input` A/B 结果；清理后的 plan 无 Lark action；disabled probe 消失
- 将 PR #3449 的 4 个本地优化提交以普通 fast-forward 推送到远端，使本地与远端对齐。
  - 证据：[确认 Codex skills 配置作用域并清理遗留 Lark skills](/threads/codex/codex-skills-lark-skills-b914f3f3)，20:43、20:46
  - Artifact：[AutoMQ/automq#3449](https://github.com/AutoMQ/automq/pull/3449)，当天推送 `4acf19bdcb..0d77404354`
- 创建 Table Topic 支持用户自有 Schema Registry 的需求 Issue，并回读确认内容落库。
  - 证据：[在 AutoMQ/automqbox 创建 Table Topic 自有 Schema Registry 需求 Issue](/threads/codex/automq-automqbox-table-topic-schema-registry-issue-6c4c0e1d)，20:20、20:21
  - Artifact：[automqbox#6122](https://github.com/AutoMQ/automqbox/issues/6122)
- 完成 GCP 8.x 机型、ARM、AKU、zone 覆盖、VM/磁盘成本与存储兼容性评估，纠正“`n4d` 可直接替代 `n2d`”的早期判断，形成 PD 与 Hyperdisk 双 profile 结论。
  - 证据：[AutoMQ GCP 机型筛选与 8.x 候选建议](/threads/codex/automq-gcp-8-x-89fd4a63)，11:35、14:38、15:17
  - Artifact：`/home/debian/automq-workspace/scratch/gcp-2c16g-analysis.py`；`/home/debian/automq-workspace/scratch/gcp-disk-sku-analysis.py`

## 未竟事项
- Kafka Consumer Lag 稿件虽然 revision 33 已完成，但随后复读确认仍偏“设计说明”，尚未形成目标叙事节奏。
  - 原因：需要先按“现象 -> 朴素方案 -> 成本问题 -> 设计推导”重写开头，再扩展到方案与恢复章节。
  - 证据：[Kafka Consumer Lag 中文稿定稿、飞书导入与定向重写](/threads/codex/kafka-consumer-lag-9dd7a1bb)，17:17、17:18
- PR #6117、#6118 和 #3449 已交付但仍处于 Open；Issue #6122 也仍待 triage。
  - 原因：代码/需求已提交，后续状态依赖 reviewer 或产品负责人。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](/threads/codex/gcp-service-account-home-gcp-463388cb)，15:21、15:40；[确认 Codex skills 配置作用域并清理遗留 Lark skills](/threads/codex/codex-skills-lark-skills-b914f3f3)，20:46；[在 AutoMQ/automqbox 创建 Table Topic 自有 Schema Registry 需求 Issue](/threads/codex/automq-automqbox-table-topic-schema-registry-issue-6c4c0e1d)，20:21

## Next Actions
- [ ] 先重写 Kafka Consumer Lag 文章开头至“精确查询成本”一段，确认叙事语气后再扩展到方案和恢复章节。
  - 来源：[Kafka Consumer Lag 中文稿定稿、飞书导入与定向重写](/threads/codex/kafka-consumer-lag-9dd7a1bb)，17:18
- [ ] 确认李振琦已安全保存且能使用 GCP key 后，删除本地 JSON 与临时 tar.gz 副本。
  - 来源：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](/threads/codex/gcp-service-account-home-gcp-463388cb)，10:37；当前两个 `600` 权限副本仍位于 `/home/debian/automq-workspace/scratch/`

## Waiting For
- 等待 AutoMQ reviewers 处理 PR #6117、#6118 和 #3449。
  - 复查条件：出现 review、CI 状态变化或合并结果时复查；当前三条 PR 均为 Open。
- 等待 automqbox 产品负责人 triage Issue #6122，明确协议、鉴权、敏感信息和迁移边界。
  - 复查条件：Issue 被指派、加标签或进入实现计划。
- 等待李振琦确认 GCP key 已安全落地且可用。
  - 复查条件：收到确认后立即清除本地明文及压缩副本。

## 待确认
- Codex skill 数量虽已降至 54，但当天记录明确要求完全重启 Codex 并新建 task 才能验证 Desktop 新会话是否不再出现 warning；证据中没有当天完成重启后的结果。

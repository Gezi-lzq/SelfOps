# GTD 每日回顾 - 2026-07-14

## 昨日推进
- 完成 GCP 运维凭据重建：删除旧 Service Account，新建 `automq-public-dev-ops-authing`，授予项目级 `roles/storage.objectUser`，创建新 key 并通过飞书发送。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](nowledgemem:/threads/codex/gcp-service-account-home-gcp-463388cb)，10:27-10:37
- 触发并跑通 GCP Console 镜像构建与 Home 版本注册；workflow run `29312496876` 成功，Home 注册接口返回 HTTP 200。随后为两条维护分支补齐 GCP 安装页文案，创建 PR #6117/#6118。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](nowledgemem:/threads/codex/gcp-service-account-home-gcp-463388cb)，15:13、15:21、15:40
  - Artifact：[PR #6117](https://github.com/AutoMQ/automqbox/pull/6117)、[PR #6118](https://github.com/AutoMQ/automqbox/pull/6118)
- 完成 GCP 8.x 机型、区域覆盖、价格和磁盘兼容性调研，纠正了“N4D 可直接替代 N2D”的初步判断，收敛为 PD/Hyperdisk 两类 storage profile，并明确 ARM、AKU 标定和 3-zone 覆盖边界。
  - 证据：[AutoMQ GCP 机型筛选与 8.x 候选建议](nowledgemem:/threads/codex/automq-gcp-8-x-89fd4a63)，11:35-15:17
- 完成两组 SQEMS 容量/Heap 复核；定位 US 重启后流量告警的 `condition` 和 labels 配置错误，按真实 Loki/VM 历史窗口回放验证后提交修复 PR。PR #180 当天已合并。
  - 证据：[SQEMS topic 巡检与重启流量告警规则修复](nowledgemem:/threads/codex/sqems-topic-1304fc6c)，15:52-20:14
  - Artifact：[PR #180](https://github.com/AutoMQ/opsbox/pull/180)
- 将 Kafka Consumer Lag 中文稿定向重写并同步到飞书 revision 33，保留图片、公式和链接；随后识别出文章仍偏“设计说明”，并收敛出从 dashboard 反直觉现象逐步推导方案的新叙事路径。
  - 证据：[Kafka Consumer Lag 中文稿定稿、飞书导入与定向重写](nowledgemem:/threads/codex/kafka-consumer-lag-9dd7a1bb)，16:55-17:18
  - Artifact：[飞书文档](https://automq66.feishu.cn/docx/InEVd6qecolSVNxxVaGcsW9Enqf)
- 清理 Codex skill/plugin 配置：Lark skills 从 27 个普通目录收敛为 6 个受管 symlink；将 37 条 workspace skill policy 迁到 user config，使模型可见 skills 从 115 降到 54；卸载 tracing plugin 并保留 Nowledge Mem。
  - 证据：[确认 Codex skills 配置作用域并清理遗留 Lark skills](nowledgemem:/threads/codex/codex-skills-lark-skills-b914f3f3)，20:21-20:39
- 找回并 fast-forward 推送 PR #3449 遗留的 4 个本地 commits；另创建自有 Schema Registry 需求 Issue #6122。
  - 证据：[确认 Codex skills 配置作用域并清理遗留 Lark skills](nowledgemem:/threads/codex/codex-skills-lark-skills-b914f3f3)，20:40-20:46；[创建 Schema Registry 需求 Issue](nowledgemem:/threads/codex/automq-automqbox-table-topic-schema-registry-issue-6c4c0e1d)，20:20-20:21
  - Artifact：[PR #3449](https://github.com/AutoMQ/automq/pull/3449)、[Issue #6122](https://github.com/AutoMQ/automqbox/issues/6122)

## 未竟事项
- Kafka Consumer Lag 文章尚未按新叙事路径完成第二轮重写；revision 33 已清楚，但仍偏设计说明。
  - 原因：当天最后只完成了叙事诊断和结构提案，未出现后续改稿结果。
  - 证据：[Kafka Consumer Lag 中文稿定稿、飞书导入与定向重写](nowledgemem:/threads/codex/kafka-consumer-lag-9dd7a1bb)，17:17-17:18
- PR #6117/#6118 均仍为 Open、Approved；实现已完成，但尚未合并。
  - 原因：等待仓库合并动作。
  - 证据：[GCP Service Account 重建与 Home GCP 版本注册、安装页文案补齐](nowledgemem:/threads/codex/gcp-service-account-home-gcp-463388cb)，15:21、15:40

## Next Actions
- [ ] 按“dashboard 反直觉现象 -> 朴素 timestamp 查询 -> 成本问题 -> Fetch 轨迹与插值 -> 恢复/误差 -> 回到 dashboard”的顺序重写 Kafka Consumer Lag 文章，并同步飞书文档。
  - 来源：当天 17:18 的明确结构提案；Memory 最新口径仍要求突出 Offset Lag 的可解释性与可重建 cache。
- [ ] 确认飞书中的新 Service Account key 已被安全保存后，安全删除本地私钥 `/home/debian/automq-workspace/scratch/automq-public-dev-ops-authing-key-20260714T023335Z.json`。
  - 来源：当天 10:37 明确建议安全清理；当前核验文件仍存在且权限为 `600`。
- [ ] 合并已 Approved 的 PR #6117 和 PR #6118，或确认维护分支是否仍需要两条 PR。
  - 来源：GitHub 当前状态均为 Open、Approved。

## Waiting For
- PR #3449 等待 reviewer 审核。
  - 复查条件：GitHub 当前仍为 Open、`REVIEW_REQUIRED`；7 月 15 日新增修正已通过 CI，因此 7 月 14 日识别的 docs/null-key 收尾不再是你的待办。

## 待确认
- Issue #6122 当前 Open、无 assignee。需确认你只是完成需求登记，还是仍负责推动 triage、协议边界与后续实现。
- GCP 8.x 机型、容量验证与 storage profile 落地虽有明确技术结论，但最新 Memory 已注明自 2026-07-15 起不再由你负责，因此未列入 Next Actions；只有在你明确重新接手时才恢复跟进。

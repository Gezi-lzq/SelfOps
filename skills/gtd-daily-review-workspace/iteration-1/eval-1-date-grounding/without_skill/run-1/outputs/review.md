# GTD 每日回顾：2026-07-14（北京时间）

> 取证窗口：2026-07-14 00:00–24:00 CST（UTC 2026-07-13 16:00–2026-07-14 16:00）。只把窗口内可由 nmem 原始 Thread 内容和可追踪产物确认的状态变化列为完成项。nmem 当前不提供逐消息时间戳，因此无法可靠落入窗口的跨日续聊均未计入。

## 今日推进

### 1. 重建 GCP 开发运维身份并完成交付

- 删除旧 Service Account `automq-public-ops-authing@credit-billing-427603.iam.gserviceaccount.com`，复查已不存在；旧 user-managed key 随账号删除失效。
- 在 `automq-public` 创建 `automq-public-dev-ops-authing@automq-public.iam.gserviceaccount.com`，授予项目级 `roles/storage.objectUser`。
- 创建新 JSON key（Key ID `86886109d7249b8dbc11f5f7102835f569f24ab8`），并于 `2026-07-14 02:36:50 UTC` 通过飞书发送给李振琦；Message ID `om_x100b6a6e42ee04a0c022edb4590902f`。
- 证据：`nowledgemem://thread/codex-019f5e70-fc4e-7203-a1ac-a6d4c1479447`，Thread 创建于 `2026-07-14T02:27:40.717273Z`，消息索引 5、7、11、13、21。

### 2. 打通 Test Home 的 GCP 版本注册链路

- 定位 `Product.NoAvailableVersion` 的直接原因：Pending 环境生成安装脚本时，`saas_product_version` 中没有匹配 `(product, cloudProvider)` 的版本。
- 从 `develop/gcp_docker` 触发 GCP Docker build，GitHub Actions Run `29312496876` 成功；镜像 tag 为 `8.3.0-SNAPSHOT-20260714065004-gcp`，digest 为 `sha256:663541cc60cb4699c4e722fdef5539295e434b9915520bcd4c1149809d5fc32b`。
- `Notify console with version` 成功调用 Test Home Ops API，返回 HTTP 200，trace ID `26a4f825ddf04370919c2ab2d04f771f`，完成 GCP 版本注册。
- 证据：`nowledgemem://thread/codex-019f5e70-fc4e-7203-a1ac-a6d4c1479447`，消息索引 37–52；产物 tag 自带 UTC 时间 `20260714065004`。

### 3. 完成 Home GCP 文案改动并提交两条 PR

- 为 `develop/202605` 完成 Cloud Account ID、GCP Compute Engine 启动按钮和带 Project ID 的链接，创建 PR [AutoMQ/automqbox#6117](https://github.com/AutoMQ/automqbox/pull/6117)，commit `f872fb6217`。
- 为 `develop/gcp_docker` 创建独立 PR [AutoMQ/automqbox#6118](https://github.com/AutoMQ/automqbox/pull/6118)，随后发现该分支没有完整 `scope` 链路，已将 PR 收敛为只改 `en_US.json` 的 5 行文案，移除无效的 `environment.scope` runtime 引用。
- 两条改动均完成 JSON 解析和 `git diff --check`；完整 frontend lint/build 未运行。
- 证据：`nowledgemem://thread/codex-019f5e70-fc4e-7203-a1ac-a6d4c1479447`，消息索引 53–75。

### 4. 创建 Table Topic 自有 Schema Registry 需求

- 在 `AutoMQ/automqbox` 创建 Issue [#6122 Table Topic 支持用户配置自有 Schema Registry](https://github.com/AutoMQ/automqbox/issues/6122)，记录配置入口、鉴权、敏感信息保护、协议兼容与迁移边界。
- 仓库没有 `needs-triage` label，因此 Issue 最终未带该标签；这不是未完成状态。
- 证据：`nowledgemem://thread/codex-019f6091-e7c1-75a3-9079-3ee593752806`，Thread 创建于 `2026-07-14T12:21:48.722313Z`，消息索引 0–5。

### 5. 收敛 Codex skills 与插件配置

- 将 `~/.agents/skills` 中 27 个遗留 Lark directories 收敛为 6 个 manager-managed symlinks，删除其余 21 个；模型可见 skills 从 115 降至 88。
- 将 automq workspace 的 37 条 skill policy 从 project config 迁到 user config，并改为 absolute paths；保留 3 enabled / 34 disabled，模型可见 skills 进一步降至 54。
- 卸载 `tracing@codex-observability-plugin`，清理 cache 和 stale hook trust state；`nowledge-mem@nowledge-community` 保持 installed/enabled。
- 证据：`nowledgemem://thread/codex-019f6092-8b6d-7323-a077-4f08dc10f0d7`，Thread 创建于 `2026-07-14T12:25:23.009605Z`，消息索引 10–25。

## 明确结论

- `scope` 的业务语义是 provider-specific Cloud Account ID，而不是 IAM permission scope；在 GCP 中对应 Project ID。
- `develop/gcp_docker` 尚无完整 Environment scope 数据链路，因此 PR #6118 不能引用 `environment.scope`；当天已采用最小兼容方案修正。
- `Product.NoAvailableVersion` 是产品/云厂商版本记录缺失或不匹配导致，不应从错误名推断为 Broker 版本问题。

## 待跟进

- 确认 PR #6117、#6118 的 CI 与评审结果；#6117 尚未跑完整 frontend lint/build。
- 决定是否向 `develop/gcp_docker` 完整 backport Environment scope 全链路。
- 确认飞书收到并安全保存新 GCP key 后，删除本地 key 文件及临时压缩副本。
- 若希望持续自动注册 GCP Home 版本，需要调整 `cmp-docker-schedule.yaml` 的 matrix 和 ref；当天只完成了一次手工发布与注册。

## 取证备注

- 未把 Thread summary、Working Memory 或长期 Memory 当作完成证明。
- 未纳入 `codex-019f6092-8b6d-7323-a077-4f08dc10f0d7` 中索引 26 之后的工作：该 Thread 可能跨日，而 nmem 缺少逐消息时间戳，无法证明这些推进发生在本回顾窗口内。

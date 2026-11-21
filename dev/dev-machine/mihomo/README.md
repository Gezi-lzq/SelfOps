# Mihomo

管理开发机的 Mihomo TUN、订阅更新和 NetBird 共存策略。

## 当前策略

- Mihomo 监听 localhost，并通过 TUN 接管默认公网流量。
- 私网地址段保持排除，避免 NetBird overlay、容器网络和本机流量进入代理。
- 不注入 NetBird 专用规则；NetBird 的公网控制面、STUN/TURN 和 Relay 流量由订阅原有规则决定。
- 订阅中的代理节点声明按名称稳定排序，消除提供方随机排序造成的伪配置变化。
- 订阅渲染后的配置与当前配置完全一致时，不重启 Mihomo。
- 只有代理入口域名轮换时，默认每 `86400` 秒应用一次；节点、端口、凭证、规则等实质变化仍立即应用。

入口域名刷新间隔可在本机 env 中覆盖：

```bash
MIHOMO_SERVER_REFRESH_INTERVAL=86400
```

## 文件

- `update-mihomo-subscription`：下载订阅、注入本机策略、校验配置并按需重启。
- `install.sh`：安装更新器和 systemd system units。
- `systemd/`：Mihomo 服务及订阅更新 timer。

订阅 URL 只保存在本机：

```text
/etc/mihomo/subscription.env
```

文件格式：

```bash
MIHOMO_SUBSCRIPTION_URL='https://provider.example/subscription'
```

该文件必须由 root 拥有且权限为 `600`，不得提交仓库。

## 安装

```bash
sudo install -d -m 0755 /etc/mihomo
sudo install -m 0600 /dev/null /etc/mihomo/subscription.env
sudoedit /etc/mihomo/subscription.env
sudo ./dev/dev-machine/mihomo/install.sh
```

已有 timer 保持原来的 enabled 状态。首次安装后手动执行更新：

```bash
sudo systemctl start mihomo-subscription.service
```

## 验证

```bash
sudo bash -n /usr/local/sbin/update-mihomo-subscription
sudo /usr/local/bin/mihomo -t -d /etc/mihomo -f /etc/mihomo/config.yaml
systemctl status mihomo mihomo-subscription.timer
netbird status --detail
```

NetBird 建立 P2P 时会显示：

```text
Connection type: P2P
```

回退到 Relay 时，应结合 Mihomo 日志确认公网 Relay 实际命中的策略；不要仅凭 `netbird status` 推断是否使用代理节点。

## DNS 与更新验收（2026-10-18）

- 订阅更新器显式注入 `dns.enable: true`、loopback DNS listener 和 `redir-host`，避免只有 TUN DNS 劫持、没有可用解析器。
- 当前机器 DNS 上游为局域网网关 `10.0.0.1` 和 `1.1.1.1`；代理入口域名使用相同上游。迁移机器前应核对网关。
- NetBird 私有域名继续由 systemd-resolved 的 wt0 专用路由处理；不把私有域名转移到 Meta。
- 更新器用 flock 防止并发，临时订阅和配置使用私有权限。
- 每次应用配置后验证系统域名解析、TUN HTTPS 和显式 HTTP 代理 HTTPS；有界重试失败后恢复旧配置并再次检查。
- 成功配置保留在 `/etc/mihomo/config.yaml.last-known-good`，不纳入 Git。旧配置自身不健康时，回滚仍可能失败，更新器会明确报错。
- 这些检查验证更新时的可用性，不保证未来节点或上游始终可用。

## 主节点组自动切换

- 更新器将 `🔰 选择节点` 固定渲染为 `fallback`，保留订阅中实际节点的候选顺序，最后追加 `DIRECT`；其余业务组保持订阅策略。
- 优先使用排序靠前且探测正常的节点；全部代理候选探测失败时尝试 DIRECT。优先节点恢复后可能自动切回。
- 每 60 秒主动检测，单次超时 5000ms，`lazy: false`。使用直连可达的 `https://www.apple.com/library/test/success.html`，期望 HTTP 200。
- 探测只代表检测地址可达，不能证明节点能访问每个业务目的地；DIRECT 也不能保证原本无法直连的服务恢复。
- 2026-10-18 已验证实际订阅更新、服务重启后组类型及 DIRECT 末位保留；隔离实例使用不可达模拟节点验证自动选择 DIRECT 并完成 HTTPS 请求。未停用正式订阅节点，也未模拟整套外网故障。

## 独立复核补充（2026-10-18）

- 修正 DIRECT 兜底与 Google-only 更新验收冲突：正常状态检查 Google；只有 controller 确认主组已选择 DIRECT、所有代理在同一 Apple 探测下失败、DIRECT 成功且各项记录在 180 秒内时，才可改用 Apple 验证系统 DNS/TUN/HTTP 代理并接受降级，明确输出 DEGRADED 警告。
- 等待探测收敛采用 90 秒窗口，每轮网络调用独立超时，最后一轮可能令总时长超过窗口。controller 设置 secret 时从本机配置读取 Bearer，不输出凭证。
- 隔离测试通过：两个不可达节点自动回退 DIRECT、完整降级验收、controller 认证、拒绝存活节点矛盾状态与过期记录。独立 subagent 完成代码及安全只读复核。
- 未注入生产回滚故障、未停用正式节点、未验证整机重启或异地网络；降级警告目前在 journal，没有额外告警通知。

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

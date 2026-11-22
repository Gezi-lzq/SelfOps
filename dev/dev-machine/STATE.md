# 开发机当前状态

日期：2026-06-06

## 当前状态

- VM：`gezi-dev` / VMID `240`
- 默认用户：`debian`
- 系统盘：`/dev/sda1` 挂载 `/`
- 独占 NVMe：`/dev/nvme0n1` 挂载 `/data`
- SelfOps：`/home/debian/SelfOps`
- Docker data-root：`/data/docker`
- k3s data-dir：`/data/k3s`
- k3s local-path：`/data/volumes/k3s`
- k3s 版本：`v1.35.5+k3s1`
- k3s 节点状态：`Ready`

## 已完成

- 安装并配置 `mise` 开发环境
- 安装并接入 NetBird：`gezi-dev.netbird.cloud`
- 安装 Docker / Compose / Buildx
- 确认目标目录模型：`/home/debian + /data`
- 将 NVMe 从 `/root` 改挂到 `/data`
- 将 SelfOps 迁到 `/home/debian/SelfOps`
- 将 Docker data-root 迁到 `/data/docker`
- 通过 `mise` 安装 base CLI 和 lab CLI
- 通过 apt 安装 `htop`、`ncdu`、`rsync`
- 配置 `gh` 登录 GitHub，并启用 git credential helper
- 添加本地到开发机的 AWS/saml2aws 凭证同步脚本：
  - 脚本：`dev/dev-machine/aws-credentials/sync-to-gezi-dev.sh`
  - 同步文件：`~/.saml2aws`、`~/.aws/config`、`~/.aws/credentials`
  - 远端备份目录：`~/.aws/backups/aws-credentials-<timestamp>/`
  - 已验证 `dev3` profile 可调用 STS
- 安装并认证 `lark-cli`，版本 `1.0.48`
  - bot 身份：ready
  - user 身份：ready
- 创建 `/home/debian/work`
- 为 `/data/services`、`/data/backups` 添加 README
- 部署单机 k3s，data-dir 使用 `/data/k3s`
- 配置 k3s local-path 数据目录为 `/data/volumes/k3s`
- 保留 Traefik 作为默认 Ingress
- 验证 local-path PVC：
  - smoke Pod 输出 `ok`
  - PVC 目录创建在 `/data/volumes/k3s`
  - 删除 Namespace 后测试目录已回收

## 待完成

- [ ] 后续按需评估 `cloudflare-tunnel-ingress-controller`

## 2026-11-22 T3 Code / T3 Connect

- 开发机 gezi-dev 已安装 T3 Code CLI 0.1.11，配置为 systemd 用户服务。T3 Connect 已启用，LAN 暴露保持关闭。
- 开发机的 mihomo TUN 曾将 Cloudflare Tunnel 流量送入代理路径，导致 `TLS handshake with edge error: EOF`。已在 `/etc/mihomo/config.yaml` 和 `/usr/local/sbin/update-mihomo-subscription` 的规则中加入 `v2.argotunnel.com`、`argotunnel.com` 的 `DIRECT` 规则。
- 当前开发机验证为 `Tunnel connected · 4 connections · HTTP2`，`mihomo` 与 `t3code` 服务均正常。
- 本地 MacBook 的 Clash Verge TUN 存在相同问题。已在 Clash Verge 当前规则 profile 和活动配置中加入同样的 `DIRECT` 规则，并重载配置。
- 当前 MacBook 验证为 `Tunnel connected · 2 connections · HTTP2`。
- 未记录 T3 Connect 授权码、订阅 URL 或其他凭证。

## 2026-11-22 Linked environments

- MacBook 与 gezi-dev 已建立 T3 Code Linked environments 连接。
- 当前连接可达，权限为 `full-access`，有效期至 2026-12-22。
- 两台机器的 T3 Connect 隧道保持正常，LAN 暴露保持关闭。

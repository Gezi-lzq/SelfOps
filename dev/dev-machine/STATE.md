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
- 完成 k3s 最小应用实验：
  - Ingress smoke app 可通过 Traefik + NetBird IP 访问
  - Redis StatefulSet 可使用 local-path PVC
  - 删除 StatefulSet 后 PVC 会保留，需显式删除 PVC 或 Namespace
  - 删除 PVC 后 `/data/volumes/k3s` 测试目录会回收

## 待完成

- [ ] 评估 NetBird Reverse Proxy 作为当前阶段公网入口
- [ ] 有自有域名 / Cloudflare zone 后，再评估 `cloudflare-tunnel-ingress-controller`

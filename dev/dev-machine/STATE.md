# 开发机当前状态

日期：2026-06-06

## 当前状态

- VM：`gezi-dev` / VMID `240`
- 默认用户：`debian`
- 当前 NVMe 挂载：`/root`
- 目标 NVMe 挂载：`/data`
- 当前 SelfOps：`/root/SelfOps`
- 目标 SelfOps：`/home/debian/SelfOps`

## 已完成

- 安装并配置 `mise` 开发环境
- 安装并接入 NetBird：`gezi-dev.netbird.cloud`
- 安装 Docker / Compose / Buildx
- Docker 当前 data-root：`/root/docker-data`
- 确认目标目录模型：`/home/debian + /data`
- 本机已确认有 `lark-cli`，版本 `1.0.46`

## 待完成

- [ ] 将 NVMe 从 `/root` 改挂到 `/data`
- [ ] 将 SelfOps 迁到 `/home/debian/SelfOps`
- [ ] 将 Docker data-root 迁到 `/data/docker`
- [ ] 通过 `mise` 安装 base CLI 和 lab CLI
- [ ] 通过 apt 安装 `htop`、`ncdu`
- [ ] 在开发机上安装并认证 `lark-cli`
- [ ] 部署单机 k3s，data-dir 使用 `/data/k3s`
- [ ] 配置 k3s local-path 数据目录为 `/data/volumes/k3s`
- [ ] 保留 Traefik 作为默认 Ingress
- [ ] 后续按需评估 `cloudflare-tunnel-ingress-controller`

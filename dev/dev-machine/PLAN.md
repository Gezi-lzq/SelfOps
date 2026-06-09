# 开发机目标状态

日期：2026-06-09

目标：把 `gezi-dev` 作为长期个人开发机，用 SelfOps 记录配置、依赖和关键变更。

## 机器

- VM：`gezi-dev` / VMID `240`
- PVE 节点：`pve1`
- SSH：`ssh gezi-dev`
- IP：`10.1.0.240/24`
- 系统：Debian 13.5
- 规格：16 cores / 32 GiB
- 系统盘：100 GiB
- 独占 NVMe：Samsung 990 PRO 1 TB

## 用户

- 默认操作用户：`debian`
- `root` 仅用于系统恢复和底层管理
- Docker、kubectl、代码开发都应由 `debian` 执行

## 目录

```text
/home/debian/
├── SelfOps/        # 管理仓库
└── work/           # 代码和开发工作区

/data/
├── docker/         # Docker data-root
├── k3s/            # k3s data-dir
├── services/       # 服务定义
├── volumes/        # 服务数据
├── backups/        # 备份
└── scratch/        # 临时实验
```

## 依赖

应由 SelfOps 记录和管理：

- `mise`
- 基础开发工具：`git`、`curl`、`build-essential` 等
- Docker / Compose / Buildx
- NetBird
- `mihomo`
- k3s
- base CLI：`kubectl`、`helm`、`k9s`、`stern`、`jq`、`yq`、`rg`、`fd`、`fzf`、`tmux`、`gh`
- lab CLI：`cloudflared`、`sops`、`age`、`restic`、`rclone`
- 业务 CLI：`lark-cli`
- AI API gateway：`CLIProxyAPI`
- apt 工具：`htop`、`ncdu`
- 后续可选：`cloudflare-tunnel-ingress-controller`、`metrics-server`、`cert-manager`

其中 base CLI、lab CLI 和 `lark-cli` 优先由 `dev/environment/config.toml` 的 `mise` 全局配置管理。
`lark-cli` 作为 `npm:@larksuite/cli` 管理；认证状态不写入仓库。
`CLIProxyAPI` 不走 `mise`，按官方 Linux installer 管理；本地 API key、OAuth 凭据和 provider token 不写入仓库。
`metrics-server`、`cert-manager` 属于 k3s 集群组件，不作为本机 CLI 安装。

## 运行时约定

- Docker 数据放 `/data/docker`
- k3s 数据放 `/data/k3s`
- k3s PVC/local-path 数据放 `/data/volumes/k3s`
- 长期服务定义放 `/data/services` 或纳入 SelfOps
- 大块数据不要放 100 GiB 系统盘
- 敏感信息不写入仓库

## k3s

- 用作单机开发集群
- 保留默认 Traefik
- 使用默认 local-path-provisioner，不上 Longhorn
- StorageClass 支持本地 dev/test StatefulSet 和 PVC
- 重要数据靠应用级备份或手动导出，不依赖存储层高可用

## 访问方式

- 私有访问：NetBird 访问 `gezi-dev` 和 Traefik 暴露的服务
- kubectl：后续通过 NetBird IP / DNS 访问 k3s API
- 临时公网：可使用 NetBird Reverse Proxy 或临时 tunnel
- 长期公网：可选 `cloudflare-tunnel-ingress-controller`
- 不默认把 k3s Pod CIDR / Service CIDR 发布到 NetBird

Ingress 约定：

- Traefik 作为默认内网入口
- Cloudflare Tunnel Ingress Controller 只用于需要公网域名的服务
- Cloudflare token 等敏感信息只放 Kubernetes Secret，不写入仓库

## 扩容

当前先保持 16 cores / 32 GiB。

如后续 k3s、Docker 服务或构建任务有内存压力，优先扩到 64 GiB；CPU 暂不优先扩。

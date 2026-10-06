# 开发机目标状态

日期：2026-07-27

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
├── work/           # 代码和开发工作区
└── automq-workspace -> /data/home/debian/automq-workspace

/data/
├── home/debian/automq-workspace/ # AutoMQ 开发工作区实际数据
├── docker/         # Docker data-root
├── containerd/     # system containerd image/snapshot data
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
- system containerd 数据放 `/data/containerd`，避免 image/snapshot 占用系统盘
- Docker 默认 `json-file` 日志限制为 `50m × 3`；journald 上限为 1 GiB，并为系统盘保留 10 GiB 空闲
- `/data/swapfile` 提供 8 GiB Swap，`vm.swappiness=10`
- NetBird 与 QEMU Guest Agent 使用 `OOMScoreAdjust=-750`；OpenSSH 保留自身更强的 OOM 保护
- k3s 数据放 `/data/k3s`
- k3s PVC/local-path 数据放 `/data/volumes/k3s`
- AutoMQ 开发工作区实际数据放 `/data/home/debian/automq-workspace`，并通过
  `/home/debian/automq-workspace` symlink 保持兼容路径
- 长期服务定义放 `/data/services` 或纳入 SelfOps
- 大块数据不要放 100 GiB 系统盘
- 敏感信息不写入仓库

## Cloud Storage

- 通过 `dev/dev-machine/cloud-storage` 维护 Agent 文件上传和异地备份约定。
- 当前目标 provider 为 Google Drive；上传和备份默认通过 `rclone` 直接传输，不依赖挂载路径，也不增加 mise wrapper。
- rclone remote 计划命名为 `gdrive`，机器远端根目录为 `gdrive:gezi-dev/`。
- `uploads/` 用于按需上传，`backups/` 用于固定目标的覆盖式备份。
- 单文件默认使用 `rclone copyto`，目录默认使用 `rclone copy`；不会默认使用带远端删除语义的 `rclone sync`。
- 定期备份按明确的源目录分别建立 systemd user service/timer，不自动备份整个 Home。
- 可选将 `gdrive:gezi-dev` 挂载到 `/home/debian/Drive`；VFS 缓存放 `/data/scratch`，mount service 默认不启用。
- OAuth token、remote 配置和其他凭证仅保存在本机，不写入 SelfOps。

## k3s

- 用作单机开发集群
- 保留默认 Traefik
- 使用默认 local-path-provisioner，不上 Longhorn
- StorageClass 支持本地 dev/test StatefulSet 和 PVC
- 重要数据靠应用级备份或手动导出，不依赖存储层高可用

## 访问方式

- 私有访问：NetBird 访问 `gezi-dev` 和 Traefik 暴露的服务
- kubectl：后续通过 NetBird IP / DNS 访问 k3s API
- 主要公网出口：维护 `ngrok -> 127.0.0.1:8780 Caddy router`，由 Caddy 按 path
  反代到本机服务
- 浏览器 Herdr 入口：通过同一个 Caddy router 暴露 `/`、`/history`、`/terminal/`、
  `/terminal-mobile/`；ttyd 必须启用 basic auth，ngrok token 和 ttyd 密码不写入仓库
- 临时公网备用：cloudflared quick tunnel 指向同一个 `127.0.0.1:8780` Caddy router
- 长期公网：可选 `cloudflare-tunnel-ingress-controller`
- 不默认把 k3s Pod CIDR / Service CIDR 发布到 NetBird

Ingress 约定：

- Traefik 作为默认内网入口
- Cloudflare Tunnel Ingress Controller 只用于需要公网域名的服务
- Cloudflare token 等敏感信息只放 Kubernetes Secret，不写入仓库

## 扩容

当前先保持 16 cores / 32 GiB。

如后续 k3s、Docker 服务或构建任务有内存压力，优先扩到 64 GiB；CPU 暂不优先扩。

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
- 通过 `mise` 安装 Terraform，版本 `1.13.3`
- 通过 `mise` 安装 `just`，版本 `1.51.0`
- 通过 apt 安装 `htop`、`ncdu`、`rsync`
- 配置 `gh` 登录 GitHub，并启用 git credential helper
  - 登录用户：`Gezi-lzq`
  - token scope 包含 `repo`
- 配置 GitHub SSH over 443
  - SSH Host：`github.com` -> `ssh.github.com:443`
  - SSH 用户：`git`
  - IdentityFile：`~/.ssh/id_ed25519_github`
  - 已添加 `ssh.github.com:443` known_hosts
  - `ssh -T git@github.com` 已验证为 `Gezi-lzq`
  - 已移除 GitHub SSH 到 HTTPS 的全局 rewrite
- 安装并配置 Codex CLI，版本 `0.137.0`
  - 配置位置：`/home/debian/.codex/config.toml`
  - provider：`https://muyuan.do/v1`
  - 使用 HTTP Responses，关闭 WebSocket
  - smoke test 返回 `ok`
- 安装并认证 `lark-cli`，版本 `1.0.48`
  - bot 身份：ready
  - user 身份：ready
- 安装并配置 Multica CLI，版本 `0.3.17`
  - server_url：`https://api.multica.ai`
  - app_url：`https://multica.ai`
  - 登录用户：`zhenqi Li (lzqtxwd@gmail.com)`
  - Workspace：`lzqtxwd's Workspace`
  - Workspace ID：`bdc30359-b067-46aa-b892-7848f9b091e8`
  - daemon 由 systemd user service 管理：`~/.config/systemd/user/multica.service`
  - 已启用 `loginctl enable-linger debian`
  - systemd PATH 包含 mise Node 目录，确保 daemon 能找到 `codex`
  - 当前 Agents：`codex`
  - 当前 Workspaces：`1`
  - task wakeup websocket 已连接
  - repo cache 已能通过 GitHub SSH 访问 `AutoMQ/automq`、`AutoMQ/automqbox`、`AutoMQ/automq-kafka-enterprise`
- 安装 Matt Pocock skills 到 `.agents`
  - 来源：`https://github.com/mattpocock/skills`
  - 源仓库：`/home/debian/.agents/sources/mattpocock-skills`
  - 生效目录：`/home/debian/.agents/skills`
  - 安装方式：非 deprecated skills 以软链接方式接入
  - 当前 commit：`be55a79`
  - 当前数量：`25`
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
- 部署第一个长期 k3s 应用：`homepage`
  - 用作开发机入口页
  - 无 PVC
  - Ingress host：`home.gezi-dev.local`
  - 通过 Traefik + NetBird IP 访问返回 HTTP 200
- 添加 NetBird Terraform 目录：
  - `dev/dev-machine/terraform/netbird`
  - 用于管理 Homepage Reverse Proxy
- 试用 NetBird Reverse Proxy：
  - Service：`gezi-dev-home`
  - Domain：`gezi-dev-home.eu1.netbird.services`
  - 目标：`gezi-dev:80`
  - 已通过 Terraform destroy 删除
  - 结论：访问体验偏卡，当前不采用
  - state 保留在开发机本地，不提交仓库
- 恢复 Homepage Ingress 和 `HOMEPAGE_ALLOWED_HOSTS`，仅保留内网访问 Host

## 待完成

- [ ] 有自有域名 / Cloudflare zone 后，再评估 `cloudflare-tunnel-ingress-controller`

# Self-Hosted Runners

声明式管理 GitHub Actions self-hosted runner，通过 mise task 驱动，幂等执行。

## 目标机

`laptop-rltvvlg6-60-231.netbird.cloud` (Ubuntu 22.04)

## 当前声明

见 [`runners.toml`](./runners.toml)

| ID | 仓库 | 安装路径 |
|----|------|---------|
| selfops | Gezi-lzq/SelfOps | `/home/gezi/actions-runner-selfops` |

## 使用

在目标机的 SelfOps 仓库目录下执行：

```bash
# 确保所有声明的 runner 已注册并运行（幂等）
mise -C infra/runners run runner:ensure

# 查看状态
mise -C infra/runners run runner:status

# 确保单个 runner
mise -C infra/runners run runner:ensure-one selfops

# 移除某个 runner
mise -C infra/runners run runner:remove selfops
```

## 依赖

- `gh` CLI（已认证，用于获取 registration/remove token）
- `systemd`（管理 runner 服务生命周期）
- `curl`（下载 runner 二进制）

## 新增 Runner

1. 在 `runners.toml` 中添加声明
2. 在目标机执行 `mise -C infra/runners run runner:ensure`

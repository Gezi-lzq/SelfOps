# NetBird Terraform

管理 `gezi-dev` 相关的 NetBird 配置。

当前状态：NetBird Reverse Proxy 已试用后放弃，默认不创建资源。

## 前置条件

- NetBird PAT，通过环境变量提供：

```bash
export NB_PAT="..."
```

- 如非 NetBird Cloud，额外设置：

```bash
export NB_MANAGEMENT_URL="https://netbird.example.com"
```

## 计划

```bash
terraform init
terraform plan
```

## 试用 Homepage Reverse Proxy

```bash
terraform apply \
  -var='enable_homepage_reverse_proxy=true'
```

Terraform 会：
- 查找 peer：`gezi-dev`
- 使用 NetBird free reverse proxy domain
- 创建 HTTP Reverse Proxy Service：`gezi-dev-home`
- 将公网请求转发到 `gezi-dev:80`
- 开启 `pass_host_header` 和 `rewrite_redirects`
- 开启 password auth

## 敏感信息

- NetBird PAT 不写入仓库，使用 `NB_PAT`
- Reverse Proxy password 不写入仓库，使用 Terraform sensitive variable
- `terraform.tfvars` 和 state 文件不提交
- `.terraform.lock.hcl` 应提交，用于锁定 provider 版本和校验和

示例：

```bash
terraform apply \
  -var='homepage_proxy_password=change-me'
```

## 试用记录

2026-06-06 首次执行 `terraform plan` 成功，计划只创建 `netbird_reverse_proxy_service.homepage`。

第一次 `terraform apply` 创建服务时报错：

```text
permission denied
```

调整 PAT 为 admin 后，创建权限问题解决。

随后发现 provider/API 实际需要把 `domain` 传成完整域名：

```text
gezi-dev-home.eu1.netbird.services
```

而不是仅传 base domain `eu1.netbird.services`。

曾创建：

```text
gezi-dev-home.eu1.netbird.services
```

试用结论：该方案访问体验偏卡，当前不采用。

Reverse Proxy Service 已通过 Terraform destroy 删除。Terraform 默认 `enable_homepage_reverse_proxy=false`，避免误创建。

本地 `terraform.tfstate` 保留在开发机该目录下，不提交仓库。

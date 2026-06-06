# NetBird Terraform

管理 `gezi-dev` 相关的 NetBird 配置。

当前目标：为 Homepage 创建 NetBird Reverse Proxy 公网入口。

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

## 创建 Homepage Reverse Proxy

```bash
terraform apply
```

Terraform 会：
- 查找 peer：`gezi-dev`
- 使用 NetBird free reverse proxy domain
- 创建 HTTP Reverse Proxy Service：`gezi-home`
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

## 后续

创建成功后，读取 output 的公网域名，并同步到 Homepage：
- `HOMEPAGE_ALLOWED_HOSTS`
- Ingress host

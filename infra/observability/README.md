# Observability Stack

WSL2 可观测基础设施：node_exporter + VictoriaMetrics + VictoriaLogs + Grafana

## 架构

```
node_exporter → VictoriaMetrics (scrape + 存储, 保留 1 个月) ← Grafana
                VictoriaLogs    (日志存储, 保留 7 天, 暂未接入)  ←┘
```

## 采集内容

| 类型 | 来源 | 目标 |
|------|------|------|
| Metrics | node_exporter (CPU/内存/磁盘/网络) | VictoriaMetrics |

采集间隔：30s。VictoriaMetrics 通过内置 `-promscrape.config` 直接 scrape node_exporter。

## 目录结构

```
SelfOps/infra/observability/
├── docker-compose.yml
├── prometheus.yml                # VictoriaMetrics scrape 配置
├── .env                          # Grafana admin 密码（已 gitignore）
├── .gitignore
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yaml  # VictoriaMetrics + VictoriaLogs 数据源
│       └── dashboards/
│           ├── dashboards.yaml   # Dashboard provisioning 配置
│           └── node-exporter.json # Node Exporter Full 大盘
└── README.md
```

数据持久化在 `~/.observability/`：

```
~/.observability/
├── victoria-metrics/    # 指标时序数据
├── victoria-logs/       # 日志数据
└── grafana/             # 大盘配置、插件（需 UID 472 权限）
```

## 端口

| 服务 | 端口 | 绑定 | 说明 |
|------|------|------|------|
| Grafana | 3000 | 0.0.0.0 | Web UI，唯一对外暴露 |
| VictoriaMetrics | 8428 | 内部网络 | Prometheus 兼容 API + scrape |
| VictoriaLogs | 9428 | 内部网络 | Loki 兼容 push API |
| node_exporter | 9100 | 内部网络 | 系统指标采集 |

## 内存限制

| 组件 | 限制 |
|------|------|
| VictoriaMetrics | 384MB |
| VictoriaLogs | 256MB |
| Grafana | 256MB |
| node_exporter | 32MB |

## 使用

通过 mise tasks 管理（在 SelfOps 根目录执行）：

```bash
mise run obs:up       # 启动
mise run obs:down     # 停止
mise run obs:status   # 查看容器状态
mise run obs:logs     # 查看日志
mise run obs:expose   # Cloudflare quick tunnel 暴露 Grafana
```

> **前置条件**：`~/.bashrc` 中需要在 `[ -z "$PS1" ] && return` 之前添加
> `export PATH="$HOME/.local/bin:$PATH"`，确保非交互式 shell 能找到 mise 二进制。

## 首次部署

```bash
# 1. 创建数据目录
mkdir -p ~/.observability/{victoria-metrics,victoria-logs,grafana}

# 2. 修复 Grafana 数据目录权限（容器内 UID 472）
sudo chown -R 472:472 ~/.observability/grafana

# 3. 创建 .env 文件
echo 'GF_ADMIN_PASSWORD=<your-password>' > .env

# 4. 启动
docker-compose up -d

# 5.（可选）通过 Cloudflare quick tunnel 暴露
cloudflared tunnel --url http://localhost:3000
```

## 外部访问

通过 Cloudflare quick tunnel 暴露 Grafana：

```bash
mise run obs:expose
# 或直接
cloudflared tunnel --url http://localhost:3000
```

Quick tunnel 域名是临时的，每次重启会变。进程需要保持前台运行。

# Bub Agents

基于 [bub](https://github.com/bubbuild/bub) 框架的 agent 声明式部署，使用官方镜像 `ghcr.io/bubbuild/bub:latest`，按 profile 隔离运行。

## 目录结构

```
agents/bub/
  docker-compose.yml       # 公共服务定义，通过 ${PROFILE} 参数化
  deploy.sh                # 部署脚本：同步 profile 私有 selfops + 建软链接 + compose up
  backup.sh                # tape 备份到 GitHub Releases
  startup.sh               # 通用启动入口（默认 apply + bub gateway）
  mise.toml                # mise tasks: bub:deploy, bub:write-env, bub:backup
  plugins/                 # 自定义 Bub 插件源码根目录
  profiles/
    yuna/
      AGENTS.md            # agent 人设（读写挂载，agent 可修改）
      bub-reqs.txt         # 插件依赖
      projects.toml        # profile 级 skills 清单，startup 时 apply
      startup.sh           # profile 启动入口
      env.template         # 环境变量模板，secrets 通过 envsubst 渲染
      docker-compose.yml   # profile 级 compose override（宿主工具挂载等）
    automq-ops/
      AGENTS.md
      bub-reqs.txt
      env.template
      docker-compose.yml   # 也可覆盖 startup.sh 等公共挂载
      startup.sh
```

## Runtime 布局

部署后目标机上的 runtime 目录：

```
/opt/bub/profiles/<profile>/
  env                      # 渲染后的环境变量文件
  workspace/               # bub workspace
  home/                    # 容器 /root
  cache/pip/               # pip 缓存
  cache/uv/                # uv 缓存
```

`workspace/` 下会保留一份 profile 私有、持久化的 `selfops/` clone。`deploy.sh` 会在宿主机侧：

1. 同步 `/opt/bub/profiles/<profile>/workspace/selfops` 到 `${SELFOPS_REPO_BRANCH}`
2. 将 `/workspace/AGENTS.md`、`/workspace/bub-reqs.txt`、`/workspace/plugins`、`/workspace/startup.sh` 软链接到 `selfops` clone 内对应路径
3. 启动容器，容器内 `/workspace/startup.sh` 指向 profile 自己的 `startup.sh`

profile 启动脚本负责执行 `agent_runtime.py apply --projects ...` 和 profile 自己的业务逻辑。

## 使用

```bash
# 部署指定 profile
mise -C agents/bub run bub:deploy yuna

# 渲染 env 文件（需要 secrets 环境变量）
mise -C agents/bub run bub:write-env yuna

# 备份 tape
mise -C agents/bub run bub:backup yuna
```

## 新增 Profile

1. 创建 `profiles/<name>/` 目录
2. 添加 `AGENTS.md`、`bub-reqs.txt`、`env.template`、`projects.toml`、`startup.sh`
3. 如需额外挂载或覆盖公共挂载，添加 `docker-compose.yml` override
4. 在 GitHub repo settings 配置对应 secrets
5. 执行 `mise -C agents/bub run bub:deploy <name>`

## 插件管理

- 官方插件继续通过各 profile 的 `bub-reqs.txt` 声明安装，不做 commit pin。
- 自定义插件源码统一放在 `agents/bub/plugins/`。
- profile 通过 `bub-reqs.txt` 中的 `file:///workspace/plugins/<plugin-dir>` 引用需要启用的自定义插件。
- `deploy.sh` 会把 `/workspace/plugins` 软链接到 profile 私有 clone 内的 `agents/bub/plugins/`。
- 部署时会强制重建容器，避免单文件 bind mount 的 `bub-reqs.txt` 在运行容器里继续指向旧 inode。

## Workflows

- `bub-deploy.yml` — push 到 main 且 `agents/bub/**` 或 `dev/agent-runtime/**` 变化时自动部署
- `bub-tape-backup.yml` — 每 6 小时备份 tape 到 GitHub Releases

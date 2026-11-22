# T3 Code 功能与当前配置调研

更新时间：2026-11-22

本文基于 T3 Code 官方仓库文档整理。配置状态来自当前 MacBook 和 `gezi-dev` 的实际检查。

## 1. 产品模型

T3 Code 的服务端运行在实际执行代码的机器上。桌面端、Web 端和移动端负责控制服务端上的项目、线程、代理和浏览器。代码、provider 凭证、线程和 agent 工作保留在对应环境的机器上。

官方文档：[安装与运行模型](https://github.com/pingdotgg/t3code/blob/main/docs/user/install.md)

## 2. 安装与常驻运行

- Linux、macOS 和 Windows 支持命令行安装。
- `t3 serve` 在当前终端启动服务。
- `t3 up` 配置远程访问，并按选择安装后台服务。
- `t3 service install` 安装常驻服务。
- `t3 update` 更新 T3 Code。
- `t3 doctor` 检查和修复 T3 数据目录。
- Linux 后台服务使用 systemd user service。服务可通过 `t3 service protect` 配置内存保护。

官方文档：[安装](https://github.com/pingdotgg/t3code/blob/main/docs/user/install.md)、[后台服务](https://github.com/pingdotgg/t3code/blob/main/docs/user/background-service.md)

## 3. 远程访问

T3 Code 支持多种访问路径。T3 Connect、LAN/tailnet 配对、Tailscale HTTPS、SSH-managed environment 和直接 HTTPS 路由可以同时存在。客户端会按路由状态选择可用路径。

### T3 Connect

- 通过账号把环境发布到其他桌面端、Web 端和移动端。
- 主机运行 `t3 connect` 或 `t3 up --connect`。
- 主机需要保持运行，T3 Code 服务和 Cloudflare Tunnel 都必须可用。
- 设备授权和配对码属于敏感凭证。
- 官方限制为每个账号最多连接 3 台机器。T3 Chat 套餐提高上限。

### LAN/tailnet 配对

- `t3 up --lan` 开启局域网和 tailnet 访问。
- `t3 pair` 生成一次性配对链接。
- 配对码只授权客户端访问，不会让不可达的主机变得可达。

### SSH-managed environment

桌面端可以通过 SSH 启动或复用远端 T3 Code 服务。项目、provider 凭证和 agent 工作仍保留在远端主机。

官方文档：[远程访问](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md)、[T3 Connect 排障](https://github.com/pingdotgg/t3code/blob/main/docs/user/t3-connect-troubleshooting.md)

## 4. Linked environments

Linked environments 是 beta 功能，用于让一台环境中的 agent 在另一台环境上启动、发送消息、等待和停止线程，并管理队列、项目和计划任务。

- 两台机器都需要在 Settings → Labs 开启。
- 连接有效期为 30 天。
- 访问级别从 read-only 到 full-access。
- 远端 agent 不能超过发起端 agent 自身的权限。
- full-access link 可以执行远端机器上的完整 agent 操作。

这项能力与 T3 Connect 不同。T3 Connect 负责环境可达性，Linked environments 负责跨环境的 agent 调度。

官方文档：[Linked environments](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md#link-another-environment)

## 5. Provider 与模型

T3 Code 通过 provider CLI 或托管运行时启动 coding agent。支持的 provider 包括 Codex、Claude、Cursor、Grok Build、Kiro、OpenCode、Antigravity、Pi、Muse Code、fx 和 ACP Registry agents。

- provider CLI 必须位于服务端非交互 shell 的 `PATH` 中。
- provider 安装、登录和配置属于实际运行环境。
- 远程环境需要在远端机器配置 provider。
- 一个 provider 可以配置多个实例，用于不同账号或不同环境变量。
- provider 凭证保存在服务端，不随移动端或控制端迁移。

官方文档：[安装与 Providers](https://github.com/pingdotgg/t3code/blob/main/docs/user/install.md)、[Pi provider](https://github.com/pingdotgg/t3code/blob/main/docs/user/providers-pi.md)

## 6. 权限模式

权限模式控制 agent 何时需要用户批准：

- `Supervised`：命令和文件改动需要批准。
- `Auto-accept edits`：文件编辑自动批准，其他动作仍可能需要批准。
- `Auto`：使用 provider 的自动审查能力处理常规动作。
- `Full access`：命令和文件改动不弹出批准。

权限模式按线程生效。新线程使用 Settings → General → New threads 中的默认值，项目可以覆盖环境默认值。

官方文档：[Permission modes](https://github.com/pingdotgg/t3code/blob/main/docs/user/permission-modes.md)

## 7. Threads、Projects 和 Worktrees

- Thread 是一次 agent 工作会话。
- Project 绑定代码目录、动作脚本、默认模型、权限和源代码设置。
- New worktree 为独立任务创建分支和工作目录。
- 主 checkout 中的线程可以直接使用现有工作树。
- Worktree 默认位于 T3 home 的 `worktrees` 目录，也可以改到指定路径。
- 支持后台线程、线程归档、线程分组、计划任务和跨设备查看。
- 可配置自动清理长期不活跃的 worktree。

官方文档：[Threads](https://github.com/pingdotgg/t3code/blob/main/docs/user/thread-sidebar.md)、[Project settings](https://github.com/pingdotgg/t3code/blob/main/docs/user/project-settings.md)

## 8. Git 与 Pull Request

T3 Code 集成 GitHub、GitLab、Forgejo、Gitea、Bitbucket、Azure DevOps、GitCafe 和 Cursor Origin。支持克隆仓库、创建分支和 worktree、查看 diff、创建和审查 Pull Request、评论和合并。

Git 凭证和 provider 配置都在实际运行环境配置。远端环境不能直接复用本机的 Git 登录态。

官方文档：[Source control](https://github.com/pingdotgg/t3code/blob/main/docs/user/source-control.md)

## 9. Browser 与 HTML renders

T3 Code 提供环境级 headless browser。浏览器标签属于环境，因此移动端、Web 端和桌面端可以查看远端环境的浏览器状态。HTML renders 用于把页面渲染为可检查的图像或内嵌预览。

浏览器首次使用会在主机下载 headless Chrome。部分 Linux 主机需要执行 `t3 browser setup`。浏览器访问和项目配置按环境生效。

官方文档：[Remote access 中的 Browser](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md#browser-on-a-remote-environment)、[HTML renders](https://github.com/pingdotgg/t3code/blob/main/docs/user/html-renders.md)

## 10. Outside agents 与 MCP

Claude Code、Codex、ChatGPT 和其他 MCP 客户端可以连接 T3 Code 环境，读取项目和线程、启动和发送线程、查询 provider 和模型。

- MCP URL 是环境地址加 `/mcp`。
- T3 Connect 环境使用 T3 Connect HTTPS 地址。
- hosted agent 不能使用仅在本机或 tailnet 可达的地址。
- 外部 agent 的权限由授权时选择的 read-only、Supervised、Auto-accept edits、Auto 或 Full access 决定。
- subagent、secret request、浏览器预览、HTML render 和 worktree handoff 等需要在 T3 thread 内运行的能力，外部 MCP agent 不能直接调用。

官方文档：[Outside agents](https://github.com/pingdotgg/t3code/blob/main/docs/user/outside-agents.md)

## 11. 当前配置状态

### MacBook

- T3 Code desktop app 已运行。
- T3 CLI 版本为 `0.1.11`。
- 本机 Codex CLI 版本为 `0.171.0`。
- T3 Connect 已启用并授权。
- Clash Verge TUN 会接管公网流量。
- 已在活动规则 profile 和活动配置中为 `v2.argotunnel.com`、`argotunnel.com` 加入 `DIRECT` 规则。
- 已验证 `Tunnel connected · 2 connections · HTTP2`。
- 已通过 T3 Connect 建立 Linked environments 连接到 gezi-dev，权限为 `full-access`，有效期至 2026-12-22。
- MacBook 没有安装 T3 后台 service，桌面应用退出或本机注销会影响可达性。

### gezi-dev

- T3 Code CLI 版本为 `0.1.11`。
- 已安装并运行 systemd user service `t3code.service`。
- T3 Connect 已启用，LAN/tailnet 暴露关闭。
- 远端已有 Codex CLI `0.171.0`，与 MacBook 当前版本一致。
- mihomo TUN 会接管公网流量。
- 已在 `/etc/mihomo/config.yaml` 和 `/usr/local/sbin/update-mihomo-subscription` 中为 `v2.argotunnel.com`、`argotunnel.com` 加入 `DIRECT` 规则。
- 已验证 `Tunnel connected · 4 connections · HTTP2`。
- Linked environments 开关已启用。
- 远端 T3 服务通过 T3 Connect 可被其他设备访问。

### 记录与分支

- 本地 SelfOps 的机器记录已推送到 `main`。
- 开发机 SelfOps 的机器记录已推送到 `machine/gezi-dev`。
- 两个分支保持独立。
- T3 Connect 授权码、订阅 URL 和其他凭证未写入文档。

## 13. 当前 Project 默认值

- gezi-dev 环境默认新 Thread 使用 worktree，并从远端默认分支创建新 worktree。
- SelfOps 使用主 checkout `/home/debian/SelfOps`。
- 其他六个代码 Project 使用 worktree 模式。
- 当前环境权限保持 `full-access`。
- Project API 未保存项目级模型覆盖，Project 继承 gezi-dev 环境默认模型。当前 gezi-dev 能力列表提供 GPT-6.2-Sol。
- 项目动作脚本和物理 worktree 根目录尚未配置。
- 已完成 `automq-workspace` Worktree 试点。线程使用 `gpt-6.2-sol` 和 `full-access`，从 `origin/private/gezi--workspace-overlay` 创建 `t3/verify-automq-workspace`，远程工作区干净，未产生修改。

## 12. 当前未完成项

- MacBook 与 gezi-dev 已建立 Linked environments 连接。当前 MacBook 可达 gezi-dev，权限为 `full-access`，有效期至 2026-12-22。
- MacBook 没有安装后台 service。需要手机在 MacBook 注销或桌面应用退出后仍能访问时，应评估安装 macOS 后台服务。
- 尚未验证两个环境的外部 agent MCP 授权流程。
- 尚未建立项目级 `t3.json`、动作脚本、worktree 清理策略和计划任务。
- 已确认 Worktree 创建链路正常。下一步按真实任务创建正式线程，再为已有且稳定的构建或测试入口配置 Project actions。
- T3 Connect 依赖 Cloudflare Tunnel 网络可达。Clash Verge 和 mihomo 的 TUN 规则需要在配置生成链路中保持 `argotunnel.com` 直连。

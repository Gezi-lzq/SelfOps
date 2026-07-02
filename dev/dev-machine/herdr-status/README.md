# Herdr Status

`herdr-status` 是 Herdr 的只读状态页服务。它不是 terminal replacement，而是手机和桌面浏览器里的轻量控制台，用来快速判断当前 Herdr sessions、agents、panes 的状态，并生成进入对应 terminal 或 history 的链接。

## 目标

它回答这些问题：

- 当前有哪些 Herdr sessions 正在运行？
- 每个 session 下有哪些 agents？
- agent 是 `working`、`blocked`、`done`、`idle` 还是 `unknown`？
- agent 所在 workspace、tab、pane、cwd 是什么？
- 如何进入某个 session 或某个 agent 对应的 Herdr terminal？
- 如何在手机上查看某个 pane 的历史输出？

服务本身只读：不发送输入、不启动 agent、不停止 session、不直接暴露 shell。

## 路由

本服务监听：

```text
127.0.0.1:8765
```

独立本地访问：

```text
http://127.0.0.1:8765/
http://127.0.0.1:8765/api.json
```

通过 `herdr-web` Caddy router 暴露：

```text
/herdr             status dashboard
/herdr/api.json    raw status JSON
/herdr/history     read-only pane history
```

相关 terminal route 由 `herdr-web` 维护：

```text
/herdr/terminal/          desktop ttyd terminal
/herdr/terminal-mobile/   plain mobile ttyd fallback
/herdr/touch-terminal/    mobile touch wrapper
```

## 配置

本地 env 文件：

```text
~/.config/selfops/herdr-status.env
```

模板：

```text
dev/dev-machine/herdr-status/herdr-status.env.example
```

主要配置：

```text
HERDR_STATUS_HOST=127.0.0.1
HERDR_STATUS_PORT=8765
HERDR_STATUS_TTYD_URL=/herdr/terminal/
HERDR_STATUS_HISTORY_URL=/herdr/history

# Optional responsive terminal URL bases:
HERDR_STATUS_TTYD_DESKTOP_URL=/herdr/terminal/
HERDR_STATUS_TTYD_MOBILE_URL=/herdr/touch-terminal/
HERDR_STATUS_TTYD_MOBILE_WIDTH=700
```

`HERDR_STATUS_TTYD_URL` 是基础 terminal URL。启用 responsive terminal URL 后：

- 宽屏使用 `HERDR_STATUS_TTYD_DESKTOP_URL`。
- 窄屏使用 `HERDR_STATUS_TTYD_MOBILE_URL`。
- 阈值由 `HERDR_STATUS_TTYD_MOBILE_WIDTH` 控制。
- status 页面会在选择 base URL 后追加相同的 ttyd `arg=...` 参数。

当前推荐：

```text
desktop: /herdr/terminal/
mobile:  /herdr/touch-terminal/
width:   700
```

这意味着桌面点击 `Session` 或 `Agent` 进入普通 ttyd；手机点击同一个链接时进入 touch wrapper。

## Terminal 链接

每个 session 会生成：

```text
/herdr/terminal/?arg=--session&arg=default
```

每个可识别 agent 会生成：

```text
/herdr/terminal/?arg=--session&arg=default&arg=--agent&arg=term_...
```

这些参数由 `dev/dev-machine/herdr-web/bin/herdr-web-session` 解析，只允许：

```text
--session <name>
--agent <target>
```

对应命令：

```text
herdr --session <name>
herdr --session <name> agent attach <target> --takeover
```

每个 terminal link 旁边有 `Link` 按钮。按钮复制的是当前 viewport 对应的最终 URL：桌面复制 desktop URL，手机复制 mobile URL。

## History 链接

每个有 pane id 的 agent 会生成：

```text
/herdr/history?session=default&pane=w1:p1&lines=400
```

History 页面把最近 pane 输出渲染成普通 HTML：

- 支持浏览器原生滚动。
- 保留常见 ANSI 颜色和 emphasis。
- 默认按终端宽度渲染，不走 xterm.js。
- 适合手机快速查看 Codex/agent 是否暂停、报错、等待输入。

History 是只读的，不会向 pane 写入任何内容。

## 排序

Sessions 和 agents 按关注优先级排序：

```text
blocked > working > unknown > idle > done > stopped
```

状态颜色也按这个语义设计，方便手机上快速扫一眼当前是否有需要处理的 agent。

## 与手机 Touch Terminal 的关系

`herdr-status` 不直接实现 terminal。手机 terminal 由 `herdr-web/public/herdr/touch-terminal/index.html` 维护。

Status 只负责生成响应式链接：

```text
desktop -> /herdr/terminal/
mobile  -> /herdr/touch-terminal/
```

`touch-terminal` 的行为：

- 默认查看模式，避免手机键盘自动弹出。
- 非输入模式下，单指拖动会转换成 inner xterm 的 wheel 事件，用于滚动 Herdr pane。
- 点击 `输入` 才允许 xterm textarea 获得焦点。
- 底部提供 Paste、Esc、Tab、方向键、Ctrl-C 和命令输入框。

电脑调试 terminal 时应直接打开 `/herdr/terminal/`，不要打开 `/herdr/touch-terminal/`。

## 运行

开发模式：

```bash
mise run herdr-status:serve
```

systemd user service：

```bash
systemctl --user status herdr-status.service
systemctl --user restart herdr-status.service
```

通过 Caddy 验证：

```bash
curl -sS -o /tmp/herdr-status.html -w 'status %{http_code} %{size_download}\n' http://127.0.0.1:8780/herdr
curl -sS -o /tmp/herdr-api.json -w 'api %{http_code} %{size_download}\n' http://127.0.0.1:8780/herdr/api.json
```

检查 responsive link 是否存在：

```bash
curl -sS http://127.0.0.1:8780/herdr | rg 'data-desktop-url|data-mobile-url|mobileTerminalWidth'
```

## 维护边界

修改状态采集、HTML 渲染、history 渲染：

```text
dev/dev-machine/herdr-status/server.py
```

修改公网 route、ttyd、tunnel、touch terminal：

```text
dev/dev-machine/herdr-web/
```

修改本机事实：

```text
dev/dev-machine/STATE.md
```

提交前至少运行：

```bash
git diff --check
python3 -m py_compile dev/dev-machine/herdr-status/server.py
```

不要把 `~/.config/selfops/herdr-status.env` 或任何 token/password 提交进 Git。

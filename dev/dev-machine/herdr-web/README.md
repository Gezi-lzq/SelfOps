# Dev-Machine Public Router

本目录维护当前开发机的公共浏览器入口。它把多个本机 localhost 服务收敛到同一个 Caddy path router，再通过 ngrok 或 Cloudflare quick tunnel 暴露出去。

当前最重要的用途是 Herdr 浏览器访问：在手机上查看 Herdr session、agent 状态、pane history，并在需要时进入对应 Herdr terminal。

## 当前方案

链路如下：

```text
browser
  -> ngrok static endpoint 或 cloudflared quick tunnel
  -> 127.0.0.1:8780 Caddy
  -> path-specific localhost backend
```

本机服务只监听 localhost：

```text
127.0.0.1:7681  ttyd desktop terminal
127.0.0.1:7682  ttyd mobile terminal profile
127.0.0.1:8765  herdr-status
127.0.0.1:8780  Caddy public router
```

用户面对的入口：

```text
/               gezi-dev service homepage
/herdr          Herdr Status Dashboard
/kiro-gateway   Kiro Gateway
```

Herdr 子路由：

```text
/herdr                    Herdr 状态页
/herdr/api.json           Herdr 状态 JSON
/herdr/history            可滚动的 pane history HTML
/herdr/terminal/          桌面 ttyd terminal
/herdr/terminal-mobile/   普通 ttyd mobile profile fallback
/herdr/touch-terminal/    手机触屏 terminal wrapper
```

桌面和手机 terminal 是两个入口。桌面应使用 `/herdr/terminal/`；手机从 `/herdr` 状态页进入时，会按 viewport 宽度自动切到 `/herdr/touch-terminal/`。不要在电脑上直接打开 `touch-terminal`，否则会看到手机底部输入栏和触控层。

## 文件职责

```text
Caddyfile
  Caddy path router。新增公开服务时优先改这里。

public/index.html
  根路径 homepage，只放少量稳定入口。

public/herdr/touch-terminal/index.html
  手机 Herdr terminal wrapper。负责触屏滚动、查看/输入模式、底部快捷键。

bin/herdr-web-ttyd
  ttyd 启动包装器，读取本地 env，追加 ttyd frontend client options。

bin/herdr-web-session
  ttyd 内执行的 Herdr 包装命令，只允许 --session 和 --agent。

bin/herdr-web-ngrok
bin/herdr-web-cloudflared
  public tunnel 启动包装器。

systemd/*.service
  systemd --user unit 模板，由 install.sh 安装到 ~/.config/systemd/user/。

herdr-web.env.example
  本地 env 模板。真实文件在 ~/.config/selfops/herdr-web.env，不进 Git。
```

`herdr-status` 的状态页服务代码和文档在相邻目录：

```text
dev/dev-machine/herdr-status/
```

## 安全边界

公开 tunnel 面向互联网，所有经 Caddy 暴露的路径都要按公网服务处理。

当前认证模型：

- `ttyd` 使用 HTTP basic auth，凭证来自 `HERDR_WEB_TTYD_CREDENTIAL`。
- `herdr-status` 和 `/herdr/history` 是只读页面，目前不额外加 basic auth。
- ngrok token、ttyd 密码、Cloudflare tunnel 状态都只保存在本地配置或 provider 侧，不写入仓库。

本地敏感文件：

```text
~/.config/selfops/herdr-web.env
~/.config/selfops/herdr-status.env
~/.config/ngrok/ngrok.yml
```

注意：ttyd basic auth 通过 `ttyd -c user:password` 传入，本机其他用户可能通过进程信息看到该参数。当前开发机按单用户机器处理可以接受。如果未来启用 ngrok OAuth、Cloudflare Access 或其他边缘认证，应清空 `HERDR_WEB_TTYD_CREDENTIAL`，让边缘层负责认证。

不要把 token、密码、provider 返回的 opaque state、完整公网 URL 绑定关系写进公共文档；机器当前事实需要记录时写入 `dev/dev-machine/STATE.md` 并脱敏。

## 安装

依赖：

- `herdr`
- `ttyd`
- `caddy`
- `ngrok` 或 `cloudflared`
- `systemd --user`

ngrok 需要先完成认证：

```bash
ngrok config add-authtoken <token>
```

如果机器没有 ngrok，可以安装用户态二进制：

```bash
mise run herdr-web:install-ngrok
```

安装本模块：

```bash
mise run herdr-web:install
```

安装会创建：

```text
~/.config/selfops/herdr-web.env
~/.config/selfops/herdr-status.env
~/.config/systemd/user/herdr-web-ttyd.service
~/.config/systemd/user/herdr-web-ttyd-mobile.service
~/.config/systemd/user/herdr-status.service
~/.config/systemd/user/herdr-web-proxy.service
~/.config/systemd/user/herdr-web-ngrok.service
~/.config/systemd/user/herdr-web-cloudflared.service
```

需要调整时编辑本地 env：

```bash
$EDITOR ~/.config/selfops/herdr-web.env
$EDITOR ~/.config/selfops/herdr-status.env
```

## 启停

启动 ngrok 方案：

```bash
mise run herdr-web:start
mise run herdr-web:url
```

启动 Cloudflare quick tunnel fallback：

```bash
mise run herdr-web:start-cloudflared
mise run herdr-web:cloudflared-url
```

查看日志：

```bash
mise run herdr-web:logs
```

停止：

```bash
mise run herdr-web:stop
```

登录后自启动：

```bash
mise run herdr-web:enable
```

如果只改了 Caddy route：

```bash
systemctl --user restart herdr-web-proxy.service
curl -sS -I http://127.0.0.1:8780/herdr
```

如果只改了 status 页面代码：

```bash
systemctl --user restart herdr-status.service
curl -sS http://127.0.0.1:8780/herdr >/tmp/herdr-status.html
```

如果只改了 touch terminal 静态页面，Caddy `file_server` 会直接读取仓库文件，通常不需要重启。

## Herdr Status 到 Terminal

`/herdr` 状态页为每个 session 和 agent 生成 terminal 链接：

```text
/herdr/terminal/?arg=--session&arg=default
/herdr/terminal/?arg=--session&arg=default&arg=--agent&arg=term_...
```

这些 `arg=...` 参数最终交给 ttyd 执行的 `herdr-web-session`：

```text
--session <name>              -> herdr --session <name>
--session <name> --agent <id> -> herdr --session <name> agent attach <id> --takeover
```

`herdr-web-session` 只接受 `--session` 和 `--agent`，避免从 URL 任意拼 shell 命令。

状态页支持响应式 terminal base URL：

```text
HERDR_STATUS_TTYD_URL=/herdr/terminal/
HERDR_STATUS_TTYD_DESKTOP_URL=/herdr/terminal/
HERDR_STATUS_TTYD_MOBILE_URL=/herdr/touch-terminal/
HERDR_STATUS_TTYD_MOBILE_WIDTH=700
```

浏览器宽度小于等于 `HERDR_STATUS_TTYD_MOBILE_WIDTH` 时，状态页把 terminal link 改为 mobile URL；宽屏使用 desktop URL。复制按钮也会复制当前 viewport 对应的 URL。

## 手机 Touch Terminal

手机入口：

```text
/herdr/touch-terminal/
```

它不是另一个 ttyd 后端，而是一个静态 wrapper：外层页面嵌入 `/herdr/terminal/`，并给手机浏览器补一层适合触屏的交互。

当前行为：

- 默认查看模式，不自动弹出手机键盘。
- 单指上下拖动终端区域时，外层页面向内层 xterm DOM 派发 `WheelEvent`，让 Herdr 自己处理 pane 滚动。
- 短按终端区域会转发 click，用于 Herdr 内部 switch 等点击场景。
- 点击底部 `输入` 后进入直接输入模式，触屏层隐藏，ttyd/xterm 可以获得焦点。
- 底部快捷栏提供 `Paste`、`Esc`、`Tab`、退格、方向键、`Ctrl-C`。
- 底部命令输入框使用 bracketed paste 发送文本，再发送回车，降低 shell 特殊字符被逐字解释的风险。

默认 ttyd frontend 参数：

```text
fontSize=10
lineHeight=1.12
disableResizeOverlay=true
```

可以在 URL query 中覆盖：

```text
/herdr/touch-terminal/?fontSize=12&lineHeight=1.15
```

也可以用 `input=1` 默认进入直接输入模式：

```text
/herdr/touch-terminal/?input=1
```

不要用 raw SGR mouse escape bytes 模拟滚动。之前验证过，在 mouse tracking 未启用或目标不匹配时，这类字节会直接写进 agent prompt，污染终端输入。

## ttyd 配置

桌面 ttyd 读取 `~/.config/selfops/herdr-web.env`：

```text
HERDR_WEB_TTYD_HOST=127.0.0.1
HERDR_WEB_TTYD_PORT=7681
HERDR_WEB_TTYD_BASE_PATH=/terminal
HERDR_WEB_TTYD_CREDENTIAL=debian:change-me
HERDR_WEB_SESSION=browser
HERDR_WEB_CWD=/home/debian
```

可选 frontend client options：

```text
HERDR_WEB_TTYD_FONT_SIZE=14
HERDR_WEB_TTYD_LINE_HEIGHT=1.15
HERDR_WEB_TTYD_SCROLLBACK=5000
HERDR_WEB_TTYD_DISABLE_LEAVE_ALERT=true
HERDR_WEB_TTYD_DISABLE_RESIZE_OVERLAY=true
HERDR_WEB_TTYD_RENDERER_TYPE=canvas
```

移动 ttyd profile 由 `herdr-web-ttyd-mobile.service` 设置独立端口和默认字体，主要保留为 plain ttyd fallback。当前手机主入口已经是 `/herdr/touch-terminal/`。

## Tunnel 策略

优先使用 ngrok static endpoint，作为当前开发机对外暴露的主要出口。

如果 ngrok 报 `ERR_NGROK_334`，说明同一个 endpoint 已经在别处在线。处理顺序：

1. 在 ngrok dashboard 停掉旧 endpoint 或旧 backend。
2. 确认本机 `herdr-web-ngrok.service` 重新启动。
3. 如果需要临时容忍多个 backend，才设置：

```text
HERDR_WEB_NGROK_POOLING=true
```

Pooling 只是应急方案。如果池子里有旧 backend 或错误 backend，请求可能间歇命中错误机器，表现为 ngrok 页面报 JSON 解析、空响应或路径不一致。

Cloudflare quick tunnel 是备用方案：

- 优点：启动快，不依赖 ngrok static endpoint 状态。
- 缺点：URL 临时，不适合作长期固定入口。

## 新增公开服务

新增服务时保持这个层级：

1. 后端服务只监听 `127.0.0.1:<port>`。
2. 在 `Caddyfile` 添加 path-specific `handle`。
3. 如果是用户可见入口，在 `public/index.html` 加 card。
4. 更新本 README。
5. 重启 `herdr-web-proxy.service` 并 curl 验证。

Caddy 模板：

```caddyfile
handle /tool-name {
	rewrite * /
	reverse_proxy 127.0.0.1:<port>
}

handle /tool-name/* {
	uri strip_prefix /tool-name
	reverse_proxy 127.0.0.1:<port>
}
```

把新 route 放在最终 fallback 之前。路径前缀要明确，避免把未知路径透传到错误服务。

## 验证清单

本地路由：

```bash
curl -sS -o /tmp/herdr-root.html -w 'root %{http_code} %{size_download}\n' http://127.0.0.1:8780/
curl -sS -o /tmp/herdr-status.html -w 'status %{http_code} %{size_download}\n' http://127.0.0.1:8780/herdr
curl -sS -o /tmp/herdr-touch.html -w 'touch %{http_code} %{size_download}\n' http://127.0.0.1:8780/herdr/touch-terminal/
```

ttyd 会要求 basic auth，验证 HTTP 状态即可：

```bash
curl -sS -o /dev/null -w 'terminal %{http_code}\n' http://127.0.0.1:8780/herdr/terminal/
```

公网路由：

```bash
public_url="$(mise run herdr-web:url)"
curl -sS -L -o /tmp/herdr-public.html -w 'public %{http_code} %{size_download}\n' "$public_url/herdr"
```

提交前：

```bash
git status --short --branch
git diff --check
```

不要把 `~/.config/selfops/*.env`、ngrok token、ttyd 密码、provider state 加入 Git。

# Environment

管理这台机器的全局开发环境依赖与版本约束。

当前使用 `mise` 作为统一入口，托管以下工具链：

- `go`
- `java`
- `maven`
- `node`
- `pnpm`
- `python`
- `uv`
- 全局 npm CLI：`@openai/codex`、`@playwright/cli`、`agent-browser`

说明：

- `npx` 不单独安装，它随 `node`/`npm` 一起提供
- `pnpm` 作为独立全局工具由 `mise` 管理，不依赖 `corepack`
- Codex、Playwright CLI、agent-browser 这类 npm 全局工具在 `config.toml` 中声明，由 mise npm backend 安装
- `go` 由 mise 管理版本，GOPATH 设为 `~/go`（Go 默认值），`go install` 的二进制放在 `~/go/bin`

## 文件布局

- `config.toml`：全局 `mise` 配置源文件
- `bootstrap.sh`：新机器初始化脚本

## 新机器初始化

前提：先安装 `mise` 本体。

推荐在仓库根目录执行：

```bash
bash dev/environment/bootstrap.sh --activate-zsh
```

如果你使用 `bash`，改为：

```bash
bash dev/environment/bootstrap.sh --activate-bash
```

这一步会：

- 把仓库内的全局 `mise` 配置链接到 `~/.config/mise/config.toml`
- 按 `config.toml` 安装全局开发工具
- 把 `mise activate zsh` 追加到 `~/.zshrc`（如果还没有）
- 把 `mise activate bash --shims` 写入 `~/.profile`（如果还没有）

注意：

- 这会让 `~/.config/mise/config.toml` 指向仓库内的 `dev/environment/config.toml`
- 如果你原本已经有自己的全局 `mise` 配置，这一步会覆盖它的入口

如果你不想让脚本自动改 shell 配置，也可以先执行：

```bash
bash dev/environment/bootstrap.sh --no-activate-profile
```

然后再手动处理 shell 激活。

完成后可用下面的命令确认安装结果：

```bash
mise ls -g
```

## 接入本机

把仓库内配置链接到 `~/.config/mise/config.toml`：

```bash
mkdir -p ~/.config/mise
ln -sfn "$PWD/dev/environment/config.toml" ~/.config/mise/config.toml
```

### 最佳接入方式

mise 官方建议按 shell 场景分层：

- login、SSH、IDE、非交互入口：在 profile 文件中启用 shims
- 日常交互式 shell：在 shell rc 文件中启用完整 `mise activate`
- 脚本、cron、CI、agent 命令：优先使用 `mise exec -- <cmd>` 保证环境确定

当前 Linux/SSH/headless 机器使用 `~/.profile` 作为 profile 入口：

```bash
if [ -x "$HOME/.local/bin/mise" ]; then
    eval "$($HOME/.local/bin/mise activate bash --shims)"
fi
```

这样 `agent-browser`、`playwright-cli`、`codex`、`node` 等命令可以直接通过
`~/.local/share/mise/shims` 解析，不需要在 `~/.local/bin` 里维护自定义 wrapper。

### Zsh 交互式 shell

推荐把下面这一行放到 `~/.zshrc` 的末尾：

```bash
eval "$($HOME/.local/bin/mise activate zsh)"
```

这样做的目的：

- 让交互式 `zsh` 直接拿到 `mise` 管理的 `PATH`
- 让 `JAVA_HOME` 等环境变量随当前激活版本自动更新
- 保证 `mise` 能覆盖前面已经加载的 `nvm`、`sdkman` 等版本管理器

这一步在以下情况下是必要的：

- 希望直接执行 `java`、`mvn`、`node`、`python`
- 希望切目录后自动切换版本
- 希望 `JAVA_HOME` 跟着 `mise` 一起变化

这一步在以下情况下不是必须的：

- 只打算使用 `mise exec ...` 或 `mise run ...`
- 不要求 shell 自动接管 `PATH`

### Bash 交互式 shell

如果使用 bash，把下面这一行放到 `~/.bashrc` 的末尾：

```bash
eval "$($HOME/.local/bin/mise activate bash)"
```

bootstrap 的 `--activate-bash` 会自动追加这行。

### 关于 shims

shims 是 login/non-interactive 场景的入口，完整 `mise activate` 是交互式场景的入口。
profile 先加载 shims，随后交互式 shell 再加载完整 activation 是安全的；mise 会在完整
activation 中接管 `PATH`。

如果是 zsh login shell，可在 `~/.zprofile` 里加：

```bash
eval "$($HOME/.local/bin/mise activate zsh --shims)"
```

建议：

- 日常终端：`~/.zshrc` 用 `mise activate zsh`
- bash/SSH/headless：`~/.profile` 用 `mise activate bash --shims`
- zsh login shell：`~/.zprofile` 用 `mise activate zsh --shims`
- 脚本中需要确定环境：`mise exec -- <cmd>`

注意：

- `mise` 应放在 `~/.zshrc` 最后，避免被后续 `PATH` 修改覆盖
- 如果决定让 `sdkman` 接管 `java`，应先把 `java` 从 `mise` 配置中移除

## 浏览器自动化

Linux/SSH/headless 机器推荐使用 Playwright 的 headless Chromium，并通过 mise 管理相关 CLI：

```toml
[tools]
node = "26.3.0"
pnpm = "11.5.2"
"npm:@playwright/cli" = "latest"
"npm:agent-browser" = "latest"
```

常用检查命令：

```bash
agent-browser doctor
playwright-cli --version
```

在 Codex 或其他 agent 中，如果 shell 还没有加载 profile，可以使用确定性写法：

```bash
mise exec -- agent-browser doctor
mise exec -- playwright-cli --version
```

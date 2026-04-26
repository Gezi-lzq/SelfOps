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

说明：

- `npx` 不单独安装，它随 `node`/`npm` 一起提供
- `pnpm` 作为独立全局工具由 `mise` 管理，不依赖 `corepack`
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

注意：

- 这会让 `~/.config/mise/config.toml` 指向仓库内的 `dev/environment/config.toml`
- 如果你原本已经有自己的全局 `mise` 配置，这一步会覆盖它的入口

如果你不想让脚本自动改 shell 配置，也可以先执行：

```bash
bash dev/environment/bootstrap.sh
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

### Zsh 最佳接入方式

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

### 关于 `.zprofile`

当前机器没有配置 `~/.zprofile`，这对日常交互式终端是可以接受的。

如果后续需要让非交互场景也更容易拿到 `mise` 工具，例如某些 IDE、login shell
或脚本环境，可以额外在 `~/.zprofile` 里加：

```bash
eval "$($HOME/.local/bin/mise activate zsh --shims)"
```

建议：

- 日常终端：`~/.zshrc` 用 `mise activate zsh`
- 非交互补充：`~/.zprofile` 可选加 `mise activate zsh --shims`

注意：

- `mise` 应放在 `~/.zshrc` 最后，避免被后续 `PATH` 修改覆盖
- 如果决定让 `sdkman` 接管 `java`，应先把 `java` 从 `mise` 配置中移除

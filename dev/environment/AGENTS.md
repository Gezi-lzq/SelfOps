# dev/environment Agent Guide

## 职责

`dev/environment/` 管理开发机全局依赖、`mise` 配置、bootstrap 脚本和 dotfile 入口。这里记录的是可复现策略，不保存登录态、token 或 app opaque state。

## 事实来源

- `config.toml`：全局 `mise` 工具声明。
- `bootstrap.sh`：新机器或当前机器的 dotfile/bootstrap 入口。
- `README.md`：依赖分类、shell activation 和安装说明。
- 根 `AGENTS.md`：分支、提交、安全和事实优先级。

## 操作规则

- 新增全局 CLI 优先改 `config.toml`。
- shell 入口或 symlink 行为优先改 `bootstrap.sh`，不要只手动编辑 `$HOME`。
- 真实 app config 可以直接改，例如 `~/.claude/settings.json`，但长期策略和验证方法要记录回 SelfOps。
- 认证状态、OAuth、API key、SSH key、provider token、cache 不提交。
- 如果某个依赖不能由 `mise` 管理，记录安装方式、版本、配置路径和验证命令。

## 常用验证

改 `config.toml` 后按风险选择：

```bash
readlink -f ~/.config/mise/config.toml
mise install
mise ls -g
<tool> --version
git diff --check
```

改 `bootstrap.sh` 后至少运行：

```bash
bash -n dev/environment/bootstrap.sh
git diff --check
```

如果实际执行 bootstrap 会改 `$HOME`，先确认这是当前任务需要的应用操作。

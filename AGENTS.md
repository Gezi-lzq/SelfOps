# SelfOps Agent Guide

## 仓库定位

SelfOps 是 AI 运维与开发机操作的控制仓库，用来沉淀可复现的机器状态、agent runtime、skills 体系、工具链入口、长期操作规则和跨机器协作约定。它不是单纯 dotfiles，也不是某一台机器的运行记录；机器分支是 SelfOps 在某台开发机上的具体投影。

根 `AGENTS.md` 是全仓库公共宪法，代表这个仓库对 agent 的目标、边界和预期。它必须在 `main` 与 `machine/<name>` 分支保持一致。机器事实、当前状态、路径和服务细节不要写进根文件。

## 最高原则

- 文档默认使用中文；命令、路径、配置 key、工具名和外部协议名保留原文。
- 当前工作树和仓库文件优先于聊天历史、记忆和模型印象。
- 清晰、局部、可验证的任务默认直接执行；涉及仓库政策、分支模型、安全边界、开发机网络、长期目录结构的变更，先讨论再修改。
- 长期决策必须回写仓库：公共政策写入根或子目录 `AGENTS.md`，子系统规则写入对应 README/`AGENTS.md`，机器目标写入 `PLAN.md`，机器事实写入 `STATE.md`。
- 涉及 secret、数据删除、强制覆盖、远端发布、机器级安装/卸载或网络暴露的操作，都必须先确认当前目标、影响范围和用户意图；不要把本地凭证或 opaque app state 写入仓库。

## 事实来源优先级

1. 当前工作树、当前分支和 `git status --short --branch`。
2. 距离目标文件最近的 `AGENTS.md`。
3. `dev/dev-machine/STATE.md` 中记录的当前机器事实。
4. `dev/dev-machine/PLAN.md` 中记录的目标状态。
5. 对应目录 README 和脚本。
6. skill、记忆和历史对话；它们只能作为线索，不能覆盖当前仓库文件。

## 分支模型

- `main` 承载公共规则、公共 skills、模板、通用脚本、通用文档和跨机器约定。
- `machine/<name>` 承载某台开发机的具体事实、路径、安装记录、服务状态和机器专属项目清单。
- 能被多台机器复用的改动优先进入 `main`，再 merge 到机器分支。
- 只对当前机器成立的改动留在机器分支。
- 如果机器分支发现公共规则缺口，先改 `main`，再 merge 回机器分支。
- 根 `AGENTS.md` 不允许在机器分支单独 fork；子目录 `AGENTS.md` 也默认遵循同样策略，除非该目录只存在于机器分支。

## 默认工作流

轻量默认：

1. 看当前上下文和 `git status --short --branch`。
2. 找到最近的 owner 文档或 owner 文件。
3. 做最小必要改动，并按风险匹配验证。

不要求每次完整阅读所有 README，不要求每次更新 `PLAN.md`/`STATE.md`，也不要求每次提交。只有当任务语义包含持久变更、用户要求提交，或需要把决策固化进仓库时，才主动 commit。

遇到以下情况升级为严格流程：分支模型、安全边界、开发机网络、全局依赖、dotfile 入口、agent-runtime 分发、systemd/服务/持久存储、远端同步、跨目录大改。

## 开发机网络

SelfOps 管理的开发机默认处于同一个 NetBird network。跨机器访问、SSH、内部服务联通优先通过 NetBird DNS 或 SSH alias。除非用户明确要求，不要引入额外网络暴露模型；某台机器的额外访问方式只记录在机器分支文档中。

不要把 NetBird setup key、token、私有 DNS 细节、敏感日志或不稳定私有 IP 写入公共文档。具体机器网络事实以 `dev/dev-machine/STATE.md` 为准。

## 配置与本地状态

SelfOps 管理可复现策略、入口脚本、模板和文档；真实 app 拥有的配置文件可以直接修改，但长期策略要回写 SelfOps。

- `dev/environment/config.toml` 管理全局 `mise` 工具。
- `~/.config/mise/config.toml` 应由 SelfOps bootstrap 建立到仓库配置的链接。
- `~/.claude/settings.json` 这类 app-owned config 可以直接改，但不要提交其中的凭证或个人 app state。
- 登录态、OAuth、token、SSH key、provider key、opaque cache 不纳入 Git。

更具体规则见 `dev/environment/AGENTS.md`。

## 子目录规则

子目录 `AGENTS.md` 用于承接具体操作规则。写法应保持短而可执行，至少说明：

- 该目录负责什么。
- 哪些文件是事实来源。
- 常见操作入口。
- 变更后要更新哪些文档。
- 最小验证方式。
- 本目录特有安全注意事项。

当前主要路由：

- `dev/environment/AGENTS.md`：全局依赖、bootstrap、dotfile 入口、本地 app config 边界。
- `dev/agent-runtime/AGENTS.md`：skills catalog、bundles、project registry、scan/plan/apply。
- `dev/dev-machine/AGENTS.md`：开发机目标/事实、NetBird 访问、服务与持久状态。
- `agents/bub/AGENTS.md`：Bub profiles、env 渲染、备份与隔离。

## 提交与远端同步

- commit 可以在明确任务语境下主动做，例如用户要求“完成变更”“更新 git”“提交一下”，或讨论已达成需要固化的仓库决策。
- commit 要小而聚焦，不要混入无关机器状态。
- 同时涉及公共层和机器层时，先提交 `main` 的公共内容，再 merge 到机器分支。
- 不要自动 push。只有用户明确要求 push、同步远端、更新 origin 或完成 git 远端更新时，才推送。

## 验证与汇报

验证强度应匹配变更风险。文档和配置改动至少执行 `git diff --check`；代码、脚本、服务、agent-runtime 和机器配置改动按最近 README 或子目录 `AGENTS.md` 执行对应验证。

如果跳过验证，必须说明原因。收尾时说明改了什么、验证了什么、没有验证什么、当前工作树是否干净。

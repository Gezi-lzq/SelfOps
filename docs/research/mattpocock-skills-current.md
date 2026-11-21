# Matt Pocock 官方 Skills 仓库现状

调查日期：2026-11-21（UTC）

## 来源与版本结论

- 官方仓库是 [`mattpocock/skills`](https://github.com/mattpocock/skills)。仓库 README 将其定位为 Matt Pocock 日常使用的、面向真实工程的软件 agent skills，并说明这些 skills 追求小型、可适配和可组合，适用于任何模型。[README](https://github.com/mattpocock/skills/blob/main/README.md)
- 当前 `main` 的最新提交是 [`abeeaf95660ba9e8b7c753eb38f441ca707a8823`](https://github.com/mattpocock/skills/commit/abeeaf95660ba9e8b7c753eb38f441ca707a8823)，提交信息为 `Merge pull request #1455 from mattpocock/ci-frontmatter-check`，提交时间为 2026-11-19 13:34:58 UTC。该提交位于最新发布标签之后，因此应把 `main` 视为当前仓库内容，把标签视为已发布版本线。[提交历史](https://github.com/mattpocock/skills/commits/main)
- 最新正式 release/tag 是 **v1.3.2**，标签提交为 [`85cbec972d7a79c278c793d272f7fc715850fad9`](https://github.com/mattpocock/skills/releases/tag/v1.3.2)，发布时间为 2026-10-29。仓库 `package.json` 也声明版本 `1.3.2`。[package.json](https://github.com/mattpocock/skills/blob/main/package.json)
- `CHANGELOG.md` 的 1.3.2 条目记录了该版本的行为修复，包括 `ask-matt` 读取完整 `SKILL.md`、`code-review` 读取仓库标准并以前台子代理返回报告、`diagnosing-bugs` 强制 mutation 校验、`implement` 使用 Skill 工具、以及 setup/triage/wizard 等流程修复。[CHANGELOG 1.3.2](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md)
- GitHub marketplace 中的官方插件名为 `mattpocock-skills`，marketplace 名为 `mattpocock`，owner 为 Matt Pocock。插件的正式发布集合是 `engineering/` 和 `productivity/` 两个 promoted bucket。[marketplace.json](https://github.com/mattpocock/skills/blob/main/.claude-plugin/marketplace.json) · [CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md)

## 完整 Skills 清单（当前 `main`）

仓库中当前共有 **39 个 `SKILL.md`**。其中 20 个 Engineering、7 个 Productivity 属于 promoted 稳定集合，8 个 In Progress 和 4 个 Misc 是公开但不进入插件的集合，Deprecated 当前为空。分类和是否进入插件以仓库规则为准。[CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md) · [engineering README](https://github.com/mattpocock/skills/blob/main/skills/engineering/README.md) · [productivity README](https://github.com/mattpocock/skills/blob/main/skills/productivity/README.md) · [in-progress README](https://github.com/mattpocock/skills/blob/main/skills/in-progress/README.md) · [misc README](https://github.com/mattpocock/skills/blob/main/skills/misc/README.md)

### Engineering（20）

- **ask-matt** — 路由用户选择合适 skill/流程。
- **code-review** — 对固定基点之后的变更做 Standards 与 Spec 双轴审查。
- **codebase-design** — 用 deep module、窄接口和清晰 seam 设计代码库。
- **diagnosing-bugs** — 以复现、最小化、假设、埋点、修复、回归测试组成诊断闭环。
- **domain-modeling** — 建立和校准领域术语、GLOSSARY 与 ADR。
- **grill-with-docs** — 访谈需求并同步领域模型与 ADR。
- **implement** — 按 spec/ticket 实现，以 TDD 和 code review 收尾。
- **implement-spec** — 把整份 spec 当作任务图，在 ready frontier 并行实现并合入 integration branch。
- **improve-codebase-architecture** — 扫描代码库的 deepening 机会并生成可视化报告。
- **pr** — 形成包含摘要视觉、前后证据和合并风险的 PR body。
- **prototype** — 用单文件 HTML 原型验证状态/逻辑或可切换 UI 方案。
- **research** — 针对高信任一手来源研究问题并把结果写成带引用的 Markdown。
- **retro** — 回顾编码会话，提出环境、检查、标准和工具改进。
- **setup-matt-pocock-skills** — 配置 issue tracker、triage labels 和领域文档布局。
- **tdd** — 按 red-green-refactor 和垂直切片实践测试驱动开发。
- **to-spec** — 将当前会话整理为 spec 并发布到 issue tracker。
- **to-tickets** — 把计划/spec/会话拆成声明阻塞边的 tracer-bullet tickets。
- **triage** — 通过 triage 角色状态机移动 issue。
- **wayfinder** — 为跨多个会话的大块工作建立决策 ticket 地图。
- **wizard** — 为仅需人操作的基础设施、凭据、第三方 dashboard 或一次性迁移生成交互式 bash wizard。

Engineering README 和当前目录均为 20 个条目：`ask-matt`, `grill-with-docs`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `to-spec`, `to-tickets`, `implement`, `implement-spec`, `wayfinder`, `retro`, `prototype`, `diagnosing-bugs`, `research`, `tdd`, `domain-modeling`, `codebase-design`, `code-review`, `pr`, `wizard`。

### Productivity（7）

- **grill-me** — 通过持续追问解决计划或设计的所有分支。
- **handoff** — 将当前会话压缩为交接文档。
- **teach** — 跨多个会话教授技能或概念，并将当前目录作为状态工作区。
- **to-questionnaire** — 为无法独自回答的决定生成异步/会议问卷。
- **wait-what** — 消息未被理解时，用 GLOSSARY 术语重新表达。
- **grilling** — 可复用的递归访谈原语。
- **writing-for-agents** — 编写 skills、AGENTS.md/CLAUDE.md 及 agent 可达文档。

### In Progress（7，公开 beta，不进插件）

`chief-of-staff`, `claude-handoff`, `loop-me`, `setup-ts-deep-modules`, `software-factory`, `writing-beats`, `writing-fragments`, `writing-shape`。

In Progress 实际为 **8 个**：`chief-of-staff`, `claude-handoff`, `loop-me`, `setup-ts-deep-modules`, `software-factory`, `writing-beats`, `writing-fragments`, `writing-shape`。README 明确说明 beta skill 不进入插件、没有 docs 页面，可能无预警变化。[in-progress README](https://github.com/mattpocock/skills/blob/main/skills/in-progress/README.md)

### Misc（4，不进插件）

`git-guardrails-claude-code`, `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit`。[misc README](https://github.com/mattpocock/skills/blob/main/skills/misc/README.md)

## 官方安装与使用实践

- README 提供按 harness 选择的安装方式：Claude Code 使用 `claude plugin install mattpocock-skills@claude-plugins-official`；Codex 使用 `codex plugin marketplace add mattpocock/skills` 后 `codex plugin add mattpocock-skills@mattpocock`；Copilot 使用对应 marketplace/plugin 命令并启用 `autoUpdate`；Gemini CLI 分别安装 `skills/engineering` 与 `skills/productivity`；其他 agent 使用 `npx skills@latest add mattpocock/skills -a <agent>`。[README 安装段](https://github.com/mattpocock/skills/blob/main/README.md#installation-30-second-setup)
- 安装后每个 repo 运行一次 `/setup-matt-pocock-skills`。它会询问 issue tracker、triage labels 和文档保存位置，再配置工程 skills。[README](https://github.com/mattpocock/skills/blob/main/README.md#2-run-setup-matt-pocock-skills)
- 安装一个 harness 即可，README 明确提示不要同时安装两套，否则每个 skill 会重复。插件会自动更新，skills.sh 复制的可编辑文件则需要手动更新。[README](https://github.com/mattpocock/skills/blob/main/README.md#installation-30-second-setup)
- 稳定插件只包含 promoted buckets。`engineering/` 与 `productivity/` 的每个 skill 必须同时出现在顶层 README 和 `.claude-plugin/plugin.json` 的 `skills` 数组中；`misc/`、`in-progress/`、`deprecated/` 不得进入这两处。[CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md)
- 每个 skill 都要有相邻的 `agents/openai.yaml`。User-invoked skill 同时设置 Claude 的 `disable-model-invocation: true` 和 Codex 的 `policy.allow_implicit_invocation: false`，只能由用户显式触发。Model-invoked skill 保留丰富的 trigger 描述，使模型可以自动触发。两种 invocation 不能混用。[.agents/invocation.md](https://github.com/mattpocock/skills/blob/main/.agents/invocation.md)
- Skill 之间的操作性依赖应明确写成 `Call the Skill tool with "name"`。每次 Skill 工具调用只传一个 skill。User-invoked skill 不能被其他 skill 调用，应让人类运行它。[.agents/invocation.md](https://github.com/mattpocock/skills/blob/main/.agents/invocation.md)
- 文档采用 progressive disclosure：把每条路径都需要的步骤放在主文件，把只在特定分支需要的 reference 放到指针指向的独立文件；每个步骤都要有清晰且可检查的 completion criterion。[writing-for-agents SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
- Agent 文档应保持单一事实源、删除 stale sediment 和 no-op 句子，使用已有的 leading words，优先写正向目标而不是依赖否定式禁止语句。[writing-for-agents SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
- 每个 promoted skill 还需要对应 `docs/<bucket>/<skill-name>.md`，页面包含 What it does、When to reach for it、Common questions、It's working if 四节。修改 promoted skill 时应同步文档和 `ask-matt` 路由。[CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md)
- 修改 manifest 后运行 `claude plugin validate . --strict`。如需本地 harness 链接，运行 `scripts/link-skills.sh`，它创建指向仓库的 symlink，使 `git pull` 后内容保持更新。[CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md)
- 任何 dispatch subagent 的 skill 都要求使用 fresh context window，避免 Codex 等 harness 默认 fork 父对话而失去子代理所需的干净上下文。[CLAUDE.md](https://github.com/mattpocock/skills/blob/main/CLAUDE.md)

## 一手来源索引

- [仓库首页/README](https://github.com/mattpocock/skills)
- [main 最新提交](https://github.com/mattpocock/skills/commit/abeeaf95660ba9e8b7c753eb38f441ca707a8823)
- [最新正式标签 v1.3.2](https://github.com/mattpocock/skills/releases/tag/v1.3.2)
- [CHANGELOG](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md)
- [所有 tags](https://github.com/mattpocock/skills/tags)
- [Claude plugin manifest](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json)
- [Marketplace manifest](https://github.com/mattpocock/skills/blob/main/.claude-plugin/marketplace.json)

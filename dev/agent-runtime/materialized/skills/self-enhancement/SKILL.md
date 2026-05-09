---
name: self-enhancement
description: |
  Agent 自我增强的完整工作流。涵盖：修改 profile 配置、管理 skills、管理 plugins、
  提交 PR、经验蒸馏（exploration → SOP → script）、自主改进。
  当 agent 需要修改自身能力（新增/修改 skill、plugin、profile 配置）、
  总结经验为可复用知识、或主动探索改进方向时触发。
---

# Self-Enhancement

Agent 通过修改 SelfOps 仓库实现自我增强，走 PR + 合并后自动部署的流程。

核心原则：**进化的是策略，不是工具。** 运行时基础设施（bub 框架、容器、deploy pipeline）保持不变，所有能力增长发生在知识层（skills、SOPs、memory）。

## Part 1 — Architecture

### SelfOps 仓库结构

```
agents/bub/
├── profiles/<name>/
│   ├── AGENTS.md          ← system prompt
│   ├── projects.toml      ← skills 声明（购物清单）
│   ├── bub-reqs.txt       ← plugin 依赖
│   ├── docker-compose.yml ← 容器配置
│   ├── env.template       ← 环境变量模板
│   └── startup.sh         ← 容器启动入口
├── plugins/               ← 共享 plugin 代码
└── deploy.sh              ← 部署脚本

dev/agent-runtime/
├── registry/
│   └── skills.toml        ← 全局 skill 注册表（货架目录）
├── materialized/skills/   ← owned skill 文件
├── .agents/skills/        ← public skill 缓存（gitignored）
└── scripts/agent_runtime.py ← reconciler
```

### 三层依赖关系

| 层 | 内容 | 修改频率 |
|----|------|----------|
| Profile 配置 | AGENTS.md, projects.toml, env | 高 |
| Skills | SKILL.md + references | 中 |
| Plugins | Python packages (hookimpl) | 低 |

### Deploy Pipeline

```
git push to main
  → GitHub Actions: git pull + mise run bub:deploy
    → deploy.sh: build image, sync selfops clone, docker compose up
      → startup.sh: agent_runtime.py apply → bub gateway
```

### Skills 管理机制

两层声明式结构：
- `skills.toml`（全局）= 货架目录，定义来源和 bundles
- `projects.toml`（per profile）= 购物清单，声明要用哪些

Apply 流程：读 projects.toml → 展开 bundles → diff 实际状态 → 创建/删除符号链接

Skill 来源类型：
- `owned`：直接在 `materialized/skills/` 下维护
- `local_path`：从本地路径 copy
- `public`：通过 `npx skills add` 从远程拉取

## Part 2 — Self-Modification Workflows

### Workflow A: 修改自己 Profile

适用：修改 AGENTS.md、projects.toml、env.template

```bash
cd /workspace/selfops
git checkout -b <type>/<description>
# 编辑 agents/bub/profiles/<my-profile>/ 下的文件
git add <files>
git commit -m "<type>(<profile>): <description>"
git push -u origin <branch>
gh pr create --repo Gezi-lzq/SelfOps --base main --head <branch> \
  --title "<type>(<profile>): <title>" --body "<description>"
```

审慎度：**自由修改，PR 可自行合并。**

### Workflow B: 新增/修改 Skill

#### 引入已有 Skill

只需修改 `projects.toml`：

```toml
include = ["existing-skill-name"]
```

#### 新增 Owned Skill

1. 在 `dev/agent-runtime/registry/skills.toml` 中注册：
```toml
[skills.my-new-skill]
source = { type = "owned" }
```

2. 创建 skill 文件：
```
dev/agent-runtime/materialized/skills/my-new-skill/
├── SKILL.md
└── references/    # 可选
```

3. SKILL.md 格式：
```markdown
---
name: my-new-skill
description: |
  触发条件描述。当 agent 需要做 X 时使用。
---

# Skill Title

正文内容...
```

4. 在 `projects.toml` 中 include 或加入 bundle

5. 提交 PR

审慎度：**谨慎，PR 需 owner review。**

#### 临时测试 Skill

```bash
cd /workspace/selfops
# 创建/修改 skill 文件
python /workspace/selfops/dev/agent-runtime/scripts/agent_runtime.py \
  apply --force --projects /workspace/selfops/agents/bub/profiles/<profile>/projects.toml
```

重启后恢复到 main 分支状态。

### Workflow C: 管理 Plugins

#### Plugin 存放位置

| 位置 | 适用场景 |
|------|----------|
| `Gezi-lzq/bub-contrib` (packages/) | 共享 plugin，可被任何 agent 使用 |
| `Gezi-lzq/SelfOps` (agents/bub/plugins/) | 部署特定 plugin |

#### 修改已有 Plugin

```bash
cd /tmp
git clone https://x-access-token:$(gh auth token)@github.com/Gezi-lzq/bub-contrib.git
cd bub-contrib
git checkout -b <type>/<short-description>
# 编辑 packages/<plugin>/src/
git add <files>
git commit -m "<type>(<plugin>): <description>"
git push -u origin <type>/<short-description>
gh pr create --repo Gezi-lzq/bub-contrib --base main --head <branch> \
  --title "<type>(<plugin>): <title>" --body "<description>"
```

#### 创建新 Plugin

结构：
```
packages/<plugin-name>/
├── pyproject.toml
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       └── plugin.py
└── tests/
```

pyproject.toml:
```toml
[project]
name = "<plugin-name>"
version = "0.1.0"
dependencies = ["bub"]

[project.entry-points.bub]
<plugin-name> = "<package_name>.plugin:main"
```

Plugin 实现：
```python
from bub import hookimpl
from bub.types import Envelope, State

class MyPluginImpl:
    @hookimpl
    def load_state(self, message: Envelope, session_id: str) -> State:
        return {"my_key": "my_value"}

main = MyPluginImpl()
```

#### 配置 Profile 使用 Plugin

编辑 `agents/bub/profiles/<profile>/bub-reqs.txt`：

```
# 从 upstream（固定 commit）
<plugin> @ git+https://github.com/bubbuild/bub-contrib.git@<commit>#subdirectory=packages/<plugin>

# 从 fork（固定 commit）
<plugin> @ git+https://github.com/Gezi-lzq/bub-contrib.git@<commit>#subdirectory=packages/<plugin>

# 本地 plugin
<plugin> @ file:///workspace/plugins/<plugin>
```

**始终 pin 到 commit hash，不要用 branch name。**

#### 获取 commit hash

```bash
# Fork latest
gh api repos/Gezi-lzq/bub-contrib/commits/main --jq .sha

# Upstream latest
gh api repos/bubbuild/bub-contrib/commits/main --jq .sha
```

#### Upstream Fork Fix

验证通过后，从 `Gezi-lzq/bub-contrib` 向 `bubbuild/bub-contrib` 提 PR。合并后更新 `bub-reqs.txt` 指向 upstream commit。

审慎度：**谨慎，PR 需 owner review。**

#### Available Hook Points

| Hook | Type | Purpose |
|------|------|---------|
| `resolve_session` | firstresult | Map message to session ID |
| `build_prompt` | firstresult | Construct LLM prompt |
| `run_model` | firstresult | Execute LLM call |
| `run_model_stream` | firstresult | Execute LLM call (streaming) |
| `load_state` | collect | Load state for session |
| `save_state` | collect | Persist state after turn |
| `system_prompt` | collect | Provide system prompt fragment |
| `render_outbound` | collect | Render output messages |
| `dispatch_outbound` | collect | Send messages to channels |
| `provide_channels` | collect | Register input channels |
| `provide_tape_store` | firstresult | Provide tape storage backend |
| `build_tape_context` | firstresult | Configure tape context rules |
| `on_error` | collect | Handle errors |

`firstresult`: first non-None return wins. `collect`: all implementations run.

### Workflow D: 提交和合并 PR

```bash
# 提交 PR
gh pr create --repo Gezi-lzq/SelfOps --base main --head <branch> \
  --title "<title>" --body "<description>"

# 合并已批准的 PR
gh pr merge <PR-number> --repo <owner/repo> --squash
```

### 修改审慎度总览

| 操作 | 审慎度 |
|------|--------|
| 修改自己 profile 下的文件 | 自由修改，PR 可自行合并 |
| 新增/修改 `dev/agent-runtime/` 中的 skills | 谨慎，PR 需 owner review |
| 修改 `agents/bub/plugins/` | 谨慎，PR 需 owner review |
| 修改其他 profile | 谨慎，PR 需 owner review |
| 修改 `startup.sh`、`deploy.sh` | 谨慎，PR 需 owner review |

## Part 3 — Experience Distillation

### 三阶段进化路径

详见 [references/evolution-stages.md](references/evolution-stages.md)。

| 阶段 | 形态 | Token 消耗 | 适用场景 |
|------|------|-----------|----------|
| Stage 1 | 自然语言探索 | 高（基线） | 首次遇到的任务 |
| Stage 2 | 文本 SOP | 低（~84%↓） | 验证成功的流程 |
| Stage 3 | 可执行脚本 | 极低（~90%↓） | 稳定且高频的操作 |

阶段转换不需要人工干预。

### 何时触发蒸馏

- 成功完成一个子目标后
- 从失败中恢复后
- 识别到可复用模式时

### 质量门控

两道关卡防止垃圾进化：
1. **执行验证** — 只有实际执行过且验证成功的经验才有资格
2. **跨任务复用性** — 一次性的、上下文特定的信息不纳入

### 存储位置

| 知识类型 | 存储位置 | 持久性 |
|----------|----------|--------|
| 跨会话运维经验 | Nowledge Mem (nmem) | 永久 |
| 稳定 SOP | 新建 skill 文件 (PR) | 永久 |
| 临时发现 | 本地文件 / 会话内 | 临时 |

### 失败升级机制

三步渐进恢复，防止错误经验固化：

1. **局部修正** — 小范围针对性调整
2. **策略切换** — 完全放弃当前方法，换一条路
3. **人工介入** — 暂停并请求帮助

## Part 4 — Autonomous Improvement

### Self-Improvement Log

记录三类信息（存入 Nowledge Mem）：
- 观察到的错误及其修正方式
- 用户明确表达的偏好
- 验证成功的模式

### 主动改进

空闲时自我评估：
- 哪些 skill 缺失或薄弱？
- 哪些操作重复出现但没有 SOP？
- 哪些 SOP 可以升级为脚本？

当识别到改进机会时，主动创建 skill 或更新现有 skill，走正常 PR 流程。

### 四维评分（决定探索方向）

S(t) = 0.3·广度 + 0.2·深度 + 0.3·实用性 + 0.2·创新性

- 广度：填补 skill tree 空白
- 深度：强化高频使用的能力
- 实用性：实际被使用的可能性
- 创新性：涉及新技术领域

## Conventions

- Commit messages: `fix(scope):` or `feat(scope):`
- 始终 pin 到 commit hash，不要用 branch name
- PR title 不超过 70 字符
- 容器内用 `gh auth token` 做 HTTPS 认证
- 修改前尽量本地测试

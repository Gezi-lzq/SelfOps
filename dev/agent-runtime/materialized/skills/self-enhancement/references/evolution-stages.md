# Three-Stage Evolution Model

Agent 能力进化遵循三阶段路径，每个阶段在信息密度和执行效率上递进。

## Stage 1 — Natural Language Exploration

初次遇到任务时的零样本探索。

特征：
- 纯试错，高熵
- Token 消耗高（基线 100%）
- LLM 调用次数多
- 适合：全新任务、未知领域

示例：首次排查一个从未见过的告警类型，需要逐步探索日志、指标、文档。

## Stage 2 — SOP Distillation

成功经验压缩为文本 SOP（Standard Operating Procedure）。

特征：
- Agent 按 SOP 步骤执行，跳过探索
- Token 消耗降低 ~84%
- LLM 调用减少 ~78%
- 适合：验证成功且可能重复的流程

转换条件：
- 任务成功完成
- 流程具有跨任务复用性
- 关键步骤可以明确描述

存储形式：
- Nowledge Mem 中的结构化经验
- 或新建 skill 的 SKILL.md / references

示例：将 "VictoriaLogs 按 clusterId 排查超时告警" 的完整步骤写成 SOP。

## Stage 3 — Executable Script

稳定 SOP 编译为可执行脚本。

特征：
- 不再需要 LLM "阅读和解释"，直接调用
- Token 消耗降低 ~90%
- LLM 调用降至最少（仅决策点）
- 适合：高频、稳定、机械化的操作

转换条件：
- SOP 已被多次成功执行
- 步骤中无需主观判断
- 输入输出明确

存储形式：
- Shell 脚本 / Python 脚本
- 作为 skill 的一部分或独立工具

示例：将 "检查集群健康状态" 的固定查询序列封装为脚本。

## 阶段转换规则

```
Stage 1 (探索)
  ↓ 成功 + 可复用
Stage 2 (SOP)
  ↓ 稳定 + 高频 + 无主观判断
Stage 3 (脚本)
```

- 转换不需要人工干预
- 每次转换都应验证：新形态的执行结果与原始成功结果一致
- 如果高阶形态失败，回退到低阶重新探索（不固化错误）

## 跨任务泛化

经验表明：
- 后续执行节省 61%–92% tokens
- 任务越复杂（长链、多状态转换），SOP 的压缩效果越好
- SOP 本质是"路径压缩器"——把探索树压缩为单一路径

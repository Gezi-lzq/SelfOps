---
name: lark
description: 飞书 / Lark 操作统一入口。处理云文档、知识库、云盘、多维表格、电子表格、日历、消息、邮件、会议、任务、审批、妙搭、OKR、画板、幻灯片及 lark-cli 认证授权。
metadata:
  requires:
    bins: ["lark-cli"]
---

# 飞书 / Lark

根据用户要操作的对象，读取下表对应模块的 `SKILL.md`，再按该模块的指引只读取当前操作需要的参考文件。模块和参考文件保留原有相对路径；不要一次性加载全部模块。

| 对象或任务 | 模块 |
|---|---|
| 认证、身份、权限、CLI 输出与高风险确认 | [shared](modules/lark-shared/SKILL.md) |
| 云文档正文、思维笔记 | [doc](modules/lark-doc/SKILL.md) |
| 知识库空间与节点 | [wiki](modules/lark-wiki/SKILL.md) |
| 云盘文件、权限、评论、导入导出 | [drive](modules/lark-drive/SKILL.md) |
| 原生 Markdown 文件 | [markdown](modules/lark-markdown/SKILL.md) |
| 多维表格 Base | [base](modules/lark-base/SKILL.md) |
| 电子表格 | [sheets](modules/lark-sheets/SKILL.md) |
| 幻灯片 | [slides](modules/lark-slides/SKILL.md) |
| 画板 | [whiteboard](modules/lark-whiteboard/SKILL.md) |
| 日历、日程、会议室 | [calendar](modules/lark-calendar/SKILL.md) |
| 视频会议、妙记、逐字稿、智能纪要 | [meeting](modules/lark-meeting/SKILL.md) |
| 联系人、用户或机器人查找 | [contact](modules/lark-contact/SKILL.md) |
| 即时消息与群聊 | [im](modules/lark-im/SKILL.md) |
| 邮件 | [mail](modules/lark-mail/SKILL.md) |
| 任务与清单 | [task](modules/lark-task/SKILL.md) |
| 审批 | [approval](modules/lark-approval/SKILL.md) |
| 考勤 | [attendance](modules/lark-attendance/SKILL.md) |
| OKR | [okr](modules/lark-okr/SKILL.md) |
| 妙搭应用 | [apps](modules/lark-apps/SKILL.md) |
| 实时事件订阅 | [event](modules/lark-event/SKILL.md) |
| 原生 OpenAPI 探索 | [openapi-explorer](modules/lark-openapi-explorer/SKILL.md) |
| 为 lark-cli 创建自定义 skill | [skill-maker](modules/lark-skill-maker/SKILL.md) |
| 整理一段时间内的会议纪要 | [workflow-meeting-summary](modules/lark-workflow-meeting-summary/SKILL.md) |
| 汇总日程与未完成任务 | [workflow-standup-report](modules/lark-workflow-standup-report/SKILL.md) |

`lark-minutes`、`lark-note`、`lark-vc`、`lark-vc-agent` 是会议模块的兼容入口，内容保存在 `modules/` 中。处理这些请求时读取 [meeting](modules/lark-meeting/SKILL.md)。

跨模块任务按实际涉及的对象加载对应模块；认证、身份或权限问题再加载 [shared](modules/lark-shared/SKILL.md)。执行命令前确认所用模块的当前 CLI 用法。

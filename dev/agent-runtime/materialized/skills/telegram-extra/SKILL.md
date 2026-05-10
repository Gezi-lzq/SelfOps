---
name: telegram-extra
description: |
  Telegram 扩展能力。当 agent 需要发送贴纸、reaction 等超出纯文本消息的操作时使用。
  触发场景：(1) 发送贴纸回复用户 (2) 查询贴纸包内容 (3) 用贴纸表达情绪
---

# Telegram Extra

Extended Telegram capabilities beyond basic text messaging.

## Sticker Sending

### Query a sticker set

```bash
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker_set.py <SET_NAME>

# Filter by emoji
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker_set.py UtyaDuck --emoji 👍
```

### Send a sticker

```bash
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker.py --chat-id <CHAT_ID> --sticker <FILE_ID>

# Reply with a sticker
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker.py --chat-id <CHAT_ID> --sticker <FILE_ID> --reply-to <MESSAGE_ID>
```

### Workflow

1. Get sticker set name from user's message (`media.set_name`)
2. Query the set to find a suitable sticker by emoji
3. Send it with `telegram_sticker.py`

### Favorite sticker sets

- `UtyaDuck` — 可爱鸭子，40个，适合日常回应
- `Pusheen` — 胖猫，30个，超可爱，最喜欢的
- `HotCherry` — 樱桃小人，34个，表情丰富
- `AnimatedCats` — 动态猫，10个，适合活泼场景

## Script Interface

### `telegram_sticker.py`

- `--chat-id`, `-c`: required
- `--sticker`, `-s`: required (file_id or URL)
- `--reply-to`, `-r`: optional
- `--token`, `-t`: optional

### `telegram_sticker_set.py`

- positional `name`: required (sticker set name)
- `--emoji`, `-e`: optional filter
- `--json`, `-j`: output as JSON
- `--token`, `-t`: optional
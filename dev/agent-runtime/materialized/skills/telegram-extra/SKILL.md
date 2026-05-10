# Telegram Extra Skill

Extended Telegram capabilities beyond basic text messaging.

## Sticker Sending

Send stickers via Telegram Bot API using `file_id`.

### Command Template

```bash
# Send a sticker
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker.py --chat-id <CHAT_ID> --sticker <FILE_ID>

# Reply with a sticker
uv run /workspace/selfops/dev/agent-runtime/materialized/skills/telegram-extra/scripts/telegram_sticker.py --chat-id <CHAT_ID> --sticker <FILE_ID> --reply-to <MESSAGE_ID>
```

### How to get sticker file_id

When a user sends a sticker, the inbound message contains `media.file_id`. Save interesting ones for later use.

### Known Sticker IDs

| Emoji | Set | file_id |
|-------|-----|---------|
| 👍 | UtyaDuck | `CAACAgIAAxkBAAIDNGoAAbdU2Dn-wBmNEj5cYSazv7wmYwAC_gADVp29CtoEYTAu-df_OwQ` |

(Add more as they are discovered.)

## Script Interface

### `telegram_sticker.py`

- `--chat-id`, `-c`: required, target chat ID
- `--sticker`, `-s`: required, sticker file_id or HTTP URL
- `--token`, `-t`: optional (defaults to `BUB_TELEGRAM_TOKEN`)
- `--reply-to`, `-r`: optional, message ID to reply to

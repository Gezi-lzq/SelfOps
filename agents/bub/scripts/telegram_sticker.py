#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

"""
Telegram Bot Sticker Sender

Send stickers via Telegram Bot API using file_id.
"""

import argparse
import os
import sys

import requests


def send_sticker(
    bot_token: str,
    chat_id: str,
    sticker: str,
    reply_to_message_id: int | None = None,
) -> dict:
    """
    Send a sticker via Telegram Bot API.

    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        sticker: Sticker file_id or URL
        reply_to_message_id: Optional message ID to reply to

    Returns:
        API response as dict
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendSticker"

    payload = {
        "chat_id": chat_id,
        "sticker": sticker,
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Send stickers via Telegram Bot API")
    parser.add_argument("--chat-id", "-c", required=True, help="Target chat ID")
    parser.add_argument(
        "--sticker",
        "-s",
        required=True,
        help="Sticker file_id or HTTP URL to .webp sticker",
    )
    parser.add_argument("--token", "-t", help="Bot token (defaults to BUB_TELEGRAM_TOKEN env var)")
    parser.add_argument("--reply-to", "-r", type=int, help="Message ID to reply to")

    args = parser.parse_args()

    bot_token = args.token or os.environ.get("BUB_TELEGRAM_TOKEN")
    if not bot_token:
        print("❌ Error: Bot token required. Set BUB_TELEGRAM_TOKEN env var or use --token")
        sys.exit(1)

    try:
        result = send_sticker(bot_token, args.chat_id, args.sticker, args.reply_to)
        sticker_emoji = result.get("result", {}).get("sticker", {}).get("emoji", "")
        print(f"✅ Sticker sent successfully to {args.chat_id} {sticker_emoji}")
    except requests.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

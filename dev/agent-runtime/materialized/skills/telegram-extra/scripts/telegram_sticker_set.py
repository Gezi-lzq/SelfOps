#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

"""
Telegram Sticker Set Query

Query stickers from a sticker set by name, with optional emoji filter.
"""

import argparse
import json
import os
import sys

import requests


def get_sticker_set(bot_token: str, name: str) -> dict:
    """Get a sticker set by name."""
    url = f"https://api.telegram.org/bot{bot_token}/getStickerSet"
    response = requests.get(url, params={"name": name}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"API error: {data}")
    return data["result"]


def main():
    parser = argparse.ArgumentParser(description="Query Telegram sticker sets")
    parser.add_argument("name", help="Sticker set name (e.g. UtyaDuck)")
    parser.add_argument("--emoji", "-e", help="Filter by emoji")
    parser.add_argument("--token", "-t", help="Bot token (defaults to BUB_TELEGRAM_TOKEN)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    bot_token = args.token or os.environ.get("BUB_TELEGRAM_TOKEN")
    if not bot_token:
        print("❌ Error: Bot token required. Set BUB_TELEGRAM_TOKEN env var or use --token")
        sys.exit(1)

    try:
        result = get_sticker_set(bot_token, args.name)
    except requests.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        sys.exit(1)

    stickers = result["stickers"]
    if args.emoji:
        stickers = [s for s in stickers if s.get("emoji") == args.emoji]

    if args.json:
        output = [{"emoji": s.get("emoji", ""), "file_id": s["file_id"]} for s in stickers]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Set: {result['name']} ({len(stickers)} stickers)")
        for s in stickers:
            print(f"  {s.get('emoji', '?')} {s['file_id']}")


if __name__ == "__main__":
    main()

"""Mint a Telethon StringSession for the setup worker account.

Run this once, interactively, on a trusted machine. It logs in as a real
Telegram *user* (not a bot) — that is the only way to talk to BotFather — and
prints a session string. `main.py` reads that string from the environment; it
is never written to disk here and must never be committed.

The credentials this used to hardcode were published to a public repository and
are burned. Issue new ones at https://my.telegram.org and export them:

    export TELEGRAM_API_ID=...
    export TELEGRAM_API_HASH=...
    python generate_session.py
"""

import asyncio
import os
import sys

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")


async def main():
    async with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
        print("\nLogin successful. Session string below — treat it as a password:\n")
        print(client.session.save())


if __name__ == "__main__":
    if not API_ID or not API_HASH:
        sys.exit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH first (my.telegram.org).")
    print("You will be asked for your phone number, the login code, and 2FA if enabled.")
    asyncio.run(main())

"""
MadaraDefaultr – Entry Point
Powered by Madara

Run:  python3 main.py
Required secrets: BOT_TOKEN, API_ID, API_HASH
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

_required = ["BOT_TOKEN", "API_ID", "API_HASH"]
_missing  = [k for k in _required if not os.environ.get(k)]
if _missing:
    raise RuntimeError(
        f"ᴍɪssɪɴɢ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ sᴇᴄʀᴇᴛs: {', '.join(_missing)}\n"
        "sᴇᴛ ᴛʜᴇᴍ ɪɴ ʀᴇᴘʟɪᴛ sᴇᴄʀᴇᴛs ᴏʀ .ᴇɴᴠ ғɪʟᴇ."
    )

from pyrogram import Client, idle
from database import init_db
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME, POWERED_BY


async def main():
    print("🗄  ɪɴɪᴛɪᴀʟɪsɪɴɢ ᴅᴀᴛᴀʙᴀsᴇ…")
    await init_db()
    print("✅ ᴅᴀᴛᴀʙᴀsᴇ ʀᴇᴀᴅʏ.")

    client = Client(
        name="MadaraDefaultr",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        sleep_threshold=60,
        workdir="./sessions",
    )

    import MadaraDefaultr as _proxy
    _proxy._client = client

    print("📦 ʟᴏᴀᴅɪɴɢ ᴘʟᴜɢɪɴs…")
    import plugins.start        # noqa: F401
    import plugins.card_game    # noqa: F401
    import plugins.bomb_game    # noqa: F401
    import plugins.hack_game    # noqa: F401
    import plugins.social       # noqa: F401
    import plugins.rpg          # noqa: F401
    import plugins.economy      # noqa: F401
    import plugins.group_mgmt   # noqa: F401
    import plugins.uno_game     # noqa: F401
    import plugins.wordseek     # noqa: F401
    print("✅ ᴘʟᴜɢɪɴs ʟᴏᴀᴅᴇᴅ.")

    os.makedirs("sessions", exist_ok=True)
    os.makedirs("assets",   exist_ok=True)

    print(f"🤖 ᴄᴏɴɴᴇᴄᴛɪɴɢ {BOT_NAME}…")
    async with client:
        me = await client.get_me()
        print(
            f"\n{'='*52}\n"
            f"  {BOT_NAME} ɪs ᴏɴʟɪɴᴇ!\n"
            f"  ᴜsᴇʀɴᴀᴍᴇ : @{me.username}\n"
            f"  ʙᴏᴛ ɪᴅ   : {me.id}\n"
            f"  {POWERED_BY}\n"
            f"{'='*52}\n"
        )
        await idle()


if __name__ == "__main__":
    asyncio.run(main())

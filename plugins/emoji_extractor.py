"""
Temporary emoji extractor — send any message with premium custom emoji
to the bot in private and it will reply with all the emoji IDs found.
Remove this plugin once you've collected the IDs you need.
"""

import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import MessageEntityType


@app.on_message(filters.private & filters.command("extract_emoji"))
async def extract_emoji_cmd(_, msg):
    """Usage: reply to a message that contains custom emoji with /extract_emoji"""
    target = msg.reply_to_message or msg
    await _extract_and_reply(target, msg)


@app.on_message(filters.private & ~filters.command([]))
async def extract_emoji_any(_, msg):
    """Auto-extract from any private message that contains custom emoji entities."""
    if not msg.entities:
        return

    found = []
    for ent in msg.entities:
        if ent.type == MessageEntityType.CUSTOM_EMOJI:
            char = msg.text[ent.offset: ent.offset + ent.length] if msg.text else "?"
            found.append((char, str(ent.custom_emoji_id)))

    if not found:
        return

    lines = ["<b>🎯 Custom Emoji IDs found:</b>\n"]
    for char, eid in found:
        lines.append(f"• {char}  →  <code>{eid}</code>")

    await msg.reply("\n".join(lines), parse_mode="html")


async def _extract_and_reply(target_msg, reply_to_msg):
    if not target_msg.entities:
        await reply_to_msg.reply("No custom emoji entities found in that message.")
        return

    found = []
    for ent in target_msg.entities:
        if ent.type == MessageEntityType.CUSTOM_EMOJI:
            text = target_msg.text or target_msg.caption or ""
            char = text[ent.offset: ent.offset + ent.length] if text else "?"
            found.append((char, str(ent.custom_emoji_id)))

    if not found:
        await reply_to_msg.reply("No custom emoji entities found in that message.")
        return

    lines = ["<b>🎯 Custom Emoji IDs found:</b>\n"]
    for char, eid in found:
        lines.append(f"• {char}  →  <code>{eid}</code>")

    await reply_to_msg.reply("\n".join(lines), parse_mode="html")

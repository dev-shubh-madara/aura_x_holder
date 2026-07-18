"""
MadaraDefaultr – Social & Romance System
Powered by Madara
"""

import random
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from database import (
    get_or_create_user, get_relationship, set_relationship,
    update_coins, get_balance
)
from config import POWERED_BY, DIVORCE_COST, pe


# ─── /propose @username ───────────────────────────────────────────────────────

@app.on_message(filters.command("propose") & filters.group)
async def propose_cmd(_, msg: Message):
    if not msg.reply_to_message:
        await msg.reply(
            f"{pe('heart','💘')} ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴘʀᴏᴘᴏsᴇ!\n"
            f"ᴜsᴀɢᴇ: ʀᴇᴘʟʏ ᴛᴏ sᴏᴍᴇᴏɴᴇ ᴀɴᴅ ᴛʏᴘᴇ /propose\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    proposer = msg.from_user
    target   = msg.reply_to_message.from_user

    if target.is_bot:
        await msg.reply(
            f"🤖 ʏᴏᴜ ᴄᴀɴ'ᴛ ᴘʀᴏᴘᴏsᴇ ᴛᴏ ᴀ ʙᴏᴛ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return
    if proposer.id == target.id:
        await msg.reply(
            f"{pe('skull','💀')} ʏᴏᴜ ᴄᴀɴ'ᴛ ᴘʀᴏᴘᴏsᴇ ᴛᴏ ʏᴏᴜʀsᴇʟғ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await get_or_create_user(proposer.id, proposer.username or "", proposer.first_name or "")
    await get_or_create_user(target.id, target.username or "", target.first_name or "")

    rel_p = await get_relationship(proposer.id)
    rel_t = await get_relationship(target.id)

    if rel_p["status"] == "married":
        await msg.reply(
            f"💔 ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴍᴀʀʀɪᴇᴅ! ᴜsᴇ /divorce ғɪʀsᴛ.\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return
    if rel_t["status"] == "married":
        await msg.reply(
            f"💔 <b>{target.first_name}</b> ɪs ᴀʟʀᴇᴀᴅʏ ᴍᴀʀʀɪᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await set_relationship(proposer.id, target.id, "proposed")
    await set_relationship(target.id, proposer.id, "proposed")

    await msg.reply(
        f"💍 <b>{proposer.first_name}</b> ᴘʀᴏᴘᴏsᴇᴅ ᴛᴏ <b>{target.first_name}</b>!\n\n"
        f"💌 {target.mention}, ʀᴇᴘʟʏ ᴡɪᴛʜ /marry ᴛᴏ ᴀᴄᴄᴇᴘᴛ ᴀɴᴅ ɢᴇᴛ\n"
        f"{pe('sparkle','✨')} <b>5% ᴛᴀx ʀᴇᴅᴜᴄᴛɪᴏɴ</b> ᴏɴ ᴄᴏɪɴ ᴛʀᴀɴsғᴇʀs!\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ─── /marry ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("marry"))
async def marry_cmd(_, msg: Message):
    uid  = msg.from_user.id
    await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    rel  = await get_relationship(uid)

    if rel["status"] == "married":
        partner = rel["partner_id"]
        await msg.reply(
            f"💑 ʏᴏᴜ ᴀʀᴇ ᴍᴀʀʀɪᴇᴅ ᴛᴏ ᴜsᴇʀ <code>{partner}</code>!\n"
            f"{pe('coins_fly','💸')} ʏᴏᴜ ᴇɴᴊᴏʏ <b>5% ᴛᴀx ʀᴇᴅᴜᴄᴛɪᴏɴ</b> ᴏɴ /give.\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    if rel["status"] == "proposed":
        partner_id = rel["partner_id"]
        rel_p = await get_relationship(partner_id)
        if rel_p.get("partner_id") == uid and rel_p.get("status") == "proposed":
            await set_relationship(uid, partner_id, "married")
            await set_relationship(partner_id, uid, "married")
            await msg.reply(
                f"🎊 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴍᴀʀʀɪᴇᴅ!\n"
                f"💑 ᴜsᴇʀ <code>{partner_id}</code> & ʏᴏᴜ ᴀʀᴇ ᴀ ᴄᴏᴜᴘʟᴇ!\n"
                f"{pe('sparkle','✨')} ʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ <b>5% ᴛᴀx ʀᴇᴅᴜᴄᴛɪᴏɴ</b> ᴏɴ /give!\n\n"
                f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
            )
            return

    await msg.reply(
        f"💔 ʏᴏᴜ ᴀʀᴇ sɪɴɢʟᴇ! ɢᴇᴛ sᴏᴍᴇᴏɴᴇ ᴛᴏ /propose ᴛᴏ ʏᴏᴜ ғɪʀsᴛ.\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /divorce ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("divorce"))
async def divorce_cmd(_, msg: Message):
    uid  = msg.from_user.id
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    rel  = await get_relationship(uid)

    if rel["status"] != "married":
        await msg.reply(
            f"💔 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍᴀʀʀɪᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    if user["coins"] < DIVORCE_COST:
        await msg.reply(
            f"❌ ᴅɪᴠᴏʀᴄᴇ ᴄᴏsᴛs <b>{DIVORCE_COST:,}</b> ᴄᴏɪɴs.\n"
            f"{pe('coin','🪙')} ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ: <code>{user['coins']:,}</code>\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    partner_id = rel["partner_id"]
    await update_coins(uid, -DIVORCE_COST)
    await set_relationship(uid, 0, "single")
    await set_relationship(partner_id, 0, "single")

    await msg.reply(
        f"💔 ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴅɪᴠᴏʀᴄᴇᴅ.\n"
        f"{pe('coins_fly','💸')} <b>{DIVORCE_COST:,}</b> ᴄᴏɪɴs ᴅᴇᴅᴜᴄᴛᴇᴅ ᴀs ᴅɪᴠᴏʀᴄᴇ ғᴇᴇ.\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /couple ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("couple") & filters.group)
async def couple_cmd(_, msg: Message):
    responses = [
        f"{pe('heart','💘')} ʏᴏᴜ ᴀʀᴇ 99% ᴄᴏᴍᴘᴀᴛɪʙʟᴇ! ᴘᴇʀғᴇᴄᴛ ᴍᴀᴛᴄʜ! 🥰",
        f"💝 ᴀʙsᴏʟᴜᴛᴇʟʏ ᴍᴀᴅᴇ ғᴏʀ ᴇᴀᴄʜ ᴏᴛʜᴇʀ! 💑",
        f"😏 ᴍᴀʏʙᴇ... ᴊᴜsᴛ ᴍᴀʏʙᴇ 45% ᴄᴏᴍᴘᴀᴛɪʙʟᴇ.",
        f"🤔 ʜᴍᴍ 60% — ᴛʜᴇʀᴇ's ᴘᴏᴛᴇɴᴛɪᴀʟ!",
        f"{pe('skull','💀')} 0% — sᴛᴀʏ ᴀᴡᴀʏ ғʀᴏᴍ ᴇᴀᴄʜ ᴏᴛʜᴇʀ 😂",
        f"{pe('fire','🔥')} 78% — ᴛᴏᴛᴀʟ ғɪʀᴇ ᴄᴏᴍʙᴏ!",
    ]

    if msg.reply_to_message:
        p1 = msg.from_user.first_name
        p2 = msg.reply_to_message.from_user.first_name
    else:
        p1 = msg.from_user.first_name
        p2 = "sᴏᴍᴇᴏɴᴇ sᴘᴇᴄɪᴀʟ"

    result = random.choice(responses)
    pct    = random.randint(0, 100)
    bar    = pe('heart','❤️') * (pct // 10) + "🖤" * (10 - pct // 10)

    await msg.reply(
        f"💑 <b>ᴄᴏᴜᴘʟᴇ ᴍᴀᴛᴄʜᴍᴀᴋᴇʀ</b>\n\n"
        f"👤 {p1}  ×  {p2}\n\n"
        f"{pe('heart','❤️')} ᴄᴏᴍᴘᴀᴛɪʙɪʟɪᴛʏ: <b>{pct}%</b>\n"
        f"{bar}\n\n"
        f"{result}\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )

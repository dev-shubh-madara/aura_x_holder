"""
MadaraDefaultr – Group Management System
Powered by Madara
"""

import time
import asyncio
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode, ChatMembersFilter
from pyrogram.types import Message, ChatPermissions
from database import get_or_create_user, set_welcome, get_welcome
from config import POWERED_BY, PING_VIDEO, PING_IMAGE, BOT_NAME, VERSION, pe
import os


# ─── Admin check helper ───────────────────────────────────────────────────────

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status.value in ("administrator", "creator")
    except Exception:
        return False


# ─── /ping ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("ping"))
async def ping_cmd(_, msg: Message):
    start = time.time()
    sent  = await msg.reply("🏓 ᴘɪɴɢɪɴɢ...", parse_mode=ParseMode.HTML)
    ms    = int((time.time() - start) * 1000)

    caption = (
        f"🏓 <b>ᴘᴏɴɢ!</b>\n\n"
        f"⚡ ʟᴀᴛᴇɴᴄʏ: <code>{ms}ms</code>\n"
        f"🤖 ʙᴏᴛ: <b>{BOT_NAME}</b>\n"
        f"📦 ᴠᴇʀsɪᴏɴ: <code>{VERSION}</code>\n"
        f"✅ sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ & ʀᴇᴀᴅʏ\n\n"
        f"<i>{POWERED_BY}</i>"
    )
    await sent.delete()
    replied = False
    if os.path.exists(PING_VIDEO):
        try:
            await msg.reply_video(
                PING_VIDEO, caption=caption, parse_mode=ParseMode.HTML,
                no_sound=False, supports_streaming=True,
                width=1280, height=720, duration=10,
            )
            replied = True
        except Exception:
            pass
    if not replied and os.path.exists(PING_IMAGE):
        try:
            await msg.reply_photo(PING_IMAGE, caption=caption, parse_mode=ParseMode.HTML)
            replied = True
        except Exception:
            pass
    if not replied:
        await msg.reply(caption, parse_mode=ParseMode.HTML)


# ─── /stats ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("stats") & filters.group)
async def stats_cmd(_, msg: Message):
    try:
        chat  = await app.get_chat(msg.chat.id)
        count = chat.members_count or "N/A"
    except Exception:
        count = "N/A"

    await msg.reply(
        f"📊 <b>ɢʀᴏᴜᴘ sᴛᴀᴛs</b>\n\n"
        f"👥 ᴍᴇᴍʙᴇʀs: <code>{count}</code>\n"
        f"🤖 ʙᴏᴛ: <b>{BOT_NAME}</b>\n"
        f"📦 ᴠᴇʀsɪᴏɴ: <code>{VERSION}</code>\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /welcome [on/off] ───────────────────────────────────────────────────────

@app.on_message(filters.command("welcome") & filters.group)
async def welcome_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return

    args = msg.command
    if len(args) < 2 or args[1].lower() not in ("on", "off"):
        await msg.reply(
            f"ᴜsᴀɢᴇ: /welcome on | /welcome off\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    enable = args[1].lower() == "on"
    await set_welcome(msg.chat.id, enable)
    state  = "✅ ᴇɴᴀʙʟᴇᴅ" if enable else "❌ ᴅɪsᴀʙʟᴇᴅ"

    await msg.reply(
        f"👋 ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇs: <b>{state}</b>\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


@app.on_chat_member_updated(filters.group)
async def on_new_member(_, update):
    try:
        if not (update.new_chat_member and
                update.new_chat_member.status.value == "member" and
                update.old_chat_member and
                update.old_chat_member.status.value not in ("member", "administrator", "creator")):
            return

        w = await get_welcome(update.chat.id)
        if not w["enabled"]:
            return

        user = update.new_chat_member.user
        await get_or_create_user(user.id, user.username or "", user.first_name or "")

        await app.send_message(
            update.chat.id,
            f"👋 <b>ᴡᴇʟᴄᴏᴍᴇ, {user.mention}!</b>\n\n"
            f"ɢʟᴀᴅ ᴛᴏ ʜᴀᴠᴇ ʏᴏᴜ ɪɴ <b>{update.chat.title}</b>!\n"
            f"ᴜsᴇ /help ᴛᴏ sᴇᴇ ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ 🎮\n\n"
            f"<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


# ─── /staff ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("staff") & filters.group)
async def staff_cmd(_, msg: Message):
    try:
        admins = []
        async for member in app.get_chat_members(msg.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
            if not member.user.is_bot:
                title = f" [{member.custom_title}]" if member.custom_title else ""
                admins.append(f"• {member.user.mention}{title}")
        text = "\n".join(admins) if admins else "ɴᴏ sᴛᴀғғ ғᴏᴜɴᴅ."
    except Exception:
        text = "❌ ᴄᴏᴜʟᴅɴ'ᴛ ғᴇᴛᴄʜ sᴛᴀғғ ʟɪsᴛ."

    await msg.reply(
        f"👮 <b>ɢʀᴏᴜᴘ sᴛᴀғғ</b>\n\n{text}\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ─── /bots ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("bots") & filters.group)
async def bots_cmd(_, msg: Message):
    try:
        bots = []
        async for member in app.get_chat_members(msg.chat.id, filter=ChatMembersFilter.BOTS):
            bots.append(f"• @{member.user.username or member.user.first_name}")
        text = "\n".join(bots) if bots else "ɴᴏ ʙᴏᴛs ғᴏᴜɴᴅ."
    except Exception:
        text = "❌ ᴄᴏᴜʟᴅɴ'ᴛ ғᴇᴛᴄʜ ʙᴏᴛ ʟɪsᴛ."

    await msg.reply(
        f"🤖 <b>ʙᴏᴛs ɪɴ ɢʀᴏᴜᴘ</b>\n\n{text}\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ─── /pin /pinned /unpin ──────────────────────────────────────────────────────

@app.on_message(filters.command("pin") & filters.group)
async def pin_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    if not msg.reply_to_message:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘɪɴ ɪᴛ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await msg.reply_to_message.pin()
        await msg.reply(f"📌 ᴍᴇssᴀɢᴇ ᴘɪɴɴᴇᴅ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("pinned") & filters.group)
async def pinned_cmd(_, msg: Message):
    try:
        chat = await app.get_chat(msg.chat.id)
        if chat.pinned_message:
            await msg.reply(
                f"📌 <b>ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ:</b>\n\n"
                f"{chat.pinned_message.text or 'ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇ'}\n\n"
                f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
            )
        else:
            await msg.reply(f"ɴᴏ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ.\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception:
        await msg.reply(f"❌ ᴄᴏᴜʟᴅɴ'ᴛ ᴄʜᴇᴄᴋ.\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("unpin") & filters.group)
async def unpin_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.unpin_chat_message(msg.chat.id)
        await msg.reply(f"📌 ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


# ─── /ban /unban /kick /mute /unmute ─────────────────────────────────────────

async def get_target(msg: Message):
    if msg.reply_to_message:
        return msg.reply_to_message.from_user
    if len(msg.command) > 1:
        try:
            return await app.get_users(msg.command[1])
        except Exception:
            return None
    return None


@app.on_message(filters.command("ban") & filters.group)
async def ban_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    target = await get_target(msg)
    if not target:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ @ᴜsᴇʀɴᴀᴍᴇ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.ban_chat_member(msg.chat.id, target.id)
        await msg.reply(
            f"🚫 <b>{target.first_name}</b> ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("unban") & filters.group)
async def unban_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    target = await get_target(msg)
    if not target:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.unban_chat_member(msg.chat.id, target.id)
        await msg.reply(
            f"✅ <b>{target.first_name}</b> ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("kick") & filters.group)
async def kick_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    target = await get_target(msg)
    if not target:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.ban_chat_member(msg.chat.id, target.id)
        await asyncio.sleep(1)
        await app.unban_chat_member(msg.chat.id, target.id)
        await msg.reply(
            f"👢 <b>{target.first_name}</b> ʜᴀs ʙᴇᴇɴ ᴋɪᴄᴋᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("mute") & filters.group)
async def mute_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    target = await get_target(msg)
    if not target:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.restrict_chat_member(
            msg.chat.id, target.id,
            ChatPermissions(can_send_messages=False)
        )
        await msg.reply(
            f"🔇 <b>{target.first_name}</b> ʜᴀs ʙᴇᴇɴ ᴍᴜᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    target = await get_target(msg)
    if not target:
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.restrict_chat_member(
            msg.chat.id, target.id,
            ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_polls=True, can_add_web_page_previews=True
            )
        )
        await msg.reply(
            f"🔊 <b>{target.first_name}</b> ʜᴀs ʙᴇᴇɴ ᴜɴᴍᴜᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


# ─── /settitle /setdescription /setphoto /removephoto ────────────────────────

@app.on_message(filters.command("settitle") & filters.group)
async def settitle_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    args = msg.command
    if len(args) < 2:
        await msg.reply(f"ᴜsᴀɢᴇ: /settitle <ɴᴀᴍᴇ>\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    title = " ".join(args[1:])
    try:
        await app.set_chat_title(msg.chat.id, title)
        await msg.reply(f"✅ ᴛɪᴛʟᴇ sᴇᴛ ᴛᴏ <b>{title}</b>!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command(["setdescription", "setdesc"]) & filters.group)
async def setdesc_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    args = msg.command
    if len(args) < 2:
        await msg.reply(f"ᴜsᴀɢᴇ: /setdesc <ᴛᴇxᴛ>\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    desc = " ".join(args[1:])
    try:
        await app.set_chat_description(msg.chat.id, desc)
        await msg.reply(f"✅ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("setphoto") & filters.group)
async def setphoto_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    if not (msg.reply_to_message and msg.reply_to_message.photo):
        await msg.reply(f"ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴛᴏ sᴇᴛ ɪᴛ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        photo = await app.download_media(msg.reply_to_message.photo.file_id)
        await app.set_chat_photo(msg.chat.id, photo)
        await msg.reply(f"✅ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("removephoto") & filters.group)
async def removephoto_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    try:
        await app.delete_chat_photo(msg.chat.id)
        await msg.reply(f"✅ ɢʀᴏᴜᴘ ᴘʜᴏᴛᴏ ʀᴇᴍᴏᴠᴇᴅ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ ғᴀɪʟᴇᴅ: {e}\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)


# ─── /zombies ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("zombies") & filters.group)
async def zombies_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return

    sent = await msg.reply(f"🔍 sᴄᴀɴɴɪɴɢ ғᴏʀ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs...\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
    kicked = 0
    try:
        async for member in app.get_chat_members(msg.chat.id):
            if member.user.is_deleted:
                try:
                    await app.ban_chat_member(msg.chat.id, member.user.id)
                    await asyncio.sleep(0.5)
                    await app.unban_chat_member(msg.chat.id, member.user.id)
                    kicked += 1
                except Exception:
                    pass
    except Exception:
        pass

    await sent.edit_text(
        f"🧟 <b>ᴢᴏᴍʙɪᴇ ᴄʟᴇᴀɴᴜᴘ ᴅᴏɴᴇ!</b>\n\n"
        f"👢 ᴋɪᴄᴋᴇᴅ <code>{kicked}</code> ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs.\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /imposter on/off ─────────────────────────────────────────────────────────

_imposter_chats: set = set()

@app.on_message(filters.command("imposter") & filters.group)
async def imposter_cmd(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply(f"❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return
    args = msg.command
    if len(args) < 2 or args[1].lower() not in ("on", "off"):
        await msg.reply(f"ᴜsᴀɢᴇ: /imposter on | off\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return

    if args[1].lower() == "on":
        _imposter_chats.add(msg.chat.id)
        await msg.reply(
            f"🕵️ ɪᴍᴘᴏsᴛᴇʀ ᴡᴀᴛᴄʜᴇʀ <b>ᴏɴ</b>!\n"
            f"ɪ'ʟʟ ᴀʟᴇʀᴛ ᴡʜᴇɴ ᴍᴇᴍʙᴇʀs ᴄʜᴀɴɢᴇ ɴᴀᴍᴇs.\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
    else:
        _imposter_chats.discard(msg.chat.id)
        await msg.reply(
            f"🕵️ ɪᴍᴘᴏsᴛᴇʀ ᴡᴀᴛᴄʜᴇʀ <b>ᴏғғ</b>.\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )

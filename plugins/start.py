"""
MadaraDefaultr – Start / Help / Navigation handlers
Powered by Madara
"""

import os
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery
from database import get_or_create_user, get_top_users, get_user_rank
from utils.buttons import (
    start_keyboard, games_keyboard, help_menu_keyboard,
    help_back_keyboard, keyboard, primary_btn, success_btn,
    danger_btn, btn,
)
from config import BOT_NAME, POWERED_BY, VERSION, START_VIDEO, START_IMAGE, pe


# ═══════════════════════════════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("start") & filters.private)
async def start_private(_, msg: Message):
    user = await get_or_create_user(
        msg.from_user.id,
        msg.from_user.username or "",
        msg.from_user.first_name or ""
    )
    name = msg.from_user.first_name or "ᴘʟᴀʏᴇʀ"
    caption = (
        f"{pe('crown','👑')} <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {BOT_NAME}!</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👋 ʜᴇʏ <b>{name}</b>! ɪ'ᴍ ᴛʜᴇ ᴜʟᴛɪᴍᴀᴛᴇ ɢᴀᴍɪɴɢ ʙᴏᴛ!\n\n"
        f"{pe('gamepad','🎮')} ᴘʟᴀʏ ᴄᴀʀᴅ ɢᴀᴍᴇs, ʙᴏᴍʙ ᴘᴀssᴇs &amp; ʜᴀᴄᴋɪɴɢ\n"
        f"{pe('knife','⚔️')} ᴀᴛᴛᴀᴄᴋ, ʀᴏʙ &amp; ᴅᴏᴍɪɴᴀᴛᴇ ᴏᴛʜᴇʀ ᴘʟᴀʏᴇʀs\n"
        f"{pe('heart','💘')} ᴘʀᴏᴘᴏsᴇ, ᴍᴀʀʀʏ &amp; ᴇɴᴊᴏʏ ʀᴇᴡᴀʀᴅs\n"
        f"{pe('coin','🪙')} ᴇᴀʀɴ ᴅᴀɪʟʏ ᴄᴏɪɴs &amp; ᴄʟɪᴍʙ ᴛʜᴇ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ!\n\n"
        f"{pe('coin','🪙')} <b>ʙᴀʟᴀɴᴄᴇ:</b> <code>{user['coins']:,}</code>  "
        f"{pe('star','⭐')} <b>ᴡɪɴs:</b> <code>{user['wins']}</code>\n\n"
        f"<i>{POWERED_BY} | {VERSION}</i>"
    )
    sent = False
    if os.path.exists(START_VIDEO):
        try:
            await msg.reply_video(
                START_VIDEO, caption=caption,
                reply_markup=start_keyboard(), parse_mode=ParseMode.HTML,
                no_sound=False, supports_streaming=True,
                width=720, height=1280, duration=52,
            )
            sent = True
        except Exception as e:
            print(f"[start] reply_video failed: {e}")
    if not sent and os.path.exists(START_IMAGE):
        try:
            await msg.reply_photo(START_IMAGE, caption=caption,
                                  reply_markup=start_keyboard(), parse_mode=ParseMode.HTML)
            sent = True
        except Exception as e:
            print(f"[start] reply_photo failed: {e}")
    if not sent:
        await msg.reply(caption, reply_markup=start_keyboard(), parse_mode=ParseMode.HTML)


@app.on_message(filters.command("start") & filters.group)
async def start_group(_, msg: Message):
    await get_or_create_user(
        msg.from_user.id,
        msg.from_user.username or "",
        msg.from_user.first_name or ""
    )
    text = (
        f"🔥 <b>{BOT_NAME} ɪs ʜᴇʀᴇ!</b>\n\n"
        f"🎮 /card  💣 /bomb  🔐 /hack\n"
        f"💰 /daily  🎁 /claim  ⚔️ /kill\n"
        f"💘 /propose  🛒 /shop  📊 /ping\n\n"
        f"ᴛʏᴘᴇ /help ғᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs!\n\n"
        f"<i>{POWERED_BY}</i>"
    )
    await msg.reply(text, reply_markup=start_keyboard(), parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  /help  → category buttons
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("help"))
async def help_cmd(_, msg: Message):
    await msg.reply(
        f"📖 <b>{BOT_NAME} — ʜᴇʟᴘ ᴄᴇɴᴛʀᴇ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs:\n\n"
        f"🎮 <b>ɢᴀᴍᴇs</b> — ᴄᴀʀᴅ, ʙᴏᴍʙ, ʜᴀᴄᴋ\n"
        f"💰 <b>ᴇᴄᴏɴᴏᴍʏ</b> — ᴅᴀɪʟʏ, sʜᴏᴘ, ᴛʀᴀᴅᴇ\n"
        f"💘 <b>sᴏᴄɪᴀʟ</b> — ᴘʀᴏᴘᴏsᴇ, ᴍᴀʀʀʏ, ᴄᴏᴜᴘʟᴇ\n"
        f"⚔️ <b>ʀᴘɢ & ᴄᴏᴍʙᴀᴛ</b> — ᴋɪʟʟ, ʀᴏʙ, ᴘʀᴏᴛᴇᴄᴛ\n"
        f"⛩️ <b>ɢʀᴏᴜᴘ ᴍɢᴍᴛ</b> — ʙᴀɴ, ᴍᴜᴛᴇ, ᴡᴇʟᴄᴏᴍᴇ\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=help_menu_keyboard()
    )


# ─── help category callbacks ──────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^help_menu$"))
async def cb_help_menu(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"📖 <b>{BOT_NAME} — ʜᴇʟᴘ ᴄᴇɴᴛʀᴇ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs:\n\n"
        f"🎮 ɢᴀᴍᴇs — ᴄᴀʀᴅ, ʙᴏᴍʙ, ʜᴀᴄᴋ\n"
        f"💰 ᴇᴄᴏɴᴏᴍʏ — ᴅᴀɪʟʏ, sʜᴏᴘ, ᴛʀᴀᴅᴇ\n"
        f"💘 sᴏᴄɪᴀʟ — ᴘʀᴏᴘᴏsᴇ, ᴍᴀʀʀʏ, ᴄᴏᴜᴘʟᴇ\n"
        f"⚔️ ʀᴘɢ — ᴋɪʟʟ, ʀᴏʙ, ᴘʀᴏᴛᴇᴄᴛ\n"
        f"⛩️ ɢʀᴏᴜᴘ — ʙᴀɴ, ᴍᴜᴛᴇ, ᴡᴇʟᴄᴏᴍᴇ\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=help_menu_keyboard()
    )


@app.on_callback_query(filters.regex("^help_games$"))
async def cb_help_games(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"🎮 <b>ɢᴀᴍᴇs ᴄᴏᴍᴍᴀɴᴅs</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🃏 /card — sᴛᴀʀᴛ ᴄᴀʀᴅ ғʟɪᴘ ɢᴀᴍᴇ\n"
        f"   ↳ /bet &lt;ᴀᴍᴏᴜɴᴛ&gt; — ᴊᴏɪɴ ɢᴀᴍᴇ\n"
        f"   ↳ /flip a/b/c/d — ᴘʟᴀʏ ʏᴏᴜʀ ᴄᴀʀᴅ\n\n"
        f"💣 /bomb &lt;ᴀᴍᴏᴜɴᴛ&gt; — sᴛᴀʀᴛ ʙᴏᴍʙ ɢᴀᴍᴇ\n"
        f"   ↳ /join &lt;ᴀᴍᴏᴜɴᴛ&gt; — ᴊᴏɪɴ\n"
        f"   ↳ /pass — ᴘᴀss ᴛʜᴇ ʙᴏᴍʙ\n"
        f"   ↳ /bombcancel — ᴄᴀɴᴄᴇʟ (ᴀᴅᴍɪɴ)\n\n"
        f"🔐 /hack &lt;ʀᴇᴡᴀʀᴅ&gt; &lt;ᴅɪɢɪᴛs&gt; — ʜᴏsᴛ ʜᴀᴄᴋ\n"
        f"   ↳ /register &lt;ᴀᴍᴏᴜɴᴛ&gt; — ᴊᴏɪɴ\n"
        f"   ↳ /guess &lt;ɴᴜᴍʙᴇʀ&gt; — ɢᴜᴇss\n"
        f"   ↳ /end — ᴇɴᴅ ɢᴀᴍᴇ (ʜᴏsᴛ)\n\n"
        f"🏆 /rank — ʏᴏᴜʀ ʀᴀɴᴋ\n"
        f"📊 /leaders — ʙᴏᴍʙ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard(
            [primary_btn("🃏 ᴄᴀʀᴅ ɪɴғᴏ", data="info_card"),
             danger_btn("💣 ʙᴏᴍʙ ɪɴғᴏ",   data="info_bomb")],
            [success_btn("🔐 ʜᴀᴄᴋ ɪɴғᴏ",  data="info_hack")],
            [btn("🔙 ʙᴀᴄᴋ", data="help_menu")],
        )
    )


@app.on_callback_query(filters.regex("^help_economy$"))
async def cb_help_economy(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"💰 <b>ᴇᴄᴏɴᴏᴍʏ ᴄᴏᴍᴍᴀɴᴅs</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 /bal [@ᴜsᴇʀ] — ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ\n"
        f"📅 /daily — ᴄʟᴀɪᴍ ᴅᴀɪʟʏ sᴛʀᴇᴀᴋ ʀᴇᴡᴀʀᴅ\n"
        f"   ↳ sᴛʀᴇᴀᴋ ʙᴏɴᴜs ɪɴᴄʀᴇᴀsᴇs ᴇᴀᴄʜ ᴅᴀʏ!\n\n"
        f"🎁 /claim — ɢʀᴏᴜᴘ ʙᴏɴᴜs 2,000 ᴄᴏɪɴs\n"
        f"   ↳ ᴄᴏᴏʟᴅᴏᴡɴ: 24 ʜᴏᴜʀs ᴘᴇʀ ɢʀᴏᴜᴘ\n\n"
        f"💸 /give &lt;ᴀᴍᴏᴜɴᴛ&gt; — ᴛʀᴀɴsғᴇʀ ᴄᴏɪɴs\n"
        f"   ↳ ᴛᴀx: 10% (5% ɪғ ᴍᴀʀʀɪᴇᴅ ᴛᴏ ᴛᴀʀɢᴇᴛ)\n\n"
        f"🛒 /shop — ʙʀᴏᴡsᴇ ᴡᴇᴀᴘᴏɴs &amp; ᴀʀᴍᴏʀ\n"
        f"🎒 /inventory — ᴠɪᴇᴡ ʏᴏᴜʀ ɪᴛᴇᴍs\n"
        f"🏆 /top — ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard(
            [primary_btn("🛒 ᴏᴘᴇɴ sʜᴏᴘ", data="open_shop")],
            [btn("🔙 ʙᴀᴄᴋ", data="help_menu")],
        )
    )


@app.on_callback_query(filters.regex("^help_social$"))
async def cb_help_social(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"💘 <b>sᴏᴄɪᴀʟ & ʀᴏᴍᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅs</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"💍 /propose — ʀᴇᴘʟʏ ᴛᴏ ᴘʀᴏᴘᴏsᴇ ᴍᴀʀʀɪᴀɢᴇ\n"
        f"   ↳ ʙᴇɴᴇғɪᴛ: 5% ᴛᴀx ʀᴇᴅᴜᴄᴛɪᴏɴ ᴏɴ /give\n\n"
        f"💑 /marry — ᴀᴄᴄᴇᴘᴛ ᴘʀᴏᴘᴏsᴀʟ / ᴄʜᴇᴄᴋ sᴛᴀᴛᴜs\n\n"
        f"💔 /divorce — ᴇɴᴅ ᴍᴀʀʀɪᴀɢᴇ\n"
        f"   ↳ ᴄᴏsᴛ: 2,000 ᴄᴏɪɴs\n\n"
        f"💞 /couple — ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ ᴡɪᴛʜ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=help_back_keyboard()
    )


@app.on_callback_query(filters.regex("^help_combat$"))
async def cb_help_combat(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"⚔️ <b>ʀᴘɢ & ᴄᴏᴍʙᴀᴛ ᴄᴏᴍᴍᴀɴᴅs</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"💀 /kill — ʀᴇᴘʟʏ ᴛᴏ ᴀᴛᴛᴀᴄᴋ ᴀ ᴘʟᴀʏᴇʀ\n"
        f"   ↳ 50% sᴜᴄᴄᴇss | ʟᴏᴏᴛ 20-40% ʙᴀʟᴀɴᴄᴇ\n"
        f"   ↳ ᴄᴏᴏʟᴅᴏᴡɴ: 1 ʜᴏᴜʀ\n\n"
        f"🔪 /rob &lt;ᴀᴍᴏᴜɴᴛ&gt; — sᴛᴇᴀʟ ᴄᴏɪɴs\n"
        f"   ↳ ʀᴇQᴜɪʀᴇs ᴡᴇᴀᴘᴏɴ ғʀᴏᴍ /shop\n\n"
        f"🛡️ /protect 1d — 24ʜ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ sʜɪᴇʟᴅ\n"
        f"   ↳ ᴄᴏsᴛ: 1,000 ᴄᴏɪɴs\n\n"
        f"✨ /revive — ɪɴsᴛᴀɴᴛ ʀᴇᴠɪᴠᴀʟ\n"
        f"   ↳ ᴄᴏsᴛ: 500 ᴄᴏɪɴs\n\n"
        f"📊 /status — ᴠɪᴇᴡ ʏᴏᴜʀ ᴄᴏᴍʙᴀᴛ sᴛᴀᴛs\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=help_back_keyboard()
    )


@app.on_callback_query(filters.regex("^help_group$"))
async def cb_help_group(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"⛩️ <b>ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴄᴏᴍᴍᴀɴᴅs</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🏓 /ping — ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ & sᴛᴀᴛᴜs\n"
        f"📊 /stats — ɢʀᴏᴜᴘ sᴛᴀᴛɪsᴛɪᴄs\n"
        f"👮 /staff — ʟɪsᴛ ᴀᴅᴍɪɴs\n"
        f"🤖 /bots — ʟɪsᴛ ʙᴏᴛs\n\n"
        f"<b>ᴀᴅᴍɪɴ ᴏɴʟʏ:</b>\n"
        f"👋 /welcome on/off — ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇs\n"
        f"📌 /pin — ᴘɪɴ ᴍᴇssᴀɢᴇ (ʀᴇᴘʟʏ)\n"
        f"📌 /pinned — sʜᴏᴡ ᴘɪɴɴᴇᴅ ᴍsɢ\n"
        f"📌 /unpin — ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇ\n"
        f"🚫 /ban — ʙᴀɴ ᴜsᴇʀ\n"
        f"✅ /unban — ᴜɴʙᴀɴ ᴜsᴇʀ\n"
        f"👢 /kick — ᴋɪᴄᴋ ᴜsᴇʀ\n"
        f"🔇 /mute — ᴍᴜᴛᴇ ᴜsᴇʀ\n"
        f"🔊 /unmute — ᴜɴᴍᴜᴛᴇ ᴜsᴇʀ\n"
        f"✏️ /settitle &lt;ɴᴀᴍᴇ&gt; — sᴇᴛ ᴛɪᴛʟᴇ\n"
        f"📝 /setdesc &lt;ᴛᴇxᴛ&gt; — sᴇᴛ ᴅᴇsᴄ\n"
        f"🖼 /setphoto — sᴇᴛ ᴘʜᴏᴛᴏ (ʀᴇᴘʟʏ)\n"
        f"🗑 /removephoto — ᴄʟᴇᴀʀ ᴘʜᴏᴛᴏ\n"
        f"🧟 /zombies — ᴋɪᴄᴋ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄs\n"
        f"🕵️ /imposter on/off — ᴜsᴇʀɴᴀᴍᴇ ᴡᴀᴛᴄʜᴇʀ\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=help_back_keyboard()
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Navigation callbacks
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^start$"))
async def cb_start(_, cq: CallbackQuery):
    user = await get_or_create_user(
        cq.from_user.id,
        cq.from_user.username or "",
        cq.from_user.first_name or ""
    )
    name = cq.from_user.first_name or "ᴘʟᴀʏᴇʀ"
    await cq.edit_message_text(
        f"👑 <b>ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ, {name}!</b>\n\n"
        f"🔥 <b>{BOT_NAME}</b>\n\n"
        f"🪙 <b>ʙᴀʟᴀɴᴄᴇ:</b> <code>{user['coins']:,}</code> ᴄᴏɪɴs\n\n"
        f"<i>{POWERED_BY} | {VERSION}</i>",
        reply_markup=start_keyboard(), parse_mode=ParseMode.HTML
    )


@app.on_callback_query(filters.regex("^games_menu$"))
async def cb_games(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"⚔️ <b>ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ɢᴀᴍᴇ</b>\n\n"
        f"🃏 <b>ᴄᴀʀᴅ ɢᴀᴍᴇ</b> — ғʟɪᴘ ᴄᴀʀᴅs, ʜɪɢʜᴇsᴛ ᴡɪɴs\n"
        f"💣 <b>ʙᴏᴍʙ ɢᴀᴍᴇ</b> — ᴘᴀss ᴛʜᴇ ʙᴏᴍʙ, ʟᴀsᴛ ᴀʟɪᴠᴇ ᴡɪɴs\n"
        f"🔐 <b>ʜᴀᴄᴋ ɢᴀᴍᴇ</b> — ɢᴜᴇss ᴛʜᴇ sᴇᴄʀᴇᴛ ᴘᴀssᴡᴏʀᴅ\n\n"
        f"<i>{POWERED_BY}</i>",
        reply_markup=games_keyboard(), parse_mode=ParseMode.HTML
    )


@app.on_callback_query(filters.regex("^wallet$"))
async def cb_wallet(_, cq: CallbackQuery):
    user = await get_or_create_user(
        cq.from_user.id, cq.from_user.username or "", cq.from_user.first_name or ""
    )
    rank = await get_user_rank(cq.from_user.id)
    name = cq.from_user.first_name or "ᴘʟᴀʏᴇʀ"
    await cq.edit_message_text(
        f"👑 <b>ᴡᴀʟʟᴇᴛ — {name}</b>\n\n"
        f"🪙 ᴄᴏɪɴs: <code>{user['coins']:,}</code>\n"
        f"🏆 ᴡɪɴs: <code>{user['wins']}</code>\n"
        f"💔 ʟᴏssᴇs: <code>{user['losses']}</code>\n"
        f"🎮 ɢᴀᴍᴇs: <code>{user['games_played']}</code>\n"
        f"💎 ʀᴀɴᴋ: #{rank}\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard(
            [primary_btn("🏆 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", data="leaderboard")],
            [btn("🔙 ʙᴀᴄᴋ", data="start")],
        )
    )


@app.on_callback_query(filters.regex("^leaderboard$"))
async def cb_leaderboard(_, cq: CallbackQuery):
    users  = await get_top_users(10)
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7
    lines  = [
        f"{medals[i]} <b>{u['first_name'] or u['username'] or 'Unknown'}</b> — <code>{u['coins']:,}</code>"
        for i, u in enumerate(users)
    ]
    await cq.edit_message_text(
        f"🏆 <b>ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n\n" + "\n".join(lines) + f"\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard([btn("🔙 ʙᴀᴄᴋ", data="start")])
    )


@app.on_callback_query(filters.regex("^open_shop$"))
async def cb_open_shop(_, cq: CallbackQuery):
    from utils.buttons import shop_keyboard
    from config import SHOP_ITEMS
    lines = [
        f"{it['name']} — <code>{it['price']:,}</code>\n  ↳ {it['desc']}"
        for it in SHOP_ITEMS.values()
    ]
    await cq.edit_message_text(
        f"🛒 <b>ᴍᴀᴅᴀʀᴀ sʜᴏᴘ</b>\n\n" + "\n\n".join(lines) +
        f"\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=shop_keyboard()
    )


# ─── Game info callbacks ──────────────────────────────────────────────────────

@app.on_callback_query(filters.regex("^info_card$"))
async def cb_info_card(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"🃏 <b>ᴄᴀʀᴅ ɢᴀᴍᴇ ʀᴜʟᴇs</b>\n\n"
        "• ᴇᴀᴄʜ ᴘʟᴀʏᴇʀ ɢᴇᴛs 4 ʜɪᴅᴅᴇɴ ᴄᴀʀᴅs: ᴀ, ʙ, ᴄ, ᴅ\n"
        "• ᴄᴀʀᴅ sᴜᴍ ɪs ᴇQᴜᴀʟ — ᴏɴʟʏ sᴛʀᴀᴛᴇɢʏ ᴡɪɴs!\n"
        "• ᴇᴀᴄʜ ʀᴏᴜɴᴅ, ғʟɪᴘ ᴏɴᴇ — ʜɪɢʜᴇsᴛ ᴡɪɴs\n"
        "• 4 ʀᴏᴜɴᴅs — ʜɪɢʜᴇsᴛ sᴄᴏʀᴇ ᴡɪɴs ᴛʜᴇ ᴘᴏᴛ 🏆\n"
        "• 60s ᴛɪᴍᴇʀ ᴘᴇʀ ᴛᴜʀɴ\n\n"
        "<b>ᴄᴏᴍᴍᴀɴᴅs:</b> /card | /bet | /flip a/b/c/d\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard([btn("🔙 ʙᴀᴄᴋ", data="help_games")])
    )


@app.on_callback_query(filters.regex("^info_bomb$"))
async def cb_info_bomb(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"💣 <b>ʙᴏᴍʙ ɢᴀᴍᴇ ʀᴜʟᴇs</b>\n\n"
        "• ᴘᴀʏ ᴇɴᴛʀʏ ғᴇᴇ ᴛᴏ ᴊᴏɪɴ\n"
        "• ᴀ ʙᴏᴍʙ ɪs sᴇᴄʀᴇᴛʟʏ ᴀssɪɢɴᴇᴅ\n"
        "• ᴜsᴇ /pass — ʙᴏᴍʙ ᴇxᴘʟᴏᴅᴇs ʀᴀɴᴅᴏᴍʟʏ 💥\n"
        "• ʟᴀsᴛ ᴘʟᴀʏᴇʀ ᴀʟɪᴠᴇ ᴡɪɴs!\n\n"
        "<b>ᴄᴏᴍᴍᴀɴᴅs:</b> /bomb | /join | /pass | /rank\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard([btn("🔙 ʙᴀᴄᴋ", data="help_games")])
    )


@app.on_callback_query(filters.regex("^info_hack$"))
async def cb_info_hack(_, cq: CallbackQuery):
    await cq.edit_message_text(
        f"🔐 <b>ʜᴀᴄᴋ ɢᴀᴍᴇ ʀᴜʟᴇs</b>\n\n"
        "• ʜᴏsᴛ sᴇᴛs ᴀ sᴇᴄʀᴇᴛ ᴘᴀssᴡᴏʀᴅ (3-6 ᴅɪɢɪᴛs)\n"
        "• ᴘʟᴀʏᴇʀs ʀᴇɢɪsᴛᴇʀ & ɢᴜᴇss\n"
        "• 🟢 ʜᴀᴄᴋs = ʀɪɢʜᴛ ᴅɪɢɪᴛ, ʀɪɢʜᴛ ᴘᴏs\n"
        "• 🟡 ɢʟɪᴛᴄʜᴇs = ʀɪɢʜᴛ ᴅɪɢɪᴛ, ᴡʀᴏɴɢ ᴘᴏs\n"
        "• ғɪʀsᴛ ᴛᴏ ᴄʀᴀᴄᴋ ᴡɪɴs!\n\n"
        "<b>ᴄᴏᴍᴍᴀɴᴅs:</b> /hack | /register | /guess | /end\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard([btn("🔙 ʙᴀᴄᴋ", data="help_games")])
    )


# ─── /top ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("top"))
async def top_cmd(_, msg: Message):
    users  = await get_top_users(10)
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7
    lines  = [
        f"{medals[i]} <b>{u['first_name'] or u['username'] or 'Unknown'}</b> — <code>{u['coins']:,}</code> ᴄᴏɪɴs"
        for i, u in enumerate(users)
    ]
    await msg.reply(
        f"🏆 <b>ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n\n" + "\n".join(lines) + f"\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )

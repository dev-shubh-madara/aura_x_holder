"""
MadaraDefaultr – RPG & Combat System
Powered by Madara
"""

import time
import random
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from database import (
    get_or_create_user, get_combat, update_combat,
    update_coins, get_balance, has_item, is_protected,
)
from config import (
    POWERED_BY, KILL_COOLDOWN, KILL_SUCCESS_RATE,
    KILL_LOOT_MIN, KILL_LOOT_MAX, PROTECT_COST, REVIVE_COST, pe
)


# ─── /kill [@user] ────────────────────────────────────────────────────────────

@app.on_message(filters.command("kill") & filters.group)
async def kill_cmd(_, msg: Message):
    if not msg.reply_to_message:
        await msg.reply(
            f"{pe('knife','⚔️')} ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴛᴛᴀᴄᴋ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    attacker = msg.from_user
    victim   = msg.reply_to_message.from_user

    if victim.is_bot or victim.id == attacker.id:
        await msg.reply(
            f"❌ ɪɴᴠᴀʟɪᴅ ᴛᴀʀɢᴇᴛ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await get_or_create_user(attacker.id, attacker.username or "", attacker.first_name or "")
    await get_or_create_user(victim.id,   victim.username   or "", victim.first_name   or "")

    c_att = await get_combat(attacker.id)
    now   = time.time()

    if now - c_att["last_kill"] < KILL_COOLDOWN:
        left = int(KILL_COOLDOWN - (now - c_att["last_kill"]))
        mins = left // 60
        await msg.reply(
            f"⏳ ᴄᴏᴏʟᴅᴏᴡɴ! ᴡᴀɪᴛ <b>{mins}m {left%60}s</b> ʙᴇғᴏʀᴇ ɴᴇxᴛ ᴀᴛᴛᴀᴄᴋ.\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    if await is_protected(victim.id):
        await msg.reply(
            f"🛡️ <b>{victim.first_name}</b> ɪs ᴘʀᴏᴛᴇᴄᴛᴇᴅ! ʏᴏᴜʀ ᴀᴛᴛᴀᴄᴋ ғᴀɪʟᴇᴅ.\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    await update_combat(attacker.id, last_kill=now)

    has_sword = await has_item(attacker.id, "sword")
    loot_max  = KILL_LOOT_MAX + (0.20 if has_sword else 0)

    if random.random() < KILL_SUCCESS_RATE:
        v_bal    = await get_balance(victim.id)
        loot_pct = random.uniform(KILL_LOOT_MIN, loot_max)
        loot     = max(int(v_bal * loot_pct), 50)

        await update_coins(victim.id,   -loot)
        await update_coins(attacker.id,  loot)
        await update_combat(attacker.id, kills=c_att["kills"] + 1)
        c_v = await get_combat(victim.id)
        await update_combat(victim.id, deaths=c_v["deaths"] + 1)

        await msg.reply(
            f"{pe('skull','💀')} <b>{attacker.first_name}</b> ᴋɪʟʟᴇᴅ <b>{victim.first_name}</b>!\n\n"
            f"{pe('money','💰')} ʟᴏᴏᴛᴇᴅ: <code>{loot:,}</code> ᴄᴏɪɴs ({int(loot_pct*100)}%)\n"
            f"{pe('knife','🗡️')} ᴋɪʟʟs: {c_att['kills']+1}\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
    else:
        await msg.reply(
            f"😅 <b>{attacker.first_name}</b> ᴀᴛᴛᴀᴄᴋᴇᴅ <b>{victim.first_name}</b> ʙᴜᴛ ᴍɪssᴇᴅ!\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )


# ─── /rob [amount] @user ──────────────────────────────────────────────────────

@app.on_message(filters.command("rob") & filters.group)
async def rob_cmd(_, msg: Message):
    if not msg.reply_to_message:
        await msg.reply(
            f"{pe('knife','🔪')} ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ + /rob &lt;amount&gt;\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    robber = msg.from_user
    victim = msg.reply_to_message.from_user

    if victim.is_bot or victim.id == robber.id:
        await msg.reply(f"❌ ɪɴᴠᴀʟɪᴅ ᴛᴀʀɢᴇᴛ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return

    args = msg.command
    if len(args) < 2:
        await msg.reply(
            f"ᴜsᴀɢᴇ: /rob &lt;amount&gt; (ʀᴇᴘʟʏ ᴛᴏ ᴛᴀʀɢᴇᴛ)\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        amount = int(args[1])
        assert amount > 0
    except (ValueError, AssertionError):
        await msg.reply(f"❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ!\n\n<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        return

    has_weapon = (
        await has_item(robber.id, "knife") or
        await has_item(robber.id, "gun")   or
        await has_item(robber.id, "sword")
    )
    if not has_weapon:
        await msg.reply(
            f"{pe('knife','🔪')} ʏᴏᴜ ɴᴇᴇᴅ ᴀ ᴡᴇᴀᴘᴏɴ ᴛᴏ ʀᴏʙ!\n"
            f"ʙᴜʏ ᴏɴᴇ ғʀᴏᴍ /shop\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    if await is_protected(victim.id):
        await msg.reply(
            f"🛡️ <b>{victim.first_name}</b> ɪs ᴘʀᴏᴛᴇᴄᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await get_or_create_user(robber.id, robber.username or "", robber.first_name or "")
    await get_or_create_user(victim.id,  victim.username  or "", victim.first_name  or "")
    v_bal = await get_balance(victim.id)

    if v_bal < amount:
        await msg.reply(
            f"❌ <b>{victim.first_name}</b> ᴏɴʟʏ ʜᴀs <code>{v_bal:,}</code> ᴄᴏɪɴs!\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    await update_coins(victim.id,  -amount)
    await update_coins(robber.id,   amount)

    await msg.reply(
        f"🔫 <b>{robber.first_name}</b> ʀᴏʙʙᴇᴅ <b>{victim.first_name}</b>!\n\n"
        f"{pe('money','💰')} sᴛᴏʟᴇ: <code>{amount:,}</code> ᴄᴏɪɴs\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /protect 1d ─────────────────────────────────────────────────────────────

@app.on_message(filters.command("protect"))
async def protect_cmd(_, msg: Message):
    uid  = msg.from_user.id
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")

    if user["coins"] < PROTECT_COST:
        await msg.reply(
            f"❌ ɴᴇᴇᴅ <b>{PROTECT_COST:,}</b> ᴄᴏɪɴs ғᴏʀ 24ʜ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ.\n"
            f"{pe('coin','🪙')} ʙᴀʟᴀɴᴄᴇ: <code>{user['coins']:,}</code>\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    if await is_protected(uid):
        await msg.reply(
            f"🛡️ ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ!\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -PROTECT_COST)
    await update_combat(uid, protection_until=time.time() + 86400)

    await msg.reply(
        f"🛡️ <b>24ʜ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n\n"
        f"{pe('coins_fly','💸')} <b>{PROTECT_COST:,}</b> ᴄᴏɪɴs ᴅᴇᴅᴜᴄᴛᴇᴅ.\n"
        f"🛡️ ɴᴏ ᴏɴᴇ ᴄᴀɴ /kill ᴏʀ /rob ʏᴏᴜ ғᴏʀ 24 ʜᴏᴜʀs!\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /revive ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("revive"))
async def revive_cmd(_, msg: Message):
    uid  = msg.from_user.id
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")

    if user["coins"] < REVIVE_COST:
        await msg.reply(
            f"❌ ʀᴇᴠɪᴠᴀʟ ᴄᴏsᴛs <b>{REVIVE_COST:,}</b> ᴄᴏɪɴs.\n"
            f"{pe('coin','🪙')} ʙᴀʟᴀɴᴄᴇ: <code>{user['coins']:,}</code>\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -REVIVE_COST)
    await update_combat(uid, deaths=0)

    await msg.reply(
        f"{pe('sparkle','✨')} <b>ʀᴇᴠɪᴠᴇᴅ!</b> ʏᴏᴜ ᴀʀᴇ ʙᴀᴄᴋ ɪɴ ᴀᴄᴛɪᴏɴ!\n"
        f"{pe('coins_fly','💸')} <b>{REVIVE_COST:,}</b> ᴄᴏɪɴs ᴅᴇᴅᴜᴄᴛᴇᴅ.\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )


# ─── /status ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("status"))
async def status_cmd(_, msg: Message):
    uid  = msg.from_user.id
    name = msg.from_user.first_name or "ᴘʟᴀʏᴇʀ"
    await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    c    = await get_combat(uid)
    prot = c["protection_until"] > time.time()
    prot_left = int(max(0, c["protection_until"] - time.time()) // 60)
    prot_str = (f"{pe('checkmark','✅')} ᴀᴄᴛɪᴠᴇ ({prot_left}m ʟᴇғᴛ)"
                if prot else "❌ ɴᴏɴᴇ")

    await msg.reply(
        f"{pe('knife','⚔️')} <b>ᴄᴏᴍʙᴀᴛ sᴛᴀᴛᴜs — {name}</b>\n\n"
        f"{pe('knife','🗡️')} ᴋɪʟʟs: <code>{c['kills']}</code>\n"
        f"{pe('skull','💀')} ᴅᴇᴀᴛʜs: <code>{c['deaths']}</code>\n"
        f"🛡️ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ: {prot_str}\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
    )

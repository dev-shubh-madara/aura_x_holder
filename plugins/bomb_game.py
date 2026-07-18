"""
MadaraDefaultr – Bomb Game
Powered by Madara

Rules:
 • Players pay entry fee to join.
 • Bomb assigned to random player.
 • Each round: holder must /pass to move it.
 • Bomb explodes randomly after each round.
 • Last player alive wins the pot.
"""

import asyncio
import random

import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery
from utils.safe_send import safe_reply, safe_send
from database import (
    get_or_create_user, get_balance, update_coins,
    record_win, record_loss, get_bomb_leaderboard, get_user_rank
)
from utils.buttons import keyboard, primary_btn, success_btn, danger_btn, btn
from config import POWERED_BY, BOMB_ROUND_TIMEOUT, pe


bomb_games: dict[int, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════════
#  /bomb – start game
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("bomb") & filters.group)
async def start_bomb(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id in bomb_games:
        await msg.reply(
            "⚠️ A bomb game is already running!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML
        )
        return

    args = msg.command
    if len(args) < 2:
        await msg.reply(
            "Usage: <code>/bomb &lt;entry_amount&gt;</code>\nExample: /bomb 500\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    try:
        amount = int(args[1])
        assert amount > 0
    except (ValueError, AssertionError):
        await msg.reply("❌ Invalid amount!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    uid = msg.from_user.id
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    if user["coins"] < amount:
        await msg.reply(
            f"❌ Need <b>{amount:,}</b> coins. Balance: <code>{user['coins']:,}</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -amount)
    bomb_games[chat_id] = {
        "phase": "waiting",
        "host": uid,
        "entry_fee": amount,
        "pot": amount,
        "players": {uid: msg.from_user.first_name or "Player"},
        "alive": [],
        "bomb_holder": None,
        "round": 0,
        "passed": False,
    }

    kb = keyboard(
        [success_btn(f"💥 Join ({amount:,} coins)", data=f"bomb_join_{chat_id}")],
        [danger_btn("❌ Cancel", data=f"bcancel_{chat_id}")],
    )
    await msg.reply(
        f"<b>💣 Bomb Game Started!</b>\n\n"
        f"👤 Host: <b>{msg.from_user.first_name}</b>\n"
        f"💰 Entry Fee: <code>{amount:,}</code> coins\n"
        f"🏆 Pot: <code>{amount:,}</code> coins\n\n"
        f"Use <b>/join {amount}</b> or tap below to join!\n"
        f"Game starts in <b>30 seconds</b> or when host is ready.\n\n"
        f"<i>{POWERED_BY}</i>",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    # Auto-start after 30s
    await asyncio.sleep(30)
    if chat_id in bomb_games and bomb_games[chat_id]["phase"] == "waiting":
        if len(bomb_games[chat_id]["players"]) >= 2:
            await _begin_bomb_game(msg, chat_id)
        else:
            for pid in list(bomb_games[chat_id]["players"]):
                await update_coins(pid, bomb_games[chat_id]["entry_fee"])
            del bomb_games[chat_id]
            await msg.reply(
                "❌ Not enough players. Bomb game cancelled & fees refunded.\n\n" + POWERED_BY,
                parse_mode=ParseMode.HTML
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  /join
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("join") & filters.group)
async def join_bomb(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in bomb_games or bomb_games[chat_id]["phase"] != "waiting":
        await msg.reply("❌ No bomb game waiting. Start one with /bomb!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = bomb_games[chat_id]
    uid = msg.from_user.id
    if uid in g["players"]:
        await msg.reply("⚠️ Already joined!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    fee = g["entry_fee"]
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    if user["coins"] < fee:
        await msg.reply(
            f"❌ Need <b>{fee:,}</b> coins. Balance: <code>{user['coins']:,}</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -fee)
    g["players"][uid] = msg.from_user.first_name or "Player"
    g["pot"] += fee

    await msg.reply(
        f"✅ <b>{msg.from_user.first_name}</b> joined the bomb game!\n"
        f"👥 Players: {len(g['players'])}\n"
        f"🏆 Pot: <code>{g['pot']:,}</code> coins\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ─── Inline join ──────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^bomb_join_(-?\d+)$"))
async def cb_bomb_join(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    if chat_id not in bomb_games or bomb_games[chat_id]["phase"] != "waiting":
        await cq.answer("Game not available!", show_alert=True)
        return
    g = bomb_games[chat_id]
    uid = cq.from_user.id
    if uid in g["players"]:
        await cq.answer("Already joined!", show_alert=True)
        return
    fee = g["entry_fee"]
    user = await get_or_create_user(uid, cq.from_user.username or "", cq.from_user.first_name or "")
    if user["coins"] < fee:
        await cq.answer(f"Need {fee:,} coins!", show_alert=True)
        return
    await update_coins(uid, -fee)
    g["players"][uid] = cq.from_user.first_name or "Player"
    g["pot"] += fee
    await cq.answer("✅ Joined!")
    await cq.message.reply(
        f"✅ <b>{cq.from_user.first_name}</b> joined! Players: {len(g['players'])}\n\n" + POWERED_BY,
        parse_mode=ParseMode.HTML
    )


@app.on_callback_query(filters.regex(r"^bcancel_(-?\d+)$"))
async def cb_bomb_cancel_btn(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    if chat_id not in bomb_games:
        await cq.answer("No game!", show_alert=True)
        return
    g = bomb_games[chat_id]
    if cq.from_user.id != g["host"]:
        await cq.answer("Only the host can cancel!", show_alert=True)
        return
    for pid in g["players"]:
        await update_coins(pid, g["entry_fee"])
    del bomb_games[chat_id]
    await cq.edit_message_text("❌ Bomb game cancelled. Fees refunded.\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  Internal – begin game
# ═══════════════════════════════════════════════════════════════════════════════

async def _begin_bomb_game(msg, chat_id: int):
    g = bomb_games[chat_id]
    g["phase"] = "playing"
    g["alive"] = list(g["players"].keys())
    g["bomb_holder"] = random.choice(g["alive"])
    g["round"] = 1
    g["timer_task"] = None

    await msg.reply(
        f"<b>💣 Bomb Game Begins!</b>\n\n"
        f"👥 Players: {len(g['alive'])}\n"
        f"🏆 Pot: <code>{g['pot']:,}</code> coins\n\n"
        f"💥 The bomb has been secretly assigned...\n"
        f"Only the holder knows — check your DM!\n\n"
        f"Use /pass to pass the bomb!\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )
    try:
        await app.send_message(
            g["bomb_holder"],
            f"💣 <b>YOU HAVE THE BOMB!</b>\n\nUse /pass in the group to pass it!\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    _schedule_bomb_timer(msg, chat_id)


def _schedule_bomb_timer(msg, chat_id: int):
    """Cancel any existing timer and start a fresh cancellable one."""
    g = bomb_games.get(chat_id)
    if not g:
        return
    if g.get("timer_task") and not g["timer_task"].done():
        g["timer_task"].cancel()
    round_token = g["round"]

    async def _timer():
        await asyncio.sleep(BOMB_ROUND_TIMEOUT)
        if chat_id not in bomb_games:
            return
        if bomb_games[chat_id].get("round") != round_token:
            return
        if bomb_games[chat_id]["phase"] != "playing":
            return
        g2 = bomb_games[chat_id]
        if not g2["passed"]:
            await safe_send(
                chat_id,
                f"⏱ <b>{g2['players'].get(g2['bomb_holder'], 'Player')}</b> didn't pass in time!\n"
                f"💥 Checking if bomb explodes…\n\n" + POWERED_BY,
            )
        await _maybe_explode(msg, chat_id)

    g["passed"] = False
    g["timer_task"] = asyncio.create_task(_timer())


async def _maybe_explode(msg, chat_id: int):
    if chat_id not in bomb_games:
        return
    g = bomb_games[chat_id]
    if len(g["alive"]) <= 1:
        await _end_bomb_game(msg, chat_id)
        return

    explode_chance = max(0.3, 1 / len(g["alive"]))
    if random.random() < explode_chance or not g["passed"]:
        victim = g["bomb_holder"]
        victim_name = g["players"].get(victim, "Player")
        g["alive"].remove(victim)
        await record_loss(victim, "bomb_stats")
        await safe_send(
            chat_id,
            f"💥 <b>BOOM!</b> The bomb exploded on <b>{victim_name}</b>!\n\n"
            f"☠️ {victim_name} is eliminated!\n"
            f"👥 Remaining: {len(g['alive'])} players\n\n"
            f"<i>{POWERED_BY}</i>",
        )
        if len(g["alive"]) <= 1:
            await _end_bomb_game(msg, chat_id)
            return
        g["bomb_holder"] = random.choice(g["alive"])
        await safe_send(
            g["bomb_holder"],
            f"💣 <b>The bomb passed to YOU!</b> Use /pass now!\n\n" + POWERED_BY,
        )
    else:
        await safe_send(
            chat_id,
            f"😅 The bomb didn't explode this round — keep passing!\n"
            f"💥 Use /pass now!\n\n" + POWERED_BY,
        )
    g["round"] += 1
    _schedule_bomb_timer(msg, chat_id)


# ═══════════════════════════════════════════════════════════════════════════════
#  /pass
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("pass") & filters.group)
async def pass_bomb(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in bomb_games or bomb_games[chat_id]["phase"] != "playing":
        await msg.reply("❌ No bomb game running!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = bomb_games[chat_id]
    uid = msg.from_user.id
    if uid != g["bomb_holder"]:
        await msg.reply("❌ You don't have the bomb!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    others = [p for p in g["alive"] if p != uid]
    if not others:
        await msg.reply("❌ No one else to pass to!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    new_holder = random.choice(others)
    g["bomb_holder"] = new_holder
    g["passed"] = True

    # Cancel old timer — a new one will be scheduled after explosion check
    if g.get("timer_task") and not g["timer_task"].done():
        g["timer_task"].cancel()

    try:
        await app.send_message(
            new_holder,
            f"💣 <b>YOU NOW HAVE THE BOMB!</b> Use /pass quickly!\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await msg.reply(
        f"✅ <b>{msg.from_user.first_name}</b> passed the bomb!\n"
        f"💣 Bomb is now with... someone 👀\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(2)
    await _maybe_explode(msg, chat_id)


async def _end_bomb_game(msg, chat_id: int):
    g = bomb_games[chat_id]
    winner = g["alive"][0] if g["alive"] else g["bomb_holder"]
    pot = g["pot"]
    await update_coins(winner, pot)
    await record_win(winner, "bomb_stats", pot)
    await msg.reply(
        f"<b>🎉 Bomb Game Over!</b>\n\n"
        f"🏆 Winner: <b>{g['players'][winner]}</b>\n"
        f"💰 Prize: <code>{pot:,}</code> coins\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )
    del bomb_games[chat_id]


# ═══════════════════════════════════════════════════════════════════════════════
#  /bombcancel  (admin)
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("bombcancel") & filters.group)
async def bomb_cancel(_, msg: Message):
    chat_id = msg.chat.id
    uid = msg.from_user.id
    member = await app.get_chat_member(chat_id, uid)
    is_admin = member.status in ("administrator", "creator")

    if chat_id not in bomb_games:
        await msg.reply("❌ No bomb game running!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    if not is_admin and uid != bomb_games[chat_id]["host"]:
        await msg.reply("❌ Only admins or the host can cancel!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = bomb_games[chat_id]
    for pid in g["players"]:
        await update_coins(pid, g["entry_fee"])
    del bomb_games[chat_id]
    await msg.reply(
        f"<b>❌ Bomb game cancelled by admin.</b>\n"
        f"💸 Entry fees refunded to all players.\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  /rank  /leaders
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("rank"))
async def bomb_rank(_, msg: Message):
    target = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
    user = await get_or_create_user(target.id, target.username or "", target.first_name or "")
    rank = await get_user_rank(target.id)
    await msg.reply(
        f"<b>📊 Rank — {target.first_name}</b>\n\n"
        f"🪙 Coins: <code>{user['coins']:,}</code>\n"
        f"🏆 Wins: <code>{user['wins']}</code>\n"
        f"💔 Losses: <code>{user['losses']}</code>\n"
        f"📊 Global Rank: <b>#{rank}</b>\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


@app.on_message(filters.command("leaders"))
async def bomb_leaders(_, msg: Message):
    lb = await get_bomb_leaderboard(10)
    if not lb:
        await msg.reply("No bomb stats yet. Play /bomb to get started!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7
    lines = []
    for i, u in enumerate(lb):
        n = u["first_name"] or u["username"] or "Unknown"
        lines.append(f"{medals[i]} <b>{n}</b> — {u['wins']}W / {u['losses']}L — <code>{u['coins_won']:,}</code> coins")
    await msg.reply(
        "<b>💣 Bomb Game Leaderboard</b>\n\n" + "\n".join(lines) + f"\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )

"""
MadaraDefaultr – Password Hacking Mini-Game
Powered by Madara

Rules:
 • Host: /hack <reward_amount> <digit_length(3-6)> — sets hidden password
 • Players: /register <amount> coins — join and pay entry
 • Anyone: /guess <number> — make a guess (after registering)
   Response: HACKS = correct digit + position, GLITCHES = correct digit wrong position
 • First to guess correctly wins the pot
 • Only host can /end the game
"""

import random
from collections import Counter

import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from database import (
    get_or_create_user, get_balance, update_coins, record_win, record_loss
)
from utils.buttons import keyboard, primary_btn, success_btn, danger_btn, btn
from config import POWERED_BY, pe


hack_games: dict[int, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════════
#  /hack – host starts
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("hack") & filters.group)
async def start_hack(_, msg: Message):
    chat_id = msg.chat.id

    if chat_id in hack_games:
        await msg.reply(
            "⚠️ A hack game is already running! /end it first.\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    args = msg.command
    if len(args) < 3:
        await msg.reply(
            "Usage: <code>/hack &lt;reward_amount&gt; &lt;digit_length 3-6&gt;</code>\n"
            "Example: <code>/hack 5000 4</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    try:
        reward = int(args[1])
        length = int(args[2])
        assert reward > 0 and 3 <= length <= 6
    except (ValueError, AssertionError):
        await msg.reply(
            "❌ Invalid args. Reward must be > 0 and digit length between 3 and 6.\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    uid = msg.from_user.id
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    if user["coins"] < reward:
        await msg.reply(
            f"❌ You need <b>{reward:,}</b> coins to set the reward.\n"
            f"Balance: <code>{user['coins']:,}</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    password = "".join([str(random.randint(0, 9)) for _ in range(length)])
    await update_coins(uid, -reward)

    hack_games[chat_id] = {
        "host": uid,
        "host_name": msg.from_user.first_name or "Host",
        "password": password,
        "length": length,
        "reward": reward,
        "pot": reward,
        "players": {},    # uid → {name, paid}
        "guesses": [],    # list of (uid, name, guess, hacks, glitches)
        "phase": "waiting",
        "solved": False,
    }

    await msg.reply(
        f"<b>🔐 Hack Game Started!</b>\n\n"
        f"👤 Host: <b>{msg.from_user.first_name}</b>\n"
        f"🔒 Password Length: <b>{length} digits</b>\n"
        f"🏆 Reward: <code>{reward:,}</code> coins\n\n"
        f"To join: <code>/register &lt;amount&gt; coins</code>\n"
        f"To guess: <code>/guess &lt;{length}-digit number&gt;</code>\n\n"
        f"<b>Good luck, Baka! 😈</b>\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard(
            [primary_btn(f"🔐 /register to join", data="hack_howto")],
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  /register – join the hack game
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("register") & filters.group)
async def register_hack(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in hack_games:
        await msg.reply("❌ No hack game running. Start with /hack!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = hack_games[chat_id]
    uid = msg.from_user.id

    if uid == g["host"]:
        await msg.reply("❌ You're the host — you can't register!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return
    if uid in g["players"]:
        await msg.reply("⚠️ Already registered!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    args = msg.command
    if len(args) < 2:
        await msg.reply(
            "Usage: <code>/register &lt;amount&gt; coins</code>\n"
            "Example: <code>/register 1000 coins</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    try:
        amount = int(args[1])
        assert amount > 0
    except (ValueError, AssertionError):
        await msg.reply("❌ Invalid amount!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    if user["coins"] < amount:
        await msg.reply(
            f"❌ Need <b>{amount:,}</b> coins. Balance: <code>{user['coins']:,}</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -amount)
    g["players"][uid] = {"name": msg.from_user.first_name or "Player", "paid": amount}
    g["pot"] += amount

    await msg.reply(
        f"✅ <b>{msg.from_user.first_name}</b> registered!\n"
        f"💸 Paid: <code>{amount:,}</code> coins\n"
        f"🏆 Total Pot: <code>{g['pot']:,}</code> coins\n\n"
        f"Good luck, Baka believes in you! 🧠✨\n\n"
        f"Start guessing: <code>/guess {g['length'] * '?'}</code>\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  /guess
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("guess") & filters.group)
async def guess_hack(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in hack_games:
        await msg.reply("❌ No hack game running!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = hack_games[chat_id]
    if g["solved"]:
        await msg.reply("🎉 Game already solved!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    uid = msg.from_user.id
    if uid == g["host"]:
        await msg.reply(
            "❌ You're the host — you can't guess your own password!\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return
    if uid not in g["players"]:
        await msg.reply(
            f"❌ Register first with <code>/register &lt;amount&gt; coins</code>!\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    args = msg.command
    if len(args) < 2:
        await msg.reply(
            f"Usage: <code>/guess &lt;{g['length']}-digit number&gt;</code>\n"
            f"Example: <code>/guess {'1234'[:g['length']]}</code>\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    guess_str = args[1].strip()
    if not guess_str.isdigit() or len(guess_str) != g["length"]:
        await msg.reply(
            f"❌ Guess must be exactly <b>{g['length']} digits</b>!\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    password = g["password"]
    hacks, glitches = _score_guess(guess_str, password)

    name = msg.from_user.first_name or "Player"
    g["guesses"].append((uid, name, guess_str, hacks, glitches))

    if hacks == g["length"]:
        # WINNER!
        g["solved"] = True
        pot = g["pot"]
        await update_coins(uid, pot)
        if uid in g["players"]:
            await record_win(uid, "hack_stats", pot)
        for pid in g["players"]:
            if pid != uid:
                await record_loss(pid, "hack_stats")

        await msg.reply(
            f"<b>🎉 HACKED! {name} cracked the code!</b>\n\n"
            f"🔓 Password was: <code>{password}</code>\n"
            f"🏆 Winner: <b>{name}</b>\n"
            f"💰 Prize: <code>{pot:,}</code> coins\n\n"
            f"<b>BOOM! You hacked it! 🎊</b>\n\n"
            f"<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        del hack_games[chat_id]
        return

    reaction = _guess_reaction(hacks, glitches, len(g["guesses"]))
    await msg.reply(
        f"<b>🔐 Guess #{len(g['guesses'])} — {name}</b>\n\n"
        f"Your guess: <code>{guess_str}</code>\n"
        f"🟢 <b>HACKS: {hacks}</b> (right position)\n"
        f"🟡 <b>GLITCHES: {glitches}</b> (wrong position)\n\n"
        f"{reaction}\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


def _score_guess(guess: str, password: str) -> tuple[int, int]:
    hacks = sum(g == p for g, p in zip(guess, password))
    c_guess = Counter(guess)
    c_pass = Counter(password)
    total_matches = sum(min(c_guess[d], c_pass[d]) for d in c_guess)
    glitches = total_matches - hacks
    return hacks, glitches


def _guess_reaction(hacks: int, glitches: int, attempt: int) -> str:
    if hacks == 0 and glitches == 0:
        return "❌ No matches at all — try different digits!"
    if attempt <= 3:
        return "Keep going! You can do it! ✨"
    if hacks >= 3:
        return "🔥 So close! Almost there!"
    return "🧠 Use your hacks & glitches wisely!"


# ═══════════════════════════════════════════════════════════════════════════════
#  /end – host ends the game
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("end") & filters.group)
async def end_hack(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in hack_games:
        await msg.reply("❌ No hack game running!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    g = hack_games[chat_id]
    if msg.from_user.id != g["host"]:
        await msg.reply("❌ Only the host can end the game!\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    password = g["password"]
    guesses_count = len(g["guesses"])
    players_count = len(g["players"])

    # Refund 50% to all registered players
    refund = g["pot"] // 2 // max(players_count, 1) if players_count else 0
    for pid in g["players"]:
        await update_coins(pid, refund)

    del hack_games[chat_id]
    await msg.reply(
        f"<b>🔒 Hack Game Ended!</b>\n\n"
        f"👤 Host: <b>{g['host_name']}</b>\n"
        f"🔓 Password was: <code>{password}</code>\n"
        f"🎯 Total Guesses: {guesses_count}\n"
        f"💸 Partial refund ({refund:,} coins) sent to {players_count} players\n\n"
        f"Thanks for playing! 😈\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Callback – howto
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^hack_howto$"))
async def cb_hack_howto(_, cq):
    await cq.answer(
        "Use /register <amount> coins to join, then /guess <number> to crack the password! 🔐",
        show_alert=True
    )

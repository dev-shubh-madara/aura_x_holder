"""
MadaraDefaultr – Wordseek (Wordle-style) Game
/wordseek /ws   → 5-letter
/ws4            → 4-letter
/ws6            → 6-letter
/end            → end active game
"""

import random
import time
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import POWERED_BY, pe
from database import _get_db, update_coins
from data.words import (
    ANSWERS4, VALID4,
    ANSWERS5, VALID5,
    ANSWERS6, VALID6,
)

MAX_ATTEMPTS = 6

# Coin rewards per win (harder word = bigger bonus)
WIN_COINS = {4: 150, 5: 250, 6: 400}


# ══════════════════════════════════════════════════════════════════════════════
#  DB helpers
# ══════════════════════════════════════════════════════════════════════════════

async def _get_ws(chat_id: int) -> dict | None:
    return await _get_db().wordseek_games.find_one({"chat_id": chat_id}, {"_id": 0})


async def _save_ws(game: dict):
    await _get_db().wordseek_games.update_one(
        {"chat_id": game['chat_id']}, {"$set": game}, upsert=True,
    )


async def _del_ws(chat_id: int):
    await _get_db().wordseek_games.delete_one({"chat_id": chat_id})


# ══════════════════════════════════════════════════════════════════════════════
#  Game logic
# ══════════════════════════════════════════════════════════════════════════════

def evaluate(guess: str, answer: str) -> list:
    """Return Wordle-style result list for one guess."""
    n      = len(answer)
    result = ['⬛'] * n
    pool   = list(answer)

    # Pass 1: exact matches
    for i in range(n):
        if guess[i] == answer[i]:
            result[i] = '🟩'
            pool[i]   = None

    # Pass 2: present but wrong position
    for i in range(n):
        if result[i] == '🟩':
            continue
        if guess[i] in pool:
            result[i] = '🟨'
            pool[pool.index(guess[i])] = None

    return result


def build_board(game: dict, show_answer: bool = False) -> str:
    length   = game['length']
    guesses  = game['guesses']
    results  = game['results']
    attempts = len(guesses)
    remain   = MAX_ATTEMPTS - attempts

    lines = [
        f"🔍 <b>ᴡᴏʀᴅsᴇᴇᴋ — {length}-ʟᴇᴛᴛᴇʀ ᴡᴏʀᴅ</b>",
        f"━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Played rows
    for g, r in zip(guesses, results):
        tiles = " ".join(r)
        chars = " ".join(f"<b>{ch.upper()}</b>" for ch in g)
        lines += [tiles, chars, ""]

    # Empty rows
    for _ in range(remain):
        lines.append("⬛ " * length)

    lines.append("")
    if show_answer:
        lines.append(f"📝 ᴀᴛᴛᴇᴍᴘᴛs: {attempts}/{MAX_ATTEMPTS}")
    elif attempts == 0:
        lines.append(f"📝 ᴛʏᴘᴇ ᴀ {length}-ʟᴇᴛᴛᴇʀ ᴡᴏʀᴅ ɪɴ ᴄʜᴀᴛ!")
    else:
        lines.append(f"📝 {attempts}/{MAX_ATTEMPTS} — ᴋᴇᴇᴘ ɢᴜᴇssɪɴɢ!")

    lines.append(f"\n<i>{POWERED_BY}</i>")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  Start helpers
# ══════════════════════════════════════════════════════════════════════════════

async def _start(msg: Message, length: int):
    existing = await _get_ws(msg.chat.id)
    if existing:
        return await msg.reply(
            f"🔍 ᴀ ɢᴀᴍᴇ ɪs ᴀʟʀᴇᴀᴅʏ ɢᴏɪɴɢ! ᴜsᴇ /end ᴛᴏ sᴛᴏᴘ ɪᴛ.",
            parse_mode=ParseMode.HTML,
        )

    pool   = {4: ANSWERS4, 5: ANSWERS5, 6: ANSWERS6}[length]
    answer = random.choice(list(pool))

    game = {
        "chat_id":    msg.chat.id,
        "answer":     answer,
        "length":     length,
        "guesses":    [],
        "results":    [],
        "solved":     False,
        "started_by": msg.from_user.id,
        "started_at": time.time(),
        "game_msg_id": 0,
    }
    await _save_ws(game)
    sent = await msg.reply(build_board(game), parse_mode=ParseMode.HTML)
    game['game_msg_id'] = sent.id
    await _save_ws(game)


# ══════════════════════════════════════════════════════════════════════════════
#  Commands
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command(["wordseek", "ws"]) & filters.group)
async def cmd_ws5(_, msg: Message):
    await _start(msg, 5)


@app.on_message(filters.command("ws4") & filters.group)
async def cmd_ws4(_, msg: Message):
    await _start(msg, 4)


@app.on_message(filters.command("ws6") & filters.group)
async def cmd_ws6(_, msg: Message):
    await _start(msg, 6)


@app.on_message(filters.command("end") & filters.group)
async def cmd_end_ws(_, msg: Message):
    game = await _get_ws(msg.chat.id)
    if not game:
        return  # no wordseek game; let other /end handlers (hack, etc.) proceed

    is_admin = False
    try:
        m = await app.get_chat_member(msg.chat.id, msg.from_user.id)
        if m.status.value in ("creator", "administrator"):
            is_admin = True
    except Exception:
        pass

    if msg.from_user.id != game['started_by'] and not is_admin:
        return await msg.reply(
            "❌ ᴏɴʟʏ ᴛʜᴇ sᴛᴀʀᴛᴇʀ ᴏʀ ᴀᴅᴍɪɴ ᴄᴀɴ ᴇɴᴅ.", parse_mode=ParseMode.HTML
        )
    answer = game['answer']
    await _del_ws(msg.chat.id)
    await msg.reply(
        f"🔍 <b>ᴡᴏʀᴅsᴇᴇᴋ ᴇɴᴅᴇᴅ!</b>\n\n"
        f"ᴛʜᴇ ᴀɴsᴡᴇʀ ᴡᴀs: <b>{answer.upper()}</b>\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Guess handler — catches plain text messages in groups
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.group & filters.text & ~filters.command([
    "start","help","ping","bal","daily","claim","give","shop","inventory",
    "top","rank","propose","marry","divorce","couple","kill","rob","protect",
    "revive","status","card","bet","flip","bomb","join","pass","bombcancel",
    "hack","register","guess","end","wordseek","ws","ws4","ws6","uno","enduno",
    "uno_end","ban","unban","mute","unmute","pin","welcome","staff","bots",
    "stats","zombies","leaders",
]))
async def handle_guess(_, msg: Message):
    game = await _get_ws(msg.chat.id)
    if not game:
        return

    text   = msg.text.strip().lower()
    length = game['length']

    if len(text) != length or not text.isalpha():
        return  # wrong length or not pure letters — ignore

    # Validate against word list
    valid_set = {4: VALID4, 5: VALID5, 6: VALID6}[length]
    if text not in valid_set:
        return await msg.reply(
            f"❓ <b>{text.upper()}</b> ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ᴡᴏʀᴅ ʟɪsᴛ!",
            parse_mode=ParseMode.HTML,
        )

    result = evaluate(text, game['answer'])
    game['guesses'].append(text)
    game['results'].append(result)

    # ── Solved ────────────────────────────────────────────────────────────────
    if all(r == '🟩' for r in result):
        game['solved'] = True
        await _del_ws(msg.chat.id)
        guesser  = msg.from_user.first_name or "ᴘʟᴀʏᴇʀ"
        attempts = len(game['guesses'])
        bonus    = WIN_COINS.get(length, 250)
        board    = build_board(game, show_answer=True)
        await msg.reply(
            f"{board}\n\n"
            f"🏆 <b>{guesser} sᴏʟᴠᴇᴅ ɪᴛ ɪɴ {attempts} "
            f"ᴀᴛᴛᴇᴍᴘᴛ{'s' if attempts != 1 else ''}!</b>\n"
            f"ᴡᴏʀᴅ: <b>{game['answer'].upper()}</b>\n"
            f"{pe('coin','🪙')} +{bonus} ᴄᴏɪɴs!\n\n"
            f"<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML,
        )
        await update_coins(msg.from_user.id, bonus)
        return

    # ── Out of attempts ───────────────────────────────────────────────────────
    if len(game['guesses']) >= MAX_ATTEMPTS:
        await _del_ws(msg.chat.id)
        board = build_board(game, show_answer=True)
        await msg.reply(
            f"{board}\n\n"
            f"💀 <b>ɢᴀᴍᴇ ᴏᴠᴇʀ!</b> ɴᴏʙᴏᴅʏ ɢᴏᴛ ɪᴛ.\n"
            f"ᴛʜᴇ ᴡᴏʀᴅ ᴡᴀs: <b>{game['answer'].upper()}</b>\n\n"
            f"<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Continue ──────────────────────────────────────────────────────────────
    await _save_ws(game)
    await msg.reply(build_board(game), parse_mode=ParseMode.HTML)

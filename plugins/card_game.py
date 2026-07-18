"""
MadaraDefaultr – Card Flip Game
Powered by Madara

Rules:
 • Each player gets 4 hidden cards A,B,C,D (same total sum for all).
 • 4 rounds – each round every player picks one card to flip.
 • Highest card wins the round.
 • Player with highest total round-wins (tie → coins) wins the pot.
 • 60-second turn timer; auto-play if missed.
"""

import asyncio
import random
from collections import defaultdict

import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery
from utils.safe_send import safe_reply, safe_send
from database import (
    get_or_create_user, get_balance, update_coins, record_win, record_loss
)
from utils.buttons import keyboard, primary_btn, success_btn, danger_btn, btn, flip_keyboard
from config import POWERED_BY, CARD_TURN_TIMEOUT, pe


# ── Active games: chat_id → game state dict ─────────────────────────────────
card_games: dict[int, dict] = {}


def _gen_cards(n_players: int) -> list[list[int]]:
    """
    Generate balanced card hands: each hand sums to the same value.
    Cards are integers 1-9.
    """
    hands = []
    for _ in range(n_players):
        while True:
            hand = sorted([random.randint(1, 9) for _ in range(4)], reverse=True)
            if not hands or sum(hand) == sum(hands[0]):
                break
            # Force same sum by adjustment
            target = sum(hands[0])
            hand = _make_sum(target)
            break
        hands.append(hand)
    return hands


def _make_sum(target: int) -> list[int]:
    """Return 4 random cards (1-9) that sum to target."""
    for _ in range(1000):
        cards = [random.randint(1, 9) for _ in range(3)]
        last = target - sum(cards)
        if 1 <= last <= 9:
            result = sorted(cards + [last], reverse=True)
            return result
    # Fallback
    return [target // 4 + (1 if i < target % 4 else 0) for i in range(4)]


# ═══════════════════════════════════════════════════════════════════════════════
#  /card – host starts the game
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("card") & filters.group)
async def start_card_game(_, msg: Message):
    chat_id = msg.chat.id

    if chat_id in card_games:
        g = card_games[chat_id]
        if g["phase"] == "waiting":
            await msg.reply(
                "⚠️ A card game is already waiting for players.\n"
                f"Use <b>/bet &lt;amount&gt;</b> to join!\n\n<i>{POWERED_BY}</i>",
                parse_mode=ParseMode.HTML
            )
            return

    user = await get_or_create_user(msg.from_user.id,
                                    msg.from_user.username or "",
                                    msg.from_user.first_name or "")
    entry_fee = 100  # default entry fee when hosting without /bet
    if user["coins"] < entry_fee:
        await msg.reply(
            f"❌ You need at least <b>{entry_fee:,}</b> coins to start.\n"
            f"Your balance: <code>{user['coins']:,}</code>\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        return

    card_games[chat_id] = {
        "phase": "waiting",
        "host": msg.from_user.id,
        "players": {msg.from_user.id: {"name": msg.from_user.first_name or "Player",
                                        "bet": entry_fee}},
        "pot": entry_fee,
        "entry_fee": entry_fee,
        "hands": {},
        "round": 0,
        "scores": defaultdict(int),
        "used_cards": defaultdict(set),
        "round_choices": {},
        "timer_task": None,
    }
    await update_coins(msg.from_user.id, -entry_fee)

    txt = (
        f"<b>🃏 Card Game Started!</b>\n\n"
        f"👤 Host: <b>{msg.from_user.first_name}</b>\n"
        f"💰 Entry Fee: <code>{entry_fee:,}</code> coins\n"
        f"🏆 Pot: <code>{entry_fee:,}</code> coins\n\n"
        f"Use <b>/bet {entry_fee}</b> to join!\n"
        f"Game starts when 2+ players join.\n\n"
        f"<i>{POWERED_BY}</i>"
    )
    kb = keyboard(
        [success_btn(f"✅ Join (pay {entry_fee} coins)", data=f"card_join_{chat_id}")],
        [danger_btn("❌ Cancel", data=f"card_cancel_{chat_id}")],
    )
    await msg.reply(txt, reply_markup=kb, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  /bet – join the waiting game
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("bet") & filters.group)
async def bet_card_game(_, msg: Message):
    chat_id = msg.chat.id
    if chat_id not in card_games or card_games[chat_id]["phase"] != "waiting":
        await msg.reply(
            "❌ No card game is waiting right now. Use /card to start one!\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    g = card_games[chat_id]
    uid = msg.from_user.id

    if uid in g["players"]:
        await msg.reply("⚠️ You already joined this game!", parse_mode=ParseMode.HTML)
        return

    fee = g["entry_fee"]
    user = await get_or_create_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    if user["coins"] < fee:
        await msg.reply(
            f"❌ You need <b>{fee:,}</b> coins to join. Balance: <code>{user['coins']:,}</code>\n\n"
            f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML
        )
        return

    await update_coins(uid, -fee)
    g["players"][uid] = {"name": msg.from_user.first_name or "Player", "bet": fee}
    g["pot"] += fee

    player_list = "\n".join(f"• {p['name']}" for p in g["players"].values())
    txt = (
        f"<b>✅ {msg.from_user.first_name} joined the card game!</b>\n\n"
        f"👥 Players ({len(g['players'])}):\n{player_list}\n"
        f"🏆 Pot: <code>{g['pot']:,}</code> coins\n\n"
    )

    if len(g["players"]) >= 2:
        txt += "🚀 <b>Game starting in 10 seconds…</b>\n"
        await msg.reply(txt + f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(10)
        await _start_card_rounds(msg, chat_id)
    else:
        txt += f"⏳ Waiting for more players. Use /bet {fee} to join!\n\n<i>{POWERED_BY}</i>"
        await msg.reply(txt, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  Callback – inline join button
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex(r"^card_join_(-?\d+)$"))
async def cb_card_join(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    if chat_id not in card_games or card_games[chat_id]["phase"] != "waiting":
        await cq.answer("Game already started or cancelled!", show_alert=True)
        return

    g = card_games[chat_id]
    uid = cq.from_user.id
    if uid in g["players"]:
        await cq.answer("You already joined!", show_alert=True)
        return

    fee = g["entry_fee"]
    user = await get_or_create_user(uid, cq.from_user.username or "", cq.from_user.first_name or "")
    if user["coins"] < fee:
        await cq.answer(f"Not enough coins! Need {fee:,}.", show_alert=True)
        return

    await update_coins(uid, -fee)
    g["players"][uid] = {"name": cq.from_user.first_name or "Player", "bet": fee}
    g["pot"] += fee
    await cq.answer("✅ You joined!")

    if len(g["players"]) >= 2:
        await cq.message.reply(
            f"<b>🚀 Enough players! Starting card game in 10 seconds…</b>\n\n<i>{POWERED_BY}</i>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(10)
        await _start_card_rounds(cq.message, chat_id)


@app.on_callback_query(filters.regex(r"^card_cancel_(-?\d+)$"))
async def cb_card_cancel(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    if chat_id not in card_games:
        await cq.answer("No game found.", show_alert=True)
        return
    g = card_games[chat_id]
    if cq.from_user.id != g["host"]:
        await cq.answer("Only the host can cancel!", show_alert=True)
        return
    for uid, p in g["players"].items():
        await update_coins(uid, p["bet"])
    del card_games[chat_id]
    await cq.edit_message_text(
        f"<b>❌ Card game cancelled. Entry fees refunded.</b>\n\n<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Internal – start rounds
# ═══════════════════════════════════════════════════════════════════════════════

async def _start_card_rounds(msg, chat_id: int):
    if chat_id not in card_games:
        return
    g = card_games[chat_id]
    # Race-condition guard: only the first caller transitions to "playing"
    if g["phase"] != "waiting":
        return
    g["phase"] = "playing"
    n = len(g["players"])
    hands = _gen_hands_equal_sum(n)
    for i, uid in enumerate(g["players"]):
        g["hands"][uid] = hands[i]
        g["used_cards"][uid] = set()
        g["scores"][uid] = 0

    player_list = "\n".join(f"• {p['name']}" for p in g["players"].values())
    await msg.reply(
        f"<b>🃏 Card Game — Round 1 Starting!</b>\n\n"
        f"👥 Players:\n{player_list}\n"
        f"🏆 Pot: <code>{g['pot']:,}</code> coins\n\n"
        f"Each player has cards <b>A, B, C, D</b> (hidden values).\n"
        f"Cards sum is equal for all players — only strategy wins!\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(2)
    await _run_round(msg, chat_id)


def _gen_hands_equal_sum(n: int) -> list[list[int]]:
    """Generate n hands with equal sum."""
    target = None
    hands = []
    for _ in range(n):
        while True:
            h = sorted([random.randint(1, 9) for _ in range(4)], reverse=True)
            if target is None:
                target = sum(h)
                hands.append(h)
                break
            elif sum(h) == target:
                hands.append(h)
                break
            else:
                h = _make_sum(target)
                hands.append(h)
                break
    return hands


async def _run_round(msg, chat_id: int):
    if chat_id not in card_games:
        return
    g = card_games[chat_id]
    g["round"] += 1
    g["round_choices"] = {}

    if g["round"] > 4:
        await _end_card_game(msg, chat_id)
        return

    # Cancel any leftover timer from a previous round
    if g.get("timer_task") and not g["timer_task"].done():
        g["timer_task"].cancel()

    # Unique token for this round – guards against stale timer callbacks
    round_token = g["round"]

    labels = ["a", "b", "c", "d"]
    for uid, p in g["players"].items():
        used = g["used_cards"][uid]
        available = [c for c in labels if c not in used]
        hand = g["hands"][uid]
        card_display = {lbl: hand[i] for i, lbl in enumerate(labels)}
        try:
            await app.send_message(
                uid,
                f"<b>🃏 Round {g['round']}/4 — Your Cards</b>\n\n"
                + "\n".join(
                    f"{'✅' if lbl not in used else '❌'} Card {lbl.upper()}: "
                    f"<b>{card_display[lbl]}</b>{'  ← used' if lbl in used else ''}"
                    for lbl in labels
                ) +
                f"\n\n⚡ You have <b>{CARD_TURN_TIMEOUT}s</b> to /flip a card!\n"
                f"Use: <code>/flip {available[0]}</code>\n\n<i>{POWERED_BY}</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=flip_keyboard(available)
            )
        except Exception:
            pass

    txt = (
        f"<b>🃏 Round {g['round']}/4</b>\n\n"
        f"Check your DM for your card values.\n"
        f"Use /flip a / b / c / d in the group!\n"
        f"⏱ {CARD_TURN_TIMEOUT} seconds to choose…\n\n"
        f"<i>{POWERED_BY}</i>"
    )
    await safe_reply(msg, txt)

    # Schedule auto-play timer as a cancellable Task
    async def _timer():
        await asyncio.sleep(CARD_TURN_TIMEOUT)
        # Guard: only fire if we're still on the same round
        if chat_id not in card_games:
            return
        if card_games[chat_id].get("round") != round_token:
            return
        await _auto_flip(msg, chat_id)

    g["timer_task"] = asyncio.create_task(_timer())


async def _auto_flip(msg, chat_id: int):
    g = card_games[chat_id]
    labels = ["a", "b", "c", "d"]
    auto_played = []
    for uid, p in g["players"].items():
        if uid not in g["round_choices"]:
            used = g["used_cards"][uid]
            available = [c for c in labels if c not in used]
            if available:
                choice = random.choice(available)
                g["round_choices"][uid] = choice
                g["used_cards"][uid].add(choice)
                auto_played.append(p["name"])

    if auto_played:
        await safe_send(
            msg.chat.id,
            f"⏱ <b>Time's up!</b> Auto-played for: {', '.join(auto_played)}\n\n"
            f"<i>{POWERED_BY}</i>",
        )
    await _resolve_round(msg, chat_id)


# ═══════════════════════════════════════════════════════════════════════════════
#  /flip
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("flip") & filters.group)
async def flip_card(_, msg: Message):
    chat_id = msg.chat.id
    uid = msg.from_user.id

    if chat_id not in card_games or card_games[chat_id]["phase"] != "playing":
        await msg.reply("❌ No active card game. Start one with /card!\n\n" + POWERED_BY)
        return

    g = card_games[chat_id]
    if uid not in g["players"]:
        await msg.reply("❌ You're not in this game!", parse_mode=ParseMode.HTML)
        return
    if uid in g["round_choices"]:
        await msg.reply("⚠️ You already flipped a card this round!", parse_mode=ParseMode.HTML)
        return

    args = msg.command
    if len(args) < 2 or args[1].lower() not in ["a", "b", "c", "d"]:
        await msg.reply("Usage: <code>/flip a</code> or b/c/d\n\n" + POWERED_BY, parse_mode=ParseMode.HTML)
        return

    choice = args[1].lower()
    used = g["used_cards"][uid]
    if choice in used:
        labels = ["a", "b", "c", "d"]
        available = [c for c in labels if c not in used]
        await msg.reply(
            f"❌ Card <b>{choice.upper()}</b> is already used!\n"
            f"Available: {', '.join(c.upper() for c in available)}\n\n" + POWERED_BY,
            parse_mode=ParseMode.HTML
        )
        return

    g["round_choices"][uid] = choice
    g["used_cards"][uid].add(choice)
    await msg.reply(
        f"✅ <b>{msg.from_user.first_name}</b> flipped Card <b>{choice.upper()}</b>!\n\n"
        f"<i>{POWERED_BY}</i>",
        parse_mode=ParseMode.HTML
    )

    if len(g["round_choices"]) == len(g["players"]):
        await _resolve_round(msg, chat_id)


async def _resolve_round(msg, chat_id: int):
    g = card_games[chat_id]
    labels = ["a", "b", "c", "d"]
    label_index = {"a": 0, "b": 1, "c": 2, "d": 3}
    results = {}
    for uid, choice in g["round_choices"].items():
        hand = g["hands"][uid]
        val = hand[label_index[choice]]
        results[uid] = (choice, val)

    max_val = max(v for _, v in results.values())
    winners = [uid for uid, (_, v) in results.items() if v == max_val]

    for uid in winners:
        g["scores"][uid] += 1

    lines = []
    for uid, (c, v) in results.items():
        name = g["players"][uid]["name"]
        is_win = uid in winners
        lines.append(f"{'🏆 ' if is_win else '  '}{name}: Card {c.upper()} → <b>{v}</b>")

    win_names = " & ".join(g["players"][uid]["name"] for uid in winners)
    txt = (
        f"<b>🃏 Round {g['round']} Results</b>\n\n"
        + "\n".join(lines)
        + f"\n\n🥇 Round Winner: <b>{win_names}</b> (value: {max_val})\n\n"
        f"<b>Score Board:</b>\n"
        + "\n".join(f"• {g['players'][uid]['name']}: {g['scores'][uid]} pts"
                    for uid in g["players"])
        + f"\n\n<i>{POWERED_BY}</i>"
    )
    await msg.reply(txt, parse_mode=ParseMode.HTML)

    await asyncio.sleep(3)
    await _run_round(msg, chat_id)


async def _end_card_game(msg, chat_id: int):
    g = card_games[chat_id]
    max_score = max(g["scores"].values())
    winners = [uid for uid, s in g["scores"].items() if s == max_score]
    winner_id = random.choice(winners)  # tie-break
    pot = g["pot"]
    per_winner = pot // len(winners)

    for uid in winners:
        await update_coins(uid, per_winner)
        await record_win(uid, "card_stats", per_winner)
    for uid in g["players"]:
        if uid not in winners:
            await record_loss(uid, "card_stats")

    score_board = "\n".join(
        f"{'🏆 ' if uid in winners else '  '}{g['players'][uid]['name']}: {g['scores'][uid]} pts"
        for uid in sorted(g["players"], key=lambda u: g["scores"][u], reverse=True)
    )
    win_names = " & ".join(g["players"][uid]["name"] for uid in winners)

    txt = (
        f"<b>🎉 Card Game Over!</b>\n\n"
        f"<b>Final Scores:</b>\n{score_board}\n\n"
        f"🏆 <b>Winner: {win_names}!</b>\n"
        f"💰 Prize: <code>{per_winner:,}</code> coins each\n\n"
        f"<i>{POWERED_BY}</i>"
    )
    await msg.reply(txt, parse_mode=ParseMode.HTML)
    del card_games[chat_id]

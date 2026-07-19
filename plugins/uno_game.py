"""
MadaraDefaultr – UNO Card Game
Full group UNO with inline button UI & premium emoji
"""

import random
import time
import MadaraDefaultr as app
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import POWERED_BY, pe
from database import (
    get_uno_game as _get_game_db,
    save_uno_game as _save_game_db,
    delete_uno_game as _del_game_db,
    update_coins, record_win, record_loss,
)

# ══════════════════════════════════════════════════════════════════════════════
#  Card constants
# ══════════════════════════════════════════════════════════════════════════════

COLORS      = ['r', 'b', 'g', 'y']
COLOR_EMOJI = {'r': '🔴', 'b': '🔵', 'g': '🟢', 'y': '🟡'}
COLOR_NAME  = {'r': 'ʀᴇᴅ', 'b': 'ʙʟᴜᴇ', 'g': 'ɢʀᴇᴇɴ', 'y': 'ʏᴇʟʟᴏᴡ'}
VAL_DISPLAY = {'s': '⊘', 'r': '↩', 'd': '+2'}

UNO_WIN_BONUS = 500   # coins awarded to winner

# ══════════════════════════════════════════════════════════════════════════════
#  Deck helpers
# ══════════════════════════════════════════════════════════════════════════════

def create_deck() -> list:
    """Create a standard 108-card UNO deck."""
    deck = []
    for c in COLORS:
        deck.append(f"{c}0")                               # one 0
        for v in ['1','2','3','4','5','6','7','8','9','s','r','d']:
            deck.extend([f"{c}{v}", f"{c}{v}"])            # two of each
    deck.extend(['w'] * 4)                                 # 4 wilds
    deck.extend(['wd'] * 4)                                # 4 wild-draw-4
    return deck   # total: 108


def card_display(card: str) -> str:
    """Human-readable card label, e.g. '🔴 5', '🌈 +4'."""
    if card == 'w':  return '🌈 ᴡɪʟᴅ'
    if card == 'wd': return '🌈 +4'
    c, v = card[0], card[1:]
    return f"{COLOR_EMOJI.get(c,'?')}{VAL_DISPLAY.get(v, v)}"


def can_play(card: str, top_card: str, current_color: str) -> bool:
    if card in ('w', 'wd'): return True
    cc, cv = card[0], card[1:]
    if cc == current_color: return True
    if top_card not in ('w', 'wd') and cv == top_card[1:]: return True
    return False


def draw_into_hand(game: dict, uid_str: str, count: int):
    """Draw cards from deck into a player's hand; reshuffles discard if needed."""
    for _ in range(count):
        if not game['deck']:
            if len(game['discard']) > 1:
                top = game['discard'][-1]
                game['deck'] = game['discard'][:-1]
                random.shuffle(game['deck'])
                game['discard'] = [top]
        if game['deck']:
            game['hands'][uid_str].append(game['deck'].pop())


def apply_effect(game: dict, card: str, chosen_color: str = None):
    """Apply a card's effect and advance the turn pointer. Modifies game in place."""
    players = game['players']
    idx, d, n = game['current_idx'], game['direction'], len(players)

    # Set current color
    if card in ('w', 'wd'):
        game['current_color'] = chosen_color or 'r'
    else:
        game['current_color'] = card[0]

    cv = '' if card in ('w', 'wd') else card[1:]

    if cv == 's':                                   # skip
        game['current_idx'] = (idx + 2 * d) % n
    elif cv == 'r':                                 # reverse
        game['direction'] = -d
        game['current_idx'] = idx if n == 2 else (idx + game['direction']) % n
    elif cv == 'd':                                 # +2
        victim_idx = (idx + d) % n
        draw_into_hand(game, str(players[victim_idx]), 2)
        game['current_idx'] = (victim_idx + d) % n
    elif card == 'wd':                              # wild +4
        victim_idx = (idx + d) % n
        draw_into_hand(game, str(players[victim_idx]), 4)
        game['current_idx'] = (victim_idx + d) % n
    else:                                           # number / wild
        game['current_idx'] = (idx + d) % n


# ══════════════════════════════════════════════════════════════════════════════
#  UI builders
# ══════════════════════════════════════════════════════════════════════════════

def game_text(game: dict) -> str:
    players   = game['players']
    names     = game['names']
    cur_idx   = game['current_idx']
    top       = card_display(game['top_card'])
    cc        = game['current_color']
    dir_arrow = "↗️ ᴄʟᴋᴡɪsᴇ" if game['direction'] == 1 else "↙️ ᴀɴᴛɪ"

    rows = []
    for i, pid in enumerate(players):
        nm = names.get(str(pid), f"ᴘ{i+1}")
        nc = len(game['hands'].get(str(pid), []))
        tag = " ◀ ᴛᴜʀɴ" if i == cur_idx else ""
        ico = "🎯" if i == cur_idx else "👤"
        uno = " ‼️" if nc == 1 else ""
        rows.append(f"  {ico} <b>{nm}</b> — {nc}🃏{uno}{tag}")

    cur_name = names.get(str(players[cur_idx]), "ᴘʟᴀʏᴇʀ")
    return (
        f"🎴 <b>ᴜɴᴏ ɢᴀᴍᴇ!</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"<b>ᴘʟᴀʏᴇʀs:</b>\n" + "\n".join(rows) + "\n\n"
        f"🃏 <b>ᴛᴏᴘ ᴄᴀʀᴅ:</b>  {top}\n"
        f"{COLOR_EMOJI.get(cc,'🌈')} <b>ᴄᴏʟᴏʀ:</b>  {COLOR_NAME.get(cc,'?')}\n"
        f"{dir_arrow}\n\n"
        f"🎯 <b>{cur_name}'s ᴛᴜʀɴ!</b>\n\n"
        f"<i>{POWERED_BY}</i>"
    )


def game_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🃏 ᴍʏ ʜᴀɴᴅ",   callback_data="uno_hand"),
            InlineKeyboardButton("🎴 ᴅʀᴀᴡ",       callback_data="uno_draw"),
        ],
        [InlineKeyboardButton("🏳️ ᴇɴᴅ ɢᴀᴍᴇ",    callback_data="uno_quit")],
    ])


def hand_kb(hand: list, top_card: str, cur_color: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for card in hand:
        label = card_display(card)
        row.append(InlineKeyboardButton(label, callback_data=f"uno_play_{card}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("↩️ ᴄʟᴏsᴇ", callback_data="uno_back")])
    return InlineKeyboardMarkup(rows)


def color_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔴 ʀᴇᴅ",    callback_data="uno_color_r"),
            InlineKeyboardButton("🔵 ʙʟᴜᴇ",   callback_data="uno_color_b"),
        ],
        [
            InlineKeyboardButton("🟢 ɢʀᴇᴇɴ",  callback_data="uno_color_g"),
            InlineKeyboardButton("🟡 ʏᴇʟʟᴏᴡ", callback_data="uno_color_y"),
        ],
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  Database helpers (SQLite-backed)
# ══════════════════════════════════════════════════════════════════════════════

async def _get_game(chat_id: int) -> dict | None:
    return await _get_game_db(chat_id)


async def _save_game(game: dict):
    await _save_game_db(game)


async def _del_game(chat_id: int):
    await _del_game_db(chat_id)


async def _update_game_msg(chat_id: int, msg_id: int, game: dict):
    """Edit the persistent game board message."""
    try:
        await app.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=game_text(game), reply_markup=game_kb(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  /uno  – start lobby
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command("uno") & filters.group)
async def cmd_uno(_, msg: Message):
    existing = await _get_game(msg.chat.id)
    if existing:
        await msg.reply(
            f"🎴 ᴀ ɢᴀᴍᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴄᴛɪᴠᴇ! ᴜsᴇ /enduno ᴛᴏ ᴄᴀɴᴄᴇʟ ɪᴛ.",
            parse_mode=ParseMode.HTML,
        )
        return

    uid  = msg.from_user.id
    name = msg.from_user.first_name or "ʜᴏsᴛ"

    game = {
        "chat_id": msg.chat.id, "state": "waiting",
        "host_id": uid, "players": [uid],
        "names": {str(uid): name}, "hands": {},
        "deck": [], "discard": [], "top_card": "",
        "current_color": "r", "current_idx": 0, "direction": 1,
        "lobby_msg_id": 0, "game_msg_id": 0,
        "pending_wild": None,
    }
    await _save_game(game)

    def lobby_kb(n): return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ᴊᴏɪɴ", callback_data="uno_join"),
         InlineKeyboardButton("▶️ sᴛᴀʀᴛ", callback_data="uno_start")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="uno_cancel")],
    ])

    text = (
        f"🎴 <b>ᴜɴᴏ ʟᴏʙʙʏ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>ʜᴏsᴛ:</b> {name}\n\n"
        f"<b>ᴘʟᴀʏᴇʀs (1/8):</b>\n  🎯 {name}\n\n"
        f"ᴍɪɴ 2 ᴘʟᴀʏᴇʀs · ᴍᴀx 8\n\n<i>{POWERED_BY}</i>"
    )
    sent = await msg.reply(text, reply_markup=lobby_kb(1), parse_mode=ParseMode.HTML)
    game['lobby_msg_id'] = sent.id
    await _save_game(game)


def _lobby_text(game: dict) -> str:
    n     = len(game['players'])
    names = game['names']
    plist = "\n".join(
        f"  {'🎯' if i == 0 else '👤'} {names[str(p)]}"
        for i, p in enumerate(game['players'])
    )
    return (
        f"🎴 <b>ᴜɴᴏ ʟᴏʙʙʏ</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>ʜᴏsᴛ:</b> {names[str(game['host_id'])]}\n\n"
        f"<b>ᴘʟᴀʏᴇʀs ({n}/8):</b>\n{plist}\n\n"
        f"ᴍɪɴ 2 ᴘʟᴀʏᴇʀs · ᴍᴀx 8\n\n<i>{POWERED_BY}</i>"
    )


_LOBBY_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ ᴊᴏɪɴ", callback_data="uno_join"),
     InlineKeyboardButton("▶️ sᴛᴀʀᴛ", callback_data="uno_start")],
    [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="uno_cancel")],
])


# ══════════════════════════════════════════════════════════════════════════════
#  Lobby callbacks
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^uno_join$"))
async def cb_join(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'waiting':
        return await cq.answer("ɴᴏ ᴏᴘᴇɴ ʟᴏʙʙʏ.", show_alert=True)
    uid  = cq.from_user.id
    name = cq.from_user.first_name or "ᴘʟᴀʏᴇʀ"
    if uid in game['players']:
        return await cq.answer("ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴊᴏɪɴᴇᴅ! ✅", show_alert=True)
    if len(game['players']) >= 8:
        return await cq.answer("ʟᴏʙʙʏ ɪs ғᴜʟʟ (8/8)!", show_alert=True)
    game['players'].append(uid)
    game['names'][str(uid)] = name
    await _save_game(game)
    await cq.edit_message_text(_lobby_text(game), reply_markup=_LOBBY_KB,
                                parse_mode=ParseMode.HTML)
    await cq.answer(f"✅ {name} ᴊᴏɪɴᴇᴅ!")


@app.on_callback_query(filters.regex("^uno_start$"))
async def cb_start(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'waiting':
        return await cq.answer("ɴᴏ ʟᴏʙʙʏ.", show_alert=True)
    if cq.from_user.id != game['host_id']:
        return await cq.answer("ᴏɴʟʏ ʜᴏsᴛ ᴄᴀɴ sᴛᴀʀᴛ!", show_alert=True)
    if len(game['players']) < 2:
        return await cq.answer("ɴᴇᴇᴅ ≥ 2 ᴘʟᴀʏᴇʀs!", show_alert=True)

    deck = create_deck()
    random.shuffle(deck)
    random.shuffle(game['players'])         # randomise turn order

    hands = {str(p): [deck.pop() for _ in range(7)] for p in game['players']}

    # First card: must be a plain number
    top_card = None
    while deck:
        c = deck.pop()
        if c not in ('w', 'wd') and c[1] not in ('s', 'r', 'd'):
            top_card = c; break
    if not top_card:
        top_card = 'r5'     # safety fallback

    game.update({
        "state": "playing", "deck": deck,
        "discard": [top_card], "hands": hands,
        "top_card": top_card, "current_color": top_card[0],
        "current_idx": 0, "direction": 1,
    })
    await _save_game(game)

    text = game_text(game)
    try:
        await cq.edit_message_text(text, reply_markup=game_kb(), parse_mode=ParseMode.HTML)
        game['game_msg_id'] = cq.message.id
    except Exception:
        sent = await cq.message.reply(text, reply_markup=game_kb(), parse_mode=ParseMode.HTML)
        game['game_msg_id'] = sent.id
    await _save_game(game)
    await cq.answer("🎴 ɢᴀᴍᴇ sᴛᴀʀᴛᴇᴅ!")


@app.on_callback_query(filters.regex("^uno_cancel$"))
async def cb_cancel(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game:
        return await cq.answer()
    if cq.from_user.id != game['host_id']:
        return await cq.answer("ᴏɴʟʏ ʜᴏsᴛ ᴄᴀɴ ᴄᴀɴᴄᴇʟ!", show_alert=True)
    await _del_game(cq.message.chat.id)
    await cq.edit_message_text("❌ ᴜɴᴏ ʟᴏʙʙʏ ᴄᴀɴᴄᴇʟʟᴇᴅ.", parse_mode=ParseMode.HTML)
    await cq.answer("❌ ᴄᴀɴᴄᴇʟʟᴇᴅ.")


# ══════════════════════════════════════════════════════════════════════════════
#  In-game callbacks
# ══════════════════════════════════════════════════════════════════════════════

@app.on_callback_query(filters.regex("^uno_hand$"))
async def cb_hand(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'playing':
        return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ.", show_alert=True)
    uid = cq.from_user.id
    if uid != game['players'][game['current_idx']]:
        return await cq.answer("⏳ ɴᴏᴛ ʏᴏᴜʀ ᴛᴜʀɴ!", show_alert=True)

    uid_str = str(uid)
    hand    = game['hands'].get(uid_str, [])
    name    = game['names'].get(uid_str, "ᴘʟᴀʏᴇʀ")
    top     = card_display(game['top_card'])
    cc      = game['current_color']

    text = (
        f"🃏 <b>ʏᴏᴜʀ ʜᴀɴᴅ — {name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🃏 ᴛᴏᴘ: {top}  {COLOR_EMOJI.get(cc,'🌈')} ᴄᴏʟ: {COLOR_NAME.get(cc,'?')}\n\n"
        f"ᴛᴀᴘ ᴀ ᴄᴀʀᴅ ᴛᴏ ᴘʟᴀʏ ɪᴛ!\n<i>{POWERED_BY}</i>"
    )
    sent = await cq.message.reply(text,
                                   reply_markup=hand_kb(hand, game['top_card'], cc),
                                   parse_mode=ParseMode.HTML)
    await cq.answer()


@app.on_callback_query(filters.regex("^uno_draw$"))
async def cb_draw(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'playing':
        return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ.", show_alert=True)
    uid = cq.from_user.id
    if uid != game['players'][game['current_idx']]:
        return await cq.answer("⏳ ɴᴏᴛ ʏᴏᴜʀ ᴛᴜʀɴ!", show_alert=True)

    uid_str = str(uid)
    draw_into_hand(game, uid_str, 1)
    drawn = game['hands'][uid_str][-1]

    if can_play(drawn, game['top_card'], game['current_color']):
        await _save_game(game)
        await cq.answer(f"🎴 ᴅʀᴀᴡɴ: {card_display(drawn)}  ← ᴄᴀɴ ᴘʟᴀʏ! ᴛᴀᴘ ᴍʏ ʜᴀɴᴅ.",
                        show_alert=True)
    else:
        n = len(game['players'])
        game['current_idx'] = (game['current_idx'] + game['direction']) % n
        await _save_game(game)
        await cq.answer(f"🎴 ᴅʀᴀᴡɴ: {card_display(drawn)} — ᴛᴜʀɴ ᴘᴀssᴇᴅ.",
                        show_alert=True)
        await _update_game_msg(cq.message.chat.id, game['game_msg_id'], game)


@app.on_callback_query(filters.regex(r"^uno_play_(.+)$"))
async def cb_play(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'playing':
        return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ.", show_alert=True)

    uid = cq.from_user.id
    if uid != game['players'][game['current_idx']]:
        return await cq.answer("⏳ ɴᴏᴛ ʏᴏᴜʀ ᴛᴜʀɴ!", show_alert=True)

    card    = cq.matches[0].group(1)
    uid_str = str(uid)
    hand    = game['hands'].get(uid_str, [])

    if card not in hand:
        return await cq.answer("❓ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴀᴛ ᴄᴀʀᴅ!", show_alert=True)
    if not can_play(card, game['top_card'], game['current_color']):
        return await cq.answer(
            f"❌ ᴄᴀɴ'ᴛ ᴘʟᴀʏ {card_display(card)} ᴏɴ {card_display(game['top_card'])}",
            show_alert=True,
        )

    # Remove from hand & add to discard
    hand.remove(card)
    game['hands'][uid_str] = hand
    game['discard'].append(card)
    game['top_card'] = card

    # ── win condition ─────────────────────────────────────────────────────────
    if not hand:
        winner = game['names'].get(uid_str, "ᴘʟᴀʏᴇʀ")
        win_msg = (
            f"🏆 <b>ᴜɴᴏ! {winner} ᴡɪɴs!</b>\n\n"
            f"🎉 ᴀʟʟ ᴄᴀʀᴅs ᴘʟᴀʏᴇᴅ! +{UNO_WIN_BONUS} {pe('coin','🪙')} ᴄᴏɪɴs!\n\n"
            f"<i>{POWERED_BY}</i>"
        )
        try:
            await cq.message.delete()
        except Exception:
            pass
        await _update_game_msg(cq.message.chat.id, game['game_msg_id'], game)
        # Overwrite game msg with win text
        try:
            await app.edit_message_text(
                chat_id=cq.message.chat.id,
                message_id=game['game_msg_id'],
                text=win_msg, parse_mode=ParseMode.HTML,
            )
        except Exception:
            await cq.message.reply(win_msg, parse_mode=ParseMode.HTML)
        # Rewards
        await update_coins(uid, UNO_WIN_BONUS)
        try:
            await record_win(uid, "uno_stats", UNO_WIN_BONUS)
        except Exception:
            pass
        for pid in game['players']:
            if pid != uid:
                try:
                    await record_loss(pid, "uno_stats")
                except Exception:
                    pass
        await _del_game(cq.message.chat.id)
        return await cq.answer(f"🏆 {winner} ᴡɪɴs!")

    # ── uno alert ─────────────────────────────────────────────────────────────
    if len(hand) == 1:
        await cq.message.reply(
            f"‼️ <b>ᴜɴᴏ!</b> {game['names'].get(uid_str,'?')} ʜᴀs 1 ᴄᴀʀᴅ ʟᴇғᴛ!",
            parse_mode=ParseMode.HTML,
        )

    # ── wild → colour picker ──────────────────────────────────────────────────
    if card in ('w', 'wd'):
        game['pending_wild'] = card
        await _save_game(game)
        picker_text = (
            f"🌈 <b>{game['names'].get(uid_str,'?')} ᴘʟᴀʏᴇᴅ {card_display(card)}!</b>\n\n"
            f"ᴄʜᴏᴏsᴇ ᴀ ᴄᴏʟᴏʀ:\n\n<i>{POWERED_BY}</i>"
        )
        try:
            await cq.edit_message_text(picker_text, reply_markup=color_kb(),
                                        parse_mode=ParseMode.HTML)
        except Exception:
            await cq.message.reply(picker_text, reply_markup=color_kb(),
                                   parse_mode=ParseMode.HTML)
        return await cq.answer(f"🌈 ᴘʟᴀʏᴇᴅ {card_display(card)}!")

    # ── apply effect & next turn ──────────────────────────────────────────────
    apply_effect(game, card)
    await _save_game(game)
    try:
        await cq.message.delete()
    except Exception:
        pass
    await _update_game_msg(cq.message.chat.id, game['game_msg_id'], game)
    await cq.answer(f"✅ ᴘʟᴀʏᴇᴅ {card_display(card)}!")


@app.on_callback_query(filters.regex(r"^uno_color_([rbgy])$"))
async def cb_color(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game or game['state'] != 'playing':
        return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ.", show_alert=True)
    uid = cq.from_user.id
    if uid != game['players'][game['current_idx']]:
        return await cq.answer("ɴᴏᴛ ʏᴏᴜʀ ᴄʜᴏɪᴄᴇ!", show_alert=True)

    chosen    = cq.matches[0].group(1)
    wild_card = game.get('pending_wild', 'w')
    apply_effect(game, wild_card, chosen_color=chosen)
    game.pop('pending_wild', None)
    await _save_game(game)

    try:
        await cq.message.delete()
    except Exception:
        pass
    await _update_game_msg(cq.message.chat.id, game['game_msg_id'], game)
    await cq.answer(f"🎨 {COLOR_NAME[chosen].upper()} ᴄʜᴏsᴇɴ!")


@app.on_callback_query(filters.regex("^uno_back$"))
async def cb_back(_, cq: CallbackQuery):
    try:
        await cq.message.delete()
    except Exception:
        pass
    await cq.answer("↩️ ʜᴀɴᴅ ᴄʟᴏsᴇᴅ.")


@app.on_callback_query(filters.regex("^uno_quit$"))
async def cb_quit(_, cq: CallbackQuery):
    game = await _get_game(cq.message.chat.id)
    if not game:
        return await cq.answer("ɴᴏ ɢᴀᴍᴇ ᴀᴄᴛɪᴠᴇ.", show_alert=True)
    if cq.from_user.id != game['host_id']:
        return await cq.answer("ᴏɴʟʏ ʜᴏsᴛ ᴄᴀɴ ᴇɴᴅ!", show_alert=True)
    await _del_game(cq.message.chat.id)
    await cq.edit_message_text(
        f"🏳️ <b>ᴜɴᴏ ɢᴀᴍᴇ ᴇɴᴅᴇᴅ</b> ʙʏ {game['names'].get(str(cq.from_user.id),'ʜᴏsᴛ')}.\n\n"
        f"<i>{POWERED_BY}</i>", parse_mode=ParseMode.HTML,
    )
    await cq.answer("🏳️ ɢᴀᴍᴇ ᴇɴᴅᴇᴅ.")


# ══════════════════════════════════════════════════════════════════════════════
#  /enduno command
# ══════════════════════════════════════════════════════════════════════════════

@app.on_message(filters.command(["enduno", "uno_end"]) & filters.group)
async def cmd_enduno(_, msg: Message):
    game = await _get_game(msg.chat.id)
    if not game:
        return await msg.reply("❌ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴜɴᴏ ɢᴀᴍᴇ.", parse_mode=ParseMode.HTML)

    is_admin = False
    try:
        m = await app.get_chat_member(msg.chat.id, msg.from_user.id)
        if m.status.value in ("creator", "administrator"):
            is_admin = True
    except Exception:
        pass

    if msg.from_user.id != game['host_id'] and not is_admin:
        return await msg.reply(
            "❌ ᴏɴʟʏ ʜᴏsᴛ ᴏʀ ᴀᴅᴍɪɴ ᴄᴀɴ ᴇɴᴅ.", parse_mode=ParseMode.HTML
        )
    await _del_game(msg.chat.id)
    await msg.reply("🏳️ ᴜɴᴏ ɢᴀᴍᴇ ᴇɴᴅᴇᴅ.", parse_mode=ParseMode.HTML)

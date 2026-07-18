"""
MadaraDefaultr – Button helpers (Kurigram styled, small-caps labels)
Powered by Madara
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle
from config import PREMIUM_EMOJI


def _eid(name: str) -> str | None:
    """Return the premium emoji document ID for a named emoji, or None."""
    return PREMIUM_EMOJI.get(name)


# ── Factories ────────────────────────────────────────────────────────────────

def _build(text: str, style=None, data: str = None, url: str = None,
           emoji: str = None) -> InlineKeyboardButton:
    """Internal factory. icon_custom_emoji_id uses verified real document IDs."""
    kwargs = {}
    if style is not None:
        kwargs["style"] = style
    eid = _eid(emoji) if emoji else None
    if eid:
        kwargs["icon_custom_emoji_id"] = int(eid)
    if url:
        return InlineKeyboardButton(text, url=url, **kwargs)
    return InlineKeyboardButton(text, callback_data=data, **kwargs)


def btn(text: str, data: str = None, url: str = None,
        emoji: str = None) -> InlineKeyboardButton:
    return _build(text, data=data, url=url, emoji=emoji)


def primary_btn(text: str, data: str = None, url: str = None,
                emoji: str = None) -> InlineKeyboardButton:
    return _build(text, style=ButtonStyle.PRIMARY, data=data, url=url, emoji=emoji)


def success_btn(text: str, data: str = None, url: str = None,
                emoji: str = None) -> InlineKeyboardButton:
    return _build(text, style=ButtonStyle.SUCCESS, data=data, url=url, emoji=emoji)


def danger_btn(text: str, data: str = None, url: str = None,
               emoji: str = None) -> InlineKeyboardButton:
    return _build(text, style=ButtonStyle.DANGER, data=data, url=url, emoji=emoji)


def keyboard(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(list(rows))


# ── Preset keyboards ─────────────────────────────────────────────────────────

def start_keyboard() -> InlineKeyboardMarkup:
    return keyboard(
        [primary_btn("🎮 ɢᴀᴍᴇs ᴍᴇɴᴜ",   data="games_menu",   emoji="game"),
         success_btn("💰 ᴍʏ ᴡᴀʟʟᴇᴛ",     data="wallet",        emoji="coin")],
        [btn("📖 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs",       data="help_menu",     emoji="book"),
         btn("🏆 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ",           data="leaderboard",   emoji="trophy")],
        [primary_btn("➕ ᴀᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ",
                     url="https://t.me/SHRISTI_GAME_PLAYER_bot?startgroup=true",
                     emoji="star")],
    )


def help_menu_keyboard() -> InlineKeyboardMarkup:
    return keyboard(
        [primary_btn("🎮 ɢᴀᴍᴇs",        data="help_games",   emoji="game"),
         success_btn("💰 ᴇᴄᴏɴᴏᴍʏ",      data="help_economy", emoji="coin")],
        [btn("💘 sᴏᴄɪᴀʟ & ʀᴏᴍᴀɴᴄᴇ",    data="help_social",  emoji="heart"),
         danger_btn("⚔️ ʀᴘɢ & ᴄᴏᴍʙᴀᴛ", data="help_combat",  emoji="sword")],
        [btn("⛩️ ɢʀᴏᴜᴘ ᴍɢᴍᴛ",           data="help_group",   emoji="shield"),
         btn("🔙 ʙᴀᴄᴋ",                  data="start")],
    )


def games_keyboard() -> InlineKeyboardMarkup:
    return keyboard(
        [primary_btn("🃏 ᴄᴀʀᴅ ɢᴀᴍᴇ",  data="info_card", emoji="card"),
         danger_btn("💣 ʙᴏᴍʙ ɢᴀᴍᴇ",   data="info_bomb", emoji="bomb")],
        [success_btn("🔐 ʜᴀᴄᴋ ɢᴀᴍᴇ",  data="info_hack", emoji="lock")],
        [btn("🔙 ʙᴀᴄᴋ",                data="start")],
    )


def help_back_keyboard(back: str = "help_menu") -> InlineKeyboardMarkup:
    return keyboard([btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", data=back)])


def flip_keyboard(available_cards: list) -> InlineKeyboardMarkup:
    label_map = {"a": "🅰️ ᴀ", "b": "🅱️ ʙ", "c": "🃏 ᴄ", "d": "🎴 ᴅ"}
    row = [primary_btn(label_map[c], data=f"flip_{c}", emoji="card")
           for c in available_cards]
    return InlineKeyboardMarkup([row])


def shop_keyboard() -> InlineKeyboardMarkup:
    return keyboard(
        [primary_btn("🔪 ᴋɴɪғᴇ — 1,000",  data="buy_knife",  emoji="sword"),
         primary_btn("🔫 ɢᴜɴ — 2,500",     data="buy_gun",    emoji="sword")],
        [primary_btn("⚔️ sᴡᴏʀᴅ — 5,000",  data="buy_sword",  emoji="sword")],
        [success_btn("🛡️ sʜɪᴇʟᴅ — 1,500", data="buy_shield", emoji="shield"),
         success_btn("🦺 ᴠᴇsᴛ — 3,000",   data="buy_vest",   emoji="shield")],
        [btn("🔙 ʙᴀᴄᴋ",                   data="help_economy")],
    )

"""
MadaraDefaultr Bot Configuration
Powered by Madara
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram credentials ────────────────────────────────────────────────────
API_ID    = int(os.environ.get("API_ID", 0))
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ── Bot branding ────────────────────────────────────────────────────────────
BOT_NAME      = "ʀᴀᴊsʜʀᴇᴇ ɢᴀᴍᴇ"
BOT_USERNAME  = "rajshree_game_player_bot"
POWERED_BY    = "⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴍᴏɴ"
VERSION       = "v2.0"

# ── Database ────────────────────────────────────────────────────────────────
DATABASE_PATH = "madara.db"   # SQLite file

# ── Assets ──────────────────────────────────────────────────────────────────
START_IMAGE = "assets/start.jpg"   # legacy fallback
PING_IMAGE  = "assets/ping.jpg"    # legacy fallback
START_VIDEO = "assets/start.mp4"
PING_VIDEO  = "assets/ping.mp4"

# ── Premium emoji IDs ────────────────────────────────────────────────────────
# All IDs below are real document IDs fetched directly from Telegram sticker
# sets via MTProto. Packs: Nandu_xdd, Callmejija, Prixzz, StatusPackNew,
# sticks_0e3f7_by_TgEmodziBot.
PREMIUM_EMOJI: dict[str, str] = {
    # ── From Nandu_xdd_by_fStikBot ──────────────────────────────────────────
    "crown":      "6082168879390396599",   # 👑
    "fire":       "6082157416122683055",   # 🔥
    "zap":        "6082509100929781640",   # ⚡
    "star":       "6082163188558728946",   # ⭐
    "coin":       "6082612850159784041",   # 🪙
    "money":      "6082584623634713636",   # 💰
    "sparkle":    "6080217808891810619",   # ✨
    "heart":      "6082292578743487881",   # ❤️
    "skull":      "6082409105501195897",   # 💀
    "devil":      "6082367912469859693",   # 😈
    "check":      "6082526379583212989",   # ✅
    "ribbon":     "6082147142560910839",   # 🎀
    "butterfly":  "6082166946655112304",   # 🦋
    "headphones": "6082387600599944892",   # 🎧
    "notepad":    "6082230207228415656",   # 📝
    "knife":      "6082208801111412688",   # 🔪
    "coins_fly":  "6082586710988820084",   # 💸
    "muscle":     "6082301245987491238",   # 💪
    # ── From Callmejija_by_fStikBot ─────────────────────────────────────────
    "gift":       "6168060795016976899",   # 🎁
    "moon":       "6127573903549145643",   # 🌟 (moon)
    "wolf":       "6127636064610818291",   # 🐺
    "target":     "6125218994455582617",   # 🎯
    # ── From StatusPackNew (utility / UI icons) ──────────────────────────────
    "checkmark":  "5406690851533370477",   # ✅
    "lock":       "5409320020058584473",   # 🔓
    "warning":    "5408943604829794451",   # ⚠️
    "package":    "5409380072291316349",   # 📦
    "music":      "5409025823388741707",   # 🎵
    "arrow":      "5408834199127864608",   # ➡️
    "settings":   "5408910121264756249",   # ⚙
    "trash":      "5408832111773757273",   # 🗑
    "mic":        "5409119256107297715",   # 🎤
    "refresh":    "5408891085969700325",   # 🔄
    "link":       "5409032416163540795",   # 🔗
    "pin":        "5409228133528252069",   # 📌
    "plus":       "5408947088048271132",   # ➕
    "new_tag":    "5409344230789232321",   # 🆕
    "gamepad":    "5409098988156629257",   # 👾
    "fire2":      "5409127373595487294",   # 🔥 (status style)
    "folder":     "5409111052719767901",   # 📁
    # ── From emj_8aa5c_by_TgEmodziBot ───────────────────────────────────────
    "uno":        "5222109572598315310",   # 🎴  uno card
    "dice":       "5222067174428819458",   # 🎲  dice
    "joker":      "5219521865893520274",   # 🃏  joker card
    "rainbow":    "5219768622822228908",   # 🌈  rainbow/wild
    "search":     "5221199477799002490",   # 🔍  search/wordseek
    "letters":    "5221028936905441996",   # 🔤  letters
    "wordle":     "5221199477799002490",   # 🔍  wordle alias
    "notepad2":   "5220936717678545038",   # 📓  notepad2
    "idea2":      "5222087861012682851",   # 💡  idea
    # ── Button-slot aliases ──────────────────────────────────────────────────
    "game":       "5409098988156629257",   # 👾  gamepad
    "trophy":     "6082163188558728946",   # ⭐  star → trophy
    "bomb":       "6082157416122683055",   # 🔥  fire → bomb
    "sword":      "6082208801111412688",   # 🔪  knife → sword
    "card":       "6082147142560910839",   # 🎀  ribbon → card
    "diamond":    "6082163188558728946",   # ⭐  star → diamond
    "book":       "6082230207228415656",   # 📝  notepad → book
    "shield":     "5406690851533370477",   # ✅  checkmark → shield
    "ping":       "6082509100929781640",   # ⚡  zap → ping
}


def pe(name: str, fallback: str) -> str:
    """Return a premium animated <tg-emoji> tag; falls back to plain emoji."""
    eid = PREMIUM_EMOJI.get(name, "")
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback

# ── Game settings ───────────────────────────────────────────────────────────
CARD_TURN_TIMEOUT  = 60
BOMB_ROUND_TIMEOUT = 30
HACK_GUESS_TIMEOUT = 300

# ── Economy settings ────────────────────────────────────────────────────────
STARTING_COINS    = 5000
DAILY_BASE        = 500          # coins for day 1
CLAIM_AMOUNT      = 2000         # /claim group bonus
CLAIM_COOLDOWN    = 86400        # 24 h in seconds
DAILY_COOLDOWN    = 86400
DIVORCE_COST      = 2000
PROTECT_COST      = 1000         # per day
REVIVE_COST       = 500
TRANSFER_TAX      = 0.10         # 10 %
TRANSFER_TAX_MARRIED = 0.05      # 5 % if married

# ── RPG settings ────────────────────────────────────────────────────────────
KILL_COOLDOWN     = 3600         # 1 h between kills
KILL_SUCCESS_RATE = 0.50
KILL_LOOT_MIN     = 0.20
KILL_LOOT_MAX     = 0.40

# ── Shop items ──────────────────────────────────────────────────────────────
SHOP_ITEMS = {
    "knife":  {"name": "🔪 ᴋɴɪғᴇ",   "price": 1000,  "type": "weapon", "desc": "ᴇɴᴀʙʟᴇs /ʀᴏʙ ᴄᴏᴍᴍᴀɴᴅ"},
    "gun":    {"name": "🔫 ɢᴜɴ",     "price": 2500,  "type": "weapon", "desc": "+10% ʀᴏʙ sᴜᴄᴄᴇss"},
    "sword":  {"name": "⚔️ sᴡᴏʀᴅ",  "price": 5000,  "type": "weapon", "desc": "+20% ᴋɪʟʟ ʟᴏᴏᴛ"},
    "shield": {"name": "🛡️ sʜɪᴇʟᴅ", "price": 1500,  "type": "armor",  "desc": "-10% ᴅᴀᴍᴀɢᴇ ᴛᴀᴋᴇɴ"},
    "vest":   {"name": "🦺 ᴠᴇsᴛ",    "price": 3000,  "type": "armor",  "desc": "-20% ᴅᴀᴍᴀɢᴇ ᴛᴀᴋᴇɴ"},
}

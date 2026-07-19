"""
MadaraDefaultr – Database Layer (SQLite / aiosqlite)
Powered by Madara
"""

import aiosqlite
import json
import time

DB_PATH = "madara.db"

# ─── Init ─────────────────────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT    DEFAULT '',
                first_name  TEXT    DEFAULT '',
                coins       INTEGER DEFAULT 5000,
                gems        INTEGER DEFAULT 0,
                wins        INTEGER DEFAULT 0,
                losses      INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS relationships (
                user_id    INTEGER PRIMARY KEY,
                partner_id INTEGER DEFAULT 0,
                status     TEXT    DEFAULT 'single'
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER,
                item      TEXT,
                bought_at REAL DEFAULT 0,
                UNIQUE(user_id, item)
            );
            CREATE TABLE IF NOT EXISTS combat (
                user_id          INTEGER PRIMARY KEY,
                kills            INTEGER DEFAULT 0,
                deaths           INTEGER DEFAULT 0,
                protection_until REAL    DEFAULT 0,
                last_kill        REAL    DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS daily (
                user_id    INTEGER PRIMARY KEY,
                last_daily REAL    DEFAULT 0,
                streak     INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS group_claims (
                user_id    INTEGER,
                chat_id    INTEGER,
                last_claim REAL DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            );
            CREATE TABLE IF NOT EXISTS welcome_settings (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS bomb_stats (
                user_id   INTEGER PRIMARY KEY,
                wins      INTEGER DEFAULT 0,
                losses    INTEGER DEFAULT 0,
                coins_won INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS card_stats (
                user_id   INTEGER PRIMARY KEY,
                wins      INTEGER DEFAULT 0,
                losses    INTEGER DEFAULT 0,
                coins_won INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS hack_stats (
                user_id   INTEGER PRIMARY KEY,
                wins      INTEGER DEFAULT 0,
                losses    INTEGER DEFAULT 0,
                coins_won INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS uno_stats (
                user_id   INTEGER PRIMARY KEY,
                wins      INTEGER DEFAULT 0,
                losses    INTEGER DEFAULT 0,
                coins_won INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS uno_games (
                chat_id INTEGER PRIMARY KEY,
                data    TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS wordseek_games (
                chat_id INTEGER PRIMARY KEY,
                data    TEXT DEFAULT '{}'
            );
        """)
        await db.commit()
    print("✅ SQLite database ready.")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _row(r) -> dict:
    return dict(r) if r else {}


# ─── Users ───────────────────────────────────────────────────────────────────

STARTING_COINS = 5000

async def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """INSERT INTO users (user_id, username, first_name, coins)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username,
                 first_name=excluded.first_name""",
            (user_id, username, first_name, STARTING_COINS),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        )).fetchone()
        return _row(row)


async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT coins FROM users WHERE user_id=?", (user_id,)
        )).fetchone()
        return row[0] if row else 0


async def update_coins(user_id: int, delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins = MAX(0, coins + ?) WHERE user_id=?",
            (delta, user_id),
        )
        await db.commit()


async def set_coins(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET coins=? WHERE user_id=?", (amount, user_id)
        )
        await db.commit()


async def record_win(user_id: int, table: str, coins_won: int):
    _ALLOWED = {"bomb_stats","card_stats","hack_stats","uno_stats"}
    if table not in _ALLOWED:
        table = "card_stats"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""INSERT INTO {table} (user_id, wins, coins_won) VALUES (?,1,?)
                ON CONFLICT(user_id) DO UPDATE SET
                  wins=wins+1, coins_won=coins_won+excluded.coins_won""",
            (user_id, coins_won),
        )
        await db.execute(
            """UPDATE users SET wins=wins+1, games_played=games_played+1
               WHERE user_id=?""",
            (user_id,),
        )
        await db.commit()


async def record_loss(user_id: int, table: str):
    _ALLOWED = {"bomb_stats","card_stats","hack_stats","uno_stats"}
    if table not in _ALLOWED:
        table = "card_stats"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""INSERT INTO {table} (user_id, losses) VALUES (?,1)
                ON CONFLICT(user_id) DO UPDATE SET losses=losses+1""",
            (user_id,),
        )
        await db.execute(
            """UPDATE users SET losses=losses+1, games_played=games_played+1
               WHERE user_id=?""",
            (user_id,),
        )
        await db.commit()


async def get_top_users(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM users ORDER BY coins DESC LIMIT ?", (limit,)
        )).fetchall()
        return [_row(r) for r in rows]


async def get_bomb_leaderboard(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            """SELECT u.first_name, u.username, b.wins, b.losses, b.coins_won
               FROM bomb_stats b JOIN users u ON b.user_id=u.user_id
               ORDER BY b.wins DESC LIMIT ?""",
            (limit,),
        )).fetchall()
        return [_row(r) for r in rows]


async def get_user_rank(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT coins FROM users WHERE user_id=?", (user_id,)
        )).fetchone()
        if not row:
            return 0
        count_row = await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE coins > ?", (row[0],)
        )).fetchone()
        return (count_row[0] if count_row else 0) + 1


# ─── Relationships ────────────────────────────────────────────────────────────

async def get_relationship(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """INSERT INTO relationships (user_id) VALUES (?)
               ON CONFLICT(user_id) DO NOTHING""",
            (user_id,),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM relationships WHERE user_id=?", (user_id,)
        )).fetchone()
        return _row(row)


async def set_relationship(user_id: int, partner_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO relationships (user_id, partner_id, status) VALUES (?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 partner_id=excluded.partner_id, status=excluded.status""",
            (user_id, partner_id, status),
        )
        await db.commit()


# ─── Inventory ────────────────────────────────────────────────────────────────

async def get_inventory(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await (await db.execute(
            "SELECT item FROM inventory WHERE user_id=?", (user_id,)
        )).fetchall()
        return [r[0] for r in rows]


async def has_item(user_id: int, item: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT 1 FROM inventory WHERE user_id=? AND item=?", (user_id, item)
        )).fetchone()
        return row is not None


async def add_item(user_id: int, item: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO inventory (user_id, item, bought_at) VALUES (?,?,?)
               ON CONFLICT(user_id, item) DO NOTHING""",
            (user_id, item, time.time()),
        )
        await db.commit()


# ─── Combat ───────────────────────────────────────────────────────────────────

async def get_combat(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO combat (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING",
            (user_id,),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM combat WHERE user_id=?", (user_id,)
        )).fetchone()
        return _row(row)


async def update_combat(user_id: int, **kwargs):
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE combat SET {cols} WHERE user_id=?", vals)
        await db.commit()


async def is_protected(user_id: int) -> bool:
    c = await get_combat(user_id)
    return c.get("protection_until", 0) > time.time()


# ─── Daily / Claim ────────────────────────────────────────────────────────────

async def get_daily(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO daily (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING",
            (user_id,),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM daily WHERE user_id=?", (user_id,)
        )).fetchone()
        return _row(row)


async def set_daily(user_id: int, streak: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO daily (user_id, last_daily, streak) VALUES (?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 last_daily=excluded.last_daily, streak=excluded.streak""",
            (user_id, time.time(), streak),
        )
        await db.commit()


async def get_group_claim(user_id: int, chat_id: int) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT last_claim FROM group_claims WHERE user_id=? AND chat_id=?",
            (user_id, chat_id),
        )).fetchone()
        return row[0] if row else 0.0


async def set_group_claim(user_id: int, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO group_claims (user_id, chat_id, last_claim) VALUES (?,?,?)
               ON CONFLICT(user_id, chat_id) DO UPDATE SET last_claim=excluded.last_claim""",
            (user_id, chat_id, time.time()),
        )
        await db.commit()


# ─── Welcome ─────────────────────────────────────────────────────────────────

async def get_welcome(chat_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO welcome_settings (chat_id) VALUES (?) ON CONFLICT(chat_id) DO NOTHING",
            (chat_id,),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM welcome_settings WHERE chat_id=?", (chat_id,)
        )).fetchone()
        return _row(row)


async def set_welcome(chat_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO welcome_settings (chat_id, enabled) VALUES (?,?)
               ON CONFLICT(chat_id) DO UPDATE SET enabled=excluded.enabled""",
            (chat_id, int(enabled)),
        )
        await db.commit()


# ─── UNO game state ───────────────────────────────────────────────────────────

async def get_uno_game(chat_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT data FROM uno_games WHERE chat_id=?", (chat_id,)
        )).fetchone()
        if not row:
            return None
        return json.loads(row[0])


async def save_uno_game(game: dict):
    game['last_activity'] = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO uno_games (chat_id, data) VALUES (?,?)
               ON CONFLICT(chat_id) DO UPDATE SET data=excluded.data""",
            (game['chat_id'], json.dumps(game)),
        )
        await db.commit()


async def delete_uno_game(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM uno_games WHERE chat_id=?", (chat_id,))
        await db.commit()


# ─── Wordseek game state ──────────────────────────────────────────────────────

async def get_wordseek(chat_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT data FROM wordseek_games WHERE chat_id=?", (chat_id,)
        )).fetchone()
        if not row:
            return None
        return json.loads(row[0])


async def save_wordseek(game: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO wordseek_games (chat_id, data) VALUES (?,?)
               ON CONFLICT(chat_id) DO UPDATE SET data=excluded.data""",
            (game['chat_id'], json.dumps(game)),
        )
        await db.commit()


async def delete_wordseek(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wordseek_games WHERE chat_id=?", (chat_id,))
        await db.commit()

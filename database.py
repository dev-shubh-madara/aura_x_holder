"""
MadaraDefaultr – Database Layer (MongoDB / Motor)
Powered by Madara
"""

import time
import motor.motor_asyncio
from config import MONGO_URI, STARTING_COINS

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db = None


def _get_db():
    global _client, _db
    if _db is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        _db = _client["madaraxgame"]
    return _db


async def init_db():
    db = _get_db()
    await db.users.create_index("user_id", unique=True)
    await db.bomb_stats.create_index("user_id", unique=True)
    await db.card_stats.create_index("user_id", unique=True)
    await db.hack_stats.create_index("user_id", unique=True)
    await db.relationships.create_index("user_id", unique=True)
    await db.inventory.create_index([("user_id", 1), ("item", 1)])
    await db.combat.create_index("user_id", unique=True)
    await db.daily.create_index("user_id", unique=True)
    await db.group_claims.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
    await db.welcome_settings.create_index("chat_id", unique=True)
    print("✅ MongoDB indexes ready.")


# ─── Users ───────────────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    db = _get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "coins": STARTING_COINS,
                "gems": 0,
                "wins": 0,
                "losses": 0,
                "games_played": 0,
            },
            "$set": {"username": username, "first_name": first_name},
        },
        upsert=True,
    )
    return await db.users.find_one({"user_id": user_id}, {"_id": 0})


async def get_balance(user_id: int) -> int:
    db = _get_db()
    doc = await db.users.find_one({"user_id": user_id}, {"coins": 1})
    return doc["coins"] if doc else 0


async def update_coins(user_id: int, delta: int):
    """Add delta to coins; floor at 0."""
    db = _get_db()
    await db.users.update_one(
        {"user_id": user_id},
        [{"$set": {"coins": {"$max": [0, {"$add": ["$coins", delta]}]}}}],
    )


async def set_coins(user_id: int, amount: int):
    db = _get_db()
    await db.users.update_one({"user_id": user_id}, {"$set": {"coins": amount}})


async def record_win(user_id: int, table: str, coins_won: int):
    db = _get_db()
    await db[table].update_one(
        {"user_id": user_id},
        {"$inc": {"wins": 1, "coins_won": coins_won}},
        upsert=True,
    )
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"wins": 1, "games_played": 1}},
    )


async def record_loss(user_id: int, table: str):
    db = _get_db()
    await db[table].update_one(
        {"user_id": user_id},
        {"$inc": {"losses": 1}},
        upsert=True,
    )
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"losses": 1, "games_played": 1}},
    )


async def get_top_users(limit: int = 10) -> list:
    db = _get_db()
    cursor = db.users.find({}, {"_id": 0}).sort("coins", -1).limit(limit)
    return await cursor.to_list(limit)


async def get_bomb_leaderboard(limit: int = 10) -> list:
    db = _get_db()
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "first_name": "$user.first_name",
                "username": "$user.username",
                "wins": 1,
                "losses": 1,
                "coins_won": 1,
            }
        },
        {"$sort": {"wins": -1}},
        {"$limit": limit},
    ]
    cursor = db.bomb_stats.aggregate(pipeline)
    return await cursor.to_list(limit)


async def get_user_rank(user_id: int) -> int:
    db = _get_db()
    user = await db.users.find_one({"user_id": user_id}, {"coins": 1})
    if not user:
        return 0
    count = await db.users.count_documents({"coins": {"$gt": user["coins"]}})
    return count + 1


# ─── Relationships ────────────────────────────────────────────────────────────

async def get_relationship(user_id: int) -> dict:
    db = _get_db()
    await db.relationships.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "partner_id": 0, "status": "single"}},
        upsert=True,
    )
    return await db.relationships.find_one({"user_id": user_id}, {"_id": 0})


async def set_relationship(user_id: int, partner_id: int, status: str):
    db = _get_db()
    await db.relationships.update_one(
        {"user_id": user_id},
        {"$set": {"partner_id": partner_id, "status": status}},
        upsert=True,
    )


# ─── Inventory ────────────────────────────────────────────────────────────────

async def get_inventory(user_id: int) -> list:
    db = _get_db()
    cursor = db.inventory.find({"user_id": user_id}, {"_id": 0, "item": 1})
    docs = await cursor.to_list(None)
    return [d["item"] for d in docs]


async def has_item(user_id: int, item: str) -> bool:
    db = _get_db()
    return await db.inventory.find_one({"user_id": user_id, "item": item}) is not None


async def add_item(user_id: int, item: str):
    db = _get_db()
    if not await has_item(user_id, item):
        await db.inventory.insert_one(
            {"user_id": user_id, "item": item, "bought_at": time.time()}
        )


# ─── Combat ───────────────────────────────────────────────────────────────────

async def get_combat(user_id: int) -> dict:
    db = _get_db()
    await db.combat.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "kills": 0,
                "deaths": 0,
                "protection_until": 0.0,
                "last_kill": 0.0,
            }
        },
        upsert=True,
    )
    return await db.combat.find_one({"user_id": user_id}, {"_id": 0})


async def update_combat(user_id: int, **kwargs):
    if not kwargs:
        return
    db = _get_db()
    await db.combat.update_one({"user_id": user_id}, {"$set": kwargs})


async def is_protected(user_id: int) -> bool:
    c = await get_combat(user_id)
    return c["protection_until"] > time.time()


# ─── Daily / Claim ────────────────────────────────────────────────────────────

async def get_daily(user_id: int) -> dict:
    db = _get_db()
    await db.daily.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "last_daily": 0.0, "streak": 0}},
        upsert=True,
    )
    return await db.daily.find_one({"user_id": user_id}, {"_id": 0})


async def set_daily(user_id: int, streak: int):
    db = _get_db()
    await db.daily.update_one(
        {"user_id": user_id},
        {"$set": {"last_daily": time.time(), "streak": streak}},
        upsert=True,
    )


async def get_group_claim(user_id: int, chat_id: int) -> float:
    db = _get_db()
    doc = await db.group_claims.find_one(
        {"user_id": user_id, "chat_id": chat_id}, {"_id": 0, "last_claim": 1}
    )
    return doc["last_claim"] if doc else 0.0


async def set_group_claim(user_id: int, chat_id: int):
    db = _get_db()
    await db.group_claims.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$set": {"last_claim": time.time()}},
        upsert=True,
    )


# ─── Welcome ─────────────────────────────────────────────────────────────────

async def get_welcome(chat_id: int) -> dict:
    db = _get_db()
    await db.welcome_settings.update_one(
        {"chat_id": chat_id},
        {"$setOnInsert": {"chat_id": chat_id, "enabled": False}},
        upsert=True,
    )
    return await db.welcome_settings.find_one({"chat_id": chat_id}, {"_id": 0})


async def set_welcome(chat_id: int, enabled: bool):
    db = _get_db()
    await db.welcome_settings.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True,
    )

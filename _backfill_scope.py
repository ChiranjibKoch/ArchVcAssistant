import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def t():
    uri = os.environ["MONGO_URI"]
    db = AsyncIOMotorClient(uri)[os.environ.get("MONGO_DB", "archvc")]

    total = await db.accounts.count_documents({})
    print(f"total: {total}")

    missing = await db.accounts.count_documents(
        {"$or": [{"scope": {"$exists": False}}, {"scope": None}]}
    )
    print(f"missing scope: {missing}")

    r = await db.accounts.update_many(
        {"$or": [{"scope": {"$exists": False}}, {"scope": None}]},
        {"$set": {"scope": "owner"}},
    )
    print(f"backfilled: {r.modified_count}")

    scopes = await db.accounts.distinct("scope")
    print(f"scopes now: {scopes}")


asyncio.run(t())

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def t():
    uri = os.environ["MONGO_URI"]
    db_name = os.environ.get("MONGO_DB", "archvc")
    c = AsyncIOMotorClient(uri)
    db = c[db_name]

    r = await db.accounts.update_many(
        {},
        {"$set": {"proxy": None, "state": "up", "why": None}},
    )
    print("accounts reset:", r.modified_count)

    r2 = await db.proxies.update_many(
        {"health": "dead"},
        {"$set": {"health": "unknown", "lent": []}},
    )
    print("proxies reset:", r2.modified_count)

    c.close()


asyncio.run(t())

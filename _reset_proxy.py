import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def t():
    uri = os.environ["MONGO_URI"]
    db_name = os.environ.get("MONGO_DB", "archvc")
    c = AsyncIOMotorClient(uri)
    db = c[db_name]

    total = await db.accounts.count_documents({})
    print(f"total accounts: {total}")

    dead = await db.proxies.count_documents({"health": "dead"})
    up = await db.proxies.count_documents({"health": "up"})
    unknown = await db.proxies.count_documents({"health": "unknown"})
    print(f"proxies — up: {up}, dead: {dead}, unknown: {unknown}")

    r = await db.accounts.update_many(
        {},
        {"$set": {"proxy": None, "state": "up", "why": None}},
    )
    print(f"accounts proxy cleared: {r.modified_count}")

    r2 = await db.proxies.update_many(
        {"health": "dead"},
        {"$set": {"health": "unknown", "lent": []}},
    )
    print(f"dead proxies reset to unknown: {r2.modified_count}")

    c.close()


asyncio.run(t())

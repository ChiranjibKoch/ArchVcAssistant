import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def t():
    uri = os.environ["MONGO_URI"]
    db_name = os.environ.get("MONGO_DB", "archvc")
    print("db:", db_name)
    c = AsyncIOMotorClient(uri)
    db = c[db_name]

    try:
        await db.tenants.drop_index("tenant_1")
        print("dropped tenant_1")
    except Exception as e:
        print("drop:", e)

    try:
        await db.tenants.create_index(
            "tenant", unique=True, sparse=True, name="tenant_1"
        )
        print("recreated sparse unique")
    except Exception as e:
        print("create:", e)

    # cleanup any null-tenant docs
    r = await db.tenants.delete_many({"tenant": None, "status": "pending"})
    print("cleaned null-tenant pending docs:", r.deleted_count)

    c.close()


asyncio.run(t())

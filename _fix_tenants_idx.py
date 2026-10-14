import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def t():
    uri = os.environ["MONGO_URI"]
    db_name = os.environ.get("MONGO_DB", "archvc")
    print("db:", db_name)
    c = AsyncIOMotorClient(uri)
    db = c[db_name]

    idx = await db.tenants.list_indexes().to_list(None)
    print("current indexes:")
    for i in idx:
        print(" ", i.get("name"), i.get("key"), "unique=", i.get("unique"), "sparse=", i.get("sparse"))

    for name in ("tenant_1",):
        try:
            await db.tenants.drop_index(name)
            print(f"dropped {name}")
        except Exception as e:
            print(f"drop {name}: {e}")

    try:
        await db.tenants.create_index(
            "tenant", unique=True, sparse=True, name="tenant_1"
        )
        print("recreated tenant_1 (unique + sparse)")
    except Exception as e:
        print("create:", e)

    r = await db.tenants.delete_many({"tenant": None})
    print("cleaned null-tenant docs:", r.deleted_count)

    r2 = await db.tenants.delete_many({"tenant": {"$exists": False}, "status": "pending"})
    print("removed broken pending:", r2.deleted_count)

    idx2 = await db.tenants.list_indexes().to_list(None)
    print("final indexes:")
    for i in idx2:
        print(" ", i.get("name"), "unique=", i.get("unique"), "sparse=", i.get("sparse"))

    c.close()


asyncio.run(t())

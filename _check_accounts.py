import asyncio
import sys

from motor.motor_asyncio import AsyncIOMotorClient


async def t(uri, dbname):
    c = AsyncIOMotorClient(uri, tz_aware=True)
    db = c[dbname]

    total = await db.accounts.count_documents({})
    print("total accounts:", total)

    for state in ["up", "sick", "off"]:
        n = await db.accounts.count_documents({"state": state})
        print(f"  state={state}: {n}")

    print()
    async for doc in db.accounts.find({}).limit(5):
        print(" aid:", doc.get("account_id"))
        print("   owner:", doc.get("owner"))
        print("   state:", doc.get("state"))
        print("   phone:", doc.get("phone"))
        print("   why:", doc.get("why"))
        print()

    c.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python _check_accounts.py <mongo_uri> <db_name>")
        sys.exit(1)
    asyncio.run(t(sys.argv[1], sys.argv[2]))

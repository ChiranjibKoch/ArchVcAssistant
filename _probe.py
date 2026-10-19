import asyncio
import os

from archvc import conf, db


async def t():
    c = conf.load()
    d = db.DB(c.mongo_uri, c.mongo_db)
    await d.ready()

    total = await d.accounts.count_documents({})
    up = await d.accounts.count_documents({"state": "up"})
    sick = await d.accounts.count_documents({"state": "sick"})
    off = await d.accounts.count_documents({"state": "off"})

    print(f"total accounts: {total}")
    print(f"  state=up:   {up}")
    print(f"  state=sick: {sick}")
    print(f"  state=off:  {off}")
    print()

    async for doc in d.accounts.find({}).limit(5):
        print(f"  aid: {doc.get('account_id')}")
        print(f"    state: {doc.get('state')}")
        print(f"    scope: {doc.get('scope', '<MISSING>')}")
        print(f"    proxy: {doc.get('proxy', '<none>')[:30] if doc.get('proxy') else '<none>'}")
        print(f"    why:   {doc.get('why', '')}")
        print()

    d.close()


asyncio.run(t())

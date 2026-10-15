import asyncio
import os

from archvc import conf, db, logs
from archvc.acct import herd
from archvc.prox import fleet


async def t():
    c = conf.load()
    d = db.DB(c.mongo_uri, c.mongo_db)
    await d.ready()
    f = fleet.Fleet(d)
    await f.refresh()

    h = herd.Herd(d, c, f)
    await h.graze()
    print(f"herd: {h.size} up, {h.sick} sick", flush=True)

    chat = int(os.environ.get("PROBE_CHAT", "-1003851418677"))
    print(f"probing chat {chat}", flush=True)

    ok = 0
    fail = 0
    errs = {}
    sample = []

    for aid, client in list(h.live.items())[:5]:
        try:
            info = await client.get_chat(chat)
            print(f"  {aid}: get_chat OK - {info.title} ({info.type})", flush=True)
            try:
                await client.join_chat(chat)
                print(f"  {aid}: join_chat OK", flush=True)
                ok += 1
            except Exception as e:
                msg = f"{type(e).__name__}: {str(e)[:100]}"
                print(f"  {aid}: join_chat FAIL - {msg}", flush=True)
                errs[msg] = errs.get(msg, 0) + 1
                fail += 1
        except Exception as e:
            msg = f"get_chat {type(e).__name__}: {str(e)[:100]}"
            print(f"  {aid}: {msg}", flush=True)
            errs[msg] = errs.get(msg, 0) + 1
            fail += 1
            sample.append(aid)

    print(f"\nresult: ok={ok} fail={fail}", flush=True)
    for k, v in errs.items():
        print(f"  {v}x  {k}", flush=True)

    await h.scatter()
    d.close()


asyncio.run(t())

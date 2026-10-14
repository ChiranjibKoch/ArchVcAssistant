import asyncio
from urllib.parse import urlparse

from pyrogram.raw.functions.messages import GetMessagesViews


def parse_url(url: str):
    try:
        p = urlparse(url)
        seg = [x for x in p.path.split("/") if x]
        if len(seg) < 2:
            return None, None
        if seg[0] == "c":
            return int("-100" + seg[1]), int(seg[2])
        return seg[0], int(seg[1])
    except Exception:
        return None, None


async def boost(accounts, url: str, count: int, react=None, join=False) -> dict:
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}

    clients = list(accounts.live.values())[:count]
    ok = 0
    fail = 0
    errs = {}

    async def one(c):
        nonlocal ok, fail
        try:
            if join:
                try:
                    await c.join_chat(chat)
                except Exception:
                    pass
            peer = await c.resolve_peer(chat)
            await c.invoke(
                GetMessagesViews(
                    peer=peer,
                    id=[mid],
                    increment=True,
                )
            )
            if react:
                try:
                    await c.send_reaction(chat, mid, react)
                except Exception:
                    pass
            ok += 1
        except Exception as ex:
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for c in clients:
        tasks.append(asyncio.create_task(one(c)))
        await asyncio.sleep(0.4)
    await asyncio.gather(*tasks, return_exceptions=True)

    if errs:
        for k, v in errs.items():
            print(f"[views] {v}x {k}", flush=True)
    return {"ok": ok, "fail": fail, "errors": errs}


async def boost_scoped(app, url, count, scope):
    ids = _scope_ids(app, scope)
    return await boost_url(app.herd, url, count, ids)


async def boost_url(herd, url, count, ids):
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}

    clients = [(aid, herd.live[aid]) for aid in ids if aid in herd.live][:count]
    ok = 0
    fail = 0
    errs = {}

    async def one(aid, c):
        nonlocal ok, fail
        try:
            peer = await c.resolve_peer(chat)
            await c.invoke(GetMessagesViews(
                peer=peer, id=[mid], increment=True,
            ))
            ok += 1
        except Exception as ex:
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for aid, c in clients:
        tasks.append(asyncio.create_task(one(aid, c)))
        await asyncio.sleep(0.4)
    await asyncio.gather(*tasks, return_exceptions=True)

    return {"ok": ok, "fail": fail, "errors": errs}


def _scope_ids(app, scope):
    if not scope:
        return []
    return [
        aid for aid, s in getattr(app.herd, "scope", {}).items()
        if s == scope
    ]


async def _boost_ids(herd, url, count, ids):
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    clients = [herd.live[a] for a in ids if a in herd.live][:count]
    ok = 0
    fail = 0
    errs = {}

    async def one(c):
        nonlocal ok, fail
        try:
            peer = await c.resolve_peer(chat)
            await c.invoke(GetMessagesViews(
                peer=peer, id=[mid], increment=True,
            ))
            ok += 1
        except Exception as ex:
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for c in clients:
        tasks.append(asyncio.create_task(one(c)))
        await asyncio.sleep(0.4)
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"ok": ok, "fail": fail, "errors": errs}

import asyncio

from archvc.intx.views import parse_url


def _is_already(exc: Exception) -> bool:
    s = str(exc).lower()
    name = type(exc).__name__.lower()
    return (
        "already" in s
        or "reaction_already" in name
        or "reactionalready" in name
    )


async def swap_reaction(client, chat, mid, emoji):
    try:
        await client.send_reaction(chat, mid, None)
        await asyncio.sleep(0.3)
    except Exception:
        pass
    await client.send_reaction(chat, mid, emoji)


async def burst(accounts, url: str, emoji: str, limit=None) -> dict:
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    clients = list(accounts.live.values())
    if limit:
        clients = clients[:limit]
    ok = 0
    fail = 0
    errs = {}

    async def one(c):
        nonlocal ok, fail
        try:
            await c.send_reaction(chat, mid, emoji)
            ok += 1
        except Exception as ex:
            if _is_already(ex):
                ok += 1
                return
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for c in clients:
        tasks.append(asyncio.create_task(one(c)))
        await asyncio.sleep(0.3)
    await asyncio.gather(*tasks, return_exceptions=True)

    if errs:
        for k, v in errs.items():
            print(f"[react] {v}x {k}", flush=True)
    return {"ok": ok, "fail": fail, "errors": errs}


async def distribute(accounts, url: str, mapping: dict) -> dict:
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    clients = list(accounts.live.values())
    jobs = []
    idx = 0
    for emoji, count in mapping.items():
        for c in clients[idx: idx + count]:
            jobs.append((c, emoji))
        idx += count
    ok = 0
    fail = 0
    errs = {}

    async def one(c, e):
        nonlocal ok, fail
        try:
            await c.send_reaction(chat, mid, e)
            ok += 1
        except Exception as ex:
            if _is_already(ex):
                ok += 1
                return
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for c, e in jobs:
        tasks.append(asyncio.create_task(one(c, e)))
        await asyncio.sleep(0.3)
    await asyncio.gather(*tasks, return_exceptions=True)

    if errs:
        for k, v in errs.items():
            print(f"[react] {v}x {k}", flush=True)
    return {"ok": ok, "fail": fail, "errors": errs}


SAFE_EMOJIS = ["👍", "❤️", "🔥", "🎉", "👏", "😁", "🥰", "🤔", "🙏"]


async def random_burst(accounts, url: str, pool=None) -> dict:
    import random as _random
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    pool = pool or SAFE_EMOJIS
    clients = list(accounts.live.values())
    ok = 0
    fail = 0
    errs = {}

    async def one(c):
        nonlocal ok, fail
        e = _random.choice(pool)
        try:
            await c.send_reaction(chat, mid, e)
            ok += 1
        except Exception as ex:
            if _is_already(ex):
                ok += 1
                return
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for c in clients:
        tasks.append(asyncio.create_task(one(c)))
        await asyncio.sleep(0.3)
    await asyncio.gather(*tasks, return_exceptions=True)

    if errs:
        for k, v in errs.items():
            print(f"[react] {v}x {k}", flush=True)
    return {"ok": ok, "fail": fail, "errors": errs}


def _scope_ids(app, scope):
    if not scope:
        return []
    return [
        aid for aid, s in getattr(app.herd, "scope", {}).items()
        if s == scope
    ]


async def burst_scoped(app, url, emoji, scope):
    ids = _scope_ids(app, scope)
    return await _burst_ids(app.herd, url, emoji, ids)


async def random_burst_scoped(app, url, pool, scope):
    import random as _r
    ids = _scope_ids(app, scope)
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}

    clients = [(aid, app.herd.live[aid]) for aid in ids if aid in app.herd.live]
    ok = 0
    fail = 0
    errs = {}

    async def one(aid, c):
        nonlocal ok, fail
        e = _r.choice(pool)
        try:
            await c.send_reaction(chat, mid, e)
            ok += 1
        except Exception as ex:
            if _is_already(ex):
                ok += 1
                return
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for aid, c in clients:
        tasks.append(asyncio.create_task(one(aid, c)))
        await asyncio.sleep(0.3)
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"ok": ok, "fail": fail, "errors": errs}


async def _burst_ids(herd, url, emoji, ids):
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    clients = [(aid, herd.live[aid]) for aid in ids if aid in herd.live]
    ok = 0
    fail = 0
    errs = {}

    async def one(aid, c):
        nonlocal ok, fail
        try:
            await c.send_reaction(chat, mid, emoji)
            ok += 1
        except Exception as ex:
            if _is_already(ex):
                ok += 1
                return
            fail += 1
            k = f"{type(ex).__name__}: {str(ex)[:80]}"
            errs[k] = errs.get(k, 0) + 1

    tasks = []
    for aid, c in clients:
        tasks.append(asyncio.create_task(one(aid, c)))
        await asyncio.sleep(0.3)
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"ok": ok, "fail": fail, "errors": errs}

import asyncio

from archvc.intx.views import parse_url


async def burst(accounts, url: str, emoji: str, limit=None) -> dict:
    chat, mid = parse_url(url)
    if not mid:
        return {"ok": 0, "fail": 0, "error": "bad_url"}
    clients = list(accounts.live.values())
    if limit:
        clients = clients[:limit]
    ok = 0
    fail = 0

    async def one(c):
        nonlocal ok, fail
        try:
            await c.send_reaction(chat, mid, emoji)
            ok += 1
        except Exception:
            fail += 1

    await asyncio.gather(*(one(c) for c in clients))
    return {"ok": ok, "fail": fail}


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
            fail += 1
            key = f"{type(ex).__name__}: {str(ex)[:60]}"
            errs[key] = errs.get(key, 0) + 1

    await asyncio.gather(*(one(c, e) for c, e in jobs))
    if errs:
        for k, v in errs.items():
            print(f"[react] {v}x {k}", flush=True)
    return {"ok": ok, "fail": fail, "errors": errs}

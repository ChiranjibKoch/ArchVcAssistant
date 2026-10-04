import asyncio


async def bulk(accounts, chat, limit: int | None = None) -> dict:
    clients = list(accounts.live.values())
    if limit:
        clients = clients[:limit]
    ok = 0
    fail = 0

    async def one(c):
        nonlocal ok, fail
        try:
            await c.join_chat(chat)
            ok += 1
        except Exception:
            fail += 1

    await asyncio.gather(*(one(c) for c in clients))
    return {"ok": ok, "fail": fail}

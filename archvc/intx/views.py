import asyncio
from urllib.parse import urlparse


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

    async def one(c):
        nonlocal ok, fail
        try:
            if join:
                try:
                    await c.join_chat(chat)
                except Exception:
                    pass
            await c.get_messages(chat, mid)
            if react:
                await c.send_reaction(chat, mid, react)
            ok += 1
        except Exception:
            fail += 1

    await asyncio.gather(*(one(c) for c in clients))
    return {"ok": ok, "fail": fail}

import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone

import aiohttp

from archvc.prox import sources

CHECK_EVERY = 1800
STATS_TTL = 10


class Fleet:
    def __init__(self, db) -> None:
        self.db = db
        self._sweeper: asyncio.Task | None = None
        self._stats: dict | None = None
        self._stats_at: float = 0.0

    async def refresh(self) -> None:
        for r in await self._pull():
            await self.db.proxies.update_one(
                {"pid": r["pid"]},
                {
                    "$set": {
                        "url": r["url"],
                        "kind": r["kind"],
                        "secret": r["secret"],
                    },
                    "$setOnInsert": {
                        "health": "unknown",
                        "lent": [],
                        "checked": None,
                    },
                },
                upsert=True,
            )
        self._stats = None
        if self._sweeper is None:
            self._sweeper = asyncio.create_task(self._sweep())

    async def _pull(self) -> list[dict]:
        out: list[dict] = []
        async with aiohttp.ClientSession() as s:
            for src in sources.LIST:
                try:
                    async with s.get(src["url"], timeout=15) as r:
                        r.raise_for_status()
                        txt = await r.text()
                except Exception:
                    continue
                out += _parse(txt, src["kind"])
        return _dedupe(out)

    async def _sweep(self) -> None:
        while True:
            try:
                await self._probe_all()
            except Exception:
                pass
            await asyncio.sleep(CHECK_EVERY)

    async def _probe_all(self) -> None:
        async for row in self.db.proxies.find({}):
            ok = await _probe(row["url"])
            await self.db.proxies.update_one(
                {"pid": row["pid"]},
                {
                    "$set": {
                        "health": "up" if ok else "down",
                        "checked": datetime.now(timezone.utc),
                    }
                },
            )
        self._stats = None

    async def stats(self, force: bool = False) -> dict:
        now = time.monotonic()
        if not force and self._stats and (now - self._stats_at) < STATS_TTL:
            return self._stats
        up = await self.db.proxies.count_documents({"health": "up"})
        down = await self.db.proxies.count_documents({"health": "down"})
        unknown = await self.db.proxies.count_documents(
            {"health": {"$nin": ["up", "down"]}}
        )
        fake_tls = await self.db.proxies.count_documents({"kind": "fake_tls"})
        total = up + down + unknown
        out = {
            "up": up, "down": down, "unknown": unknown,
            "total": total, "fake_tls": fake_tls,
            "mtproto": total - fake_tls,
        }
        self._stats = out
        self._stats_at = now
        return out

    async def alive(self) -> int:
        return (await self.stats())["up"]

    async def lend(self, holder: str) -> str | None:
        row = await self.db.proxies.find_one_and_update(
            {"health": "up", "lent": {"$ne": holder}},
            {"$addToSet": {"lent": holder}},
        )
        return row["url"] if row else None

    async def clean(self) -> int:
        r = await self.db.proxies.delete_many({"health": "down"})
        self._stats = None
        return r.deleted_count

    def halt(self) -> None:
        if self._sweeper:
            self._sweeper.cancel()


def _parse(txt: str, kind: str) -> list[dict]:
    out: list[dict] = []
    if kind == "json":
        try:
            data = json.loads(txt)
        except Exception:
            return out
        items = data if isinstance(data, list) else data.get("proxies", [])
        for it in items:
            u = it if isinstance(it, str) else it.get("url")
            if u:
                r = _row(u)
                if r:
                    out.append(r)
    else:
        for line in txt.splitlines():
            line = line.strip()
            if line:
                r = _row(line)
                if r:
                    out.append(r)
    return out


def _row(url: str) -> dict | None:
    url = url.strip()
    if "tg://proxy?" not in url:
        if "server=" in url and "port=" in url:
            url = "tg://proxy?" + url.split("?", 1)[-1]
        else:
            return None
    pid = hashlib.sha1(url.encode()).hexdigest()[:16]
    secret = ""
    if "secret=" in url:
        secret = url.split("secret=", 1)[1].split("&", 1)[0]
    kind = "fake_tls" if secret.startswith("ee") else "mtproto"
    return {"pid": pid, "url": url, "secret": secret, "kind": kind}


def _dedupe(rows: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for r in rows:
        seen[r["pid"]] = r
    return list(seen.values())


async def _probe(url: str) -> bool:
    try:
        q = url.split("?", 1)[1]
        kv = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
        host, port = kv["server"], int(kv["port"])
    except Exception:
        return False
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), 5)
        w.close()
        try:
            await w.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False

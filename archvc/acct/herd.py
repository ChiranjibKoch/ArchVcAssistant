from pyrogram import Client

from archvc.acct import store


class Herd:
    def __init__(self, db, conf, fleet) -> None:
        self.db = db
        self.conf = conf
        self.fleet = fleet
        self.live: dict[str, Client] = {}
        self.size = 0
        self.sick = 0

    async def graze(self) -> None:
        async for row in self.db.accounts.find({"state": {"$ne": "off"}}):
            try:
                await self._mount(row)
                self.size += 1
            except Exception as e:
                self.sick += 1
                await self.db.accounts.update_one(
                    {"account_id": row["account_id"]},
                    {"$set": {"state": "sick", "why": str(e)[:200]}},
                )

    async def _mount(self, row: dict) -> None:
        sess = store.open_(row["session"])
        proxy = _tg_proxy(row["proxy"]) if row.get("proxy") else None
        c = Client(
            f"a-{row['account_id']}",
            api_id=row.get("api_id") or self.conf.api_id,
            api_hash=row.get("api_hash") or self.conf.api_hash,
            session_string=sess,
            proxy=proxy,
            in_memory=True,
        )
        await c.start()
        self.live[row["account_id"]] = c

    async def adopt(
        self,
        owner: int,
        phone: str,
        session: str,
        proxy: str | None = None,
        api_id: int | None = None,
        api_hash: str | None = None,
    ) -> tuple[str, bool]:
        aid = store.fingerprint(session)
        existing = await self.db.accounts.find_one({"account_id": aid})

        if existing:
            await self.db.accounts.update_one(
                {"account_id": aid},
                {
                    "$set": {
                        "owner": owner,
                        "phone": phone,
                        "state": "up",
                        "api_id": api_id or existing.get("api_id"),
                        "api_hash": api_hash or existing.get("api_hash"),
                    }
                },
            )
            if aid not in self.live:
                row = await self.db.accounts.find_one({"account_id": aid})
                await self._mount(row)
                self.size += 1
            return aid, False

        if proxy is None:
            proxy = await self.fleet.lend(aid)
        await self.db.accounts.insert_one({
            "account_id": aid,
            "owner": owner,
            "phone": phone,
            "session": store.seal(session),
            "proxy": proxy,
            "state": "up",
            "api_id": api_id,
            "api_hash": api_hash,
        })
        row = await self.db.accounts.find_one({"account_id": aid})
        await self._mount(row)
        self.size += 1
        return aid, True

    async def cull(self, aid: str) -> None:
        c = self.live.pop(aid, None)
        if c:
            try:
                await c.stop()
            except Exception:
                pass
        await self.db.accounts.update_one(
            {"account_id": aid}, {"$set": {"state": "off"}}
        )
        self.size = max(0, self.size - 1)

    async def scatter(self) -> None:
        for c in list(self.live.values()):
            try:
                await c.stop()
            except Exception:
                pass
        self.live.clear()
        self.size = 0

    def get(self, aid: str) -> Client | None:
        return self.live.get(aid)


def _tg_proxy(url: str) -> dict | None:
    try:
        q = url.split("?", 1)[1]
        kv = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
        return {
            "scheme": "mtproxy",
            "hostname": kv["server"],
            "port": int(kv["port"]),
            "secret": kv.get("secret", ""),
        }
    except Exception:
        return None

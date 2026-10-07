import random

from pyrogram import Client

from archvc.acct import store

_DEVICES = [
    "Samsung Galaxy S23", "Samsung Galaxy S24", "Samsung Galaxy A54",
    "Google Pixel 8", "Google Pixel 8 Pro", "Google Pixel 7a",
    "Xiaomi Redmi Note 12", "Xiaomi 13 Pro", "OnePlus 11", "OnePlus Nord 3",
    "iPhone 14 Pro", "iPhone 15", "iPhone 15 Pro Max", "iPhone 13",
    "Realme GT Neo 5", "Nothing Phone 2", "Motorola Edge 40",
    "Vivo V29 Pro", "Oppo Reno 10 Pro", "Asus Zenfone 10",
    "Honor 90", "Infinix Zero 30", "Tecno Camon 20",
]

_SYSTEMS = [
    "SDK 33", "SDK 34", "SDK 35",
    "Android 13", "Android 14", "Android 15",
    "iOS 17.4", "iOS 17.5", "iOS 18.0",
]

_APPS = [
    "10.2.0 (4234)", "10.3.1 (4298)", "10.4.0 (4352)",
    "10.4.2 (4380)", "10.5.0 (4411)",
]


def _device_for(aid: str) -> dict:
    seed = int(aid[:8], 16)
    rng = random.Random(seed)
    return {
        "device_model": rng.choice(_DEVICES),
        "system_version": rng.choice(_SYSTEMS),
        "app_version": rng.choice(_APPS),
    }


class Herd:
    def __init__(self, db, conf, fleet) -> None:
        self.db = db
        self.conf = conf
        self.fleet = fleet
        self.live: dict[str, Client] = {}
        self.size = 0
        self.sick = 0
        self.on_new = None

    async def graze(self) -> None:
        rows = await self.db.accounts.find(
            {"state": {"$ne": "off"}}
        ).to_list(None)
        print(f"[herd] graze: {len(rows)} candidate accounts", flush=True)

        for i, row in enumerate(rows, 1):
            aid = row.get("account_id", "?")
            print(f"[herd] {i}/{len(rows)} mounting {aid}", flush=True)
            try:
                await self._mount(row)
                self.size += 1
                print(f"[herd]   OK {aid}", flush=True)
            except Exception as e:
                self.sick += 1
                reason = f"{type(e).__name__}: {e}"
                print(f"[herd]   FAIL {aid}: {reason}", flush=True)
                await self.db.accounts.update_one(
                    {"account_id": aid},
                    {"$set": {"state": "sick", "why": reason[:200]}},
                )
        print(f"[herd] graze done: {self.size} up, {self.sick} sick", flush=True)

    async def _mount(self, row: dict) -> None:
        aid = row["account_id"]
        raw = row.get("session", "")
        if not raw:
            raise ValueError("session field empty")

        try:
            sess = store.open_(raw)
        except Exception as e:
            raise ValueError(f"store.open_ failed: {e}")

        if not sess or len(sess) < 100:
            raise ValueError(f"session too short: len={len(sess) if sess else 0}")

        proxy = _tg_proxy(row["proxy"]) if row.get("proxy") else None
        dev = row.get("device") or _device_for(aid)

        api_id = row.get("api_id") or self.conf.api_id
        api_hash = row.get("api_hash") or self.conf.api_hash

        if not api_id or not api_hash:
            raise ValueError("api_id/api_hash missing")

        try:
            c = Client(
                f"a-{aid}",
                api_id=api_id,
                api_hash=api_hash,
                session_string=sess,
                proxy=proxy,
                device_model=dev["device_model"],
                system_version=dev["system_version"],
                app_version=dev["app_version"],
                in_memory=True,
                no_updates=True,
            )
            await c.start()
        except Exception as e:
            raise ValueError(f"client.start failed: {type(e).__name__}: {e}")

        self.live[aid] = c
        if self.on_new:
            try:
                await self.on_new(aid, c)
            except Exception:
                pass

    async def adopt(
        self,
        owner: int,
        phone: str,
        session: str,
        proxy: str | None = None,
        api_id: int | None = None,
        api_hash: str | None = None,
        tg_name: str | None = None,
        tg_id: int | None = None,
    ) -> tuple[str, bool]:
        aid = store.fingerprint(session)
        existing = await self.db.accounts.find_one({"account_id": aid})
        dev = _device_for(aid)

        if existing:
            await self.db.accounts.update_one(
                {"account_id": aid},
                {
                    "$set": {
                        "owner": owner,
                        "phone": phone,
                        "state": "up",
                        "why": None,
                        "api_id": api_id or existing.get("api_id"),
                        "api_hash": api_hash or existing.get("api_hash"),
                        "tg_name": tg_name or existing.get("tg_name"),
                        "tg_id": tg_id or existing.get("tg_id"),
                        "device": existing.get("device") or dev,
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
            "tg_name": tg_name,
            "tg_id": tg_id,
            "device": dev,
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

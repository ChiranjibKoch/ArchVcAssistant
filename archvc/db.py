import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

RETRIES = 5


class DB:
    def __init__(self, uri: str, name: str) -> None:
        self._uri = uri
        self._name = name
        self._c = None
        self._db = None

    async def ready(self) -> None:
        last = None
        for i in range(RETRIES):
            try:
                self._c = AsyncIOMotorClient(
                    self._uri,
                    tz_aware=True,
                    serverSelectionTimeoutMS=15000,
                    connectTimeoutMS=15000,
                    socketTimeoutMS=30000,
                )
                self._db = self._c[self._name]
                await self._c.admin.command("ping")
                break
            except Exception as e:
                last = e
                if self._c:
                    try:
                        self._c.close()
                    except Exception:
                        pass
                self._c = None
                self._db = None
                wait = 2 ** i
                print(f"mongo connect attempt {i+1}/{RETRIES} failed: {e} — retry in {wait}s")
                await asyncio.sleep(wait)
        else:
            raise RuntimeError(f"mongo unreachable after {RETRIES} tries: {last}")

        d = self._db
        await d.sudoers.create_index("tg_id", unique=True)
        await d.tenants.create_index("tg_id", unique=True)
        await d.tenants.create_index("tenant", unique=True, sparse=True)
        await d.tenants.create_index("status")
        await d.accounts.create_index("account_id", unique=True)
        await d.accounts.create_index("owner")
        await d.accounts.create_index("state")
        await d.proxies.create_index("pid", unique=True)
        await d.proxies.create_index("health")
        await d.logs.create_index("at", expireAfterSeconds=30 * 86400)
        await d.logins.create_index("uid", unique=True)
        await d.logins.create_index("at", expireAfterSeconds=300)

    @property
    def sudoers(self):  return self._db.sudoers

    @property
    def tenants(self):  return self._db.tenants

    @property
    def accounts(self): return self._db.accounts

    @property
    def proxies(self):  return self._db.proxies

    @property
    def logs(self):     return self._db.logs

    @property
    def logins(self):   return self._db.logins

    @property
    def settings(self): return self._db.settings

    def database(self, name: str):
        return self._c[name]

    def close(self) -> None:
        if self._c:
            self._c.close()

from datetime import datetime, timezone


class Roster:
    def __init__(self, db, owner) -> None:
        self.db = db
        if isinstance(owner, (list, tuple, set)):
            self.owners = set(int(x) for x in owner)
        else:
            self.owners = {int(owner)}
        self.ids: set[int] = set()

    async def seed(self) -> None:
        now = datetime.now(timezone.utc)
        for oid in self.owners:
            await self.db.sudoers.update_one(
                {"tg_id": oid},
                {
                    "$set": {"tg_id": oid},
                    "$setOnInsert": {"by": "boot", "at": now},
                },
                upsert=True,
            )
        await self.reload()

    async def reload(self) -> None:
        rows = await self.db.sudoers.find({}, {"tg_id": 1}).to_list(None)
        self.ids = {r["tg_id"] for r in rows}

    async def add(self, tg_id: int, by: int) -> None:
        await self.db.sudoers.update_one(
            {"tg_id": tg_id},
            {
                "$set": {"by": by},
                "$setOnInsert": {"at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        self.ids.add(tg_id)

    async def drop(self, tg_id: int) -> None:
        await self.db.sudoers.delete_one({"tg_id": tg_id})
        self.ids.discard(tg_id)

    async def all(self) -> list:
        return await self.db.sudoers.find({}).to_list(None)

    def is_owner(self, uid: int) -> bool:
        return uid in self.owners

    def has(self, uid: int) -> bool:
        return uid in self.ids

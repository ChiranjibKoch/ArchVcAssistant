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
                    "$set": {"tg_id": oid, "role": "owner"},
                    "$setOnInsert": {"by": 0, "at": now},
                },
                upsert=True,
            )
        await self.reload()

    async def reload(self) -> None:
        rows = await self.db.sudoers.find({}, {"tg_id": 1}).to_list(None)
        self.ids = {int(r["tg_id"]) for r in rows}

    async def add(self, tg_id: int, by: int = 0) -> bool:
        tg_id = int(tg_id)
        if tg_id in self.owners:
            return False
        await self.db.sudoers.update_one(
            {"tg_id": tg_id},
            {
                "$set": {"tg_id": tg_id, "role": "sudo", "by": int(by)},
                "$setOnInsert": {"at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        self.ids.add(tg_id)
        return True

    async def drop(self, tg_id: int) -> bool:
        tg_id = int(tg_id)
        if tg_id in self.owners:
            return False
        r = await self.db.sudoers.delete_one(
            {"tg_id": tg_id, "role": {"$ne": "owner"}}
        )
        self.ids.discard(tg_id)
        return r.deleted_count > 0

    async def all(self) -> list:
        rows = await self.db.sudoers.find({}).to_list(None)
        for r in rows:
            if "tg_id" in r:
                r["tg_id"] = int(r["tg_id"])
        return rows

    def is_owner(self, uid: int) -> bool:
        try:
            return int(uid) in self.owners
        except (TypeError, ValueError):
            return False

    def has(self, uid: int) -> bool:
        try:
            return int(uid) in self.ids or int(uid) in self.owners
        except (TypeError, ValueError):
            return False

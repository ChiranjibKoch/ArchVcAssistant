from datetime import datetime, timezone


class Roster:
    def __init__(self, db, owner: int) -> None:
        self.db = db
        self.owner = owner
        self.ids: set[int] = set()

    async def seed(self) -> None:
        await self.db.sudoers.update_one(
            {"tg_id": self.owner},
            {
                "$set": {"tg_id": self.owner},
                "$setOnInsert": {
                    "by": "boot",
                    "at": datetime.now(timezone.utc),
                },
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

    async def all(self) -> list[dict]:
        return await self.db.sudoers.find({}).to_list(None)

    def is_owner(self, uid: int) -> bool:
        return uid == self.owner

    def has(self, uid: int) -> bool:
        return uid in self.ids

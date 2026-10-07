import secrets
from datetime import datetime, timezone


class Tenants:
    def __init__(self, db, log) -> None:
        self.db = db
        self.log = log

    async def get(self, tg_id: int):
        return await self.db.tenants.find_one({"tg_id": tg_id})

    async def request(self, tg_id: int, username, first_name):
        existing = await self.get(tg_id)
        if existing:
            return existing
        rec = {
            "tg_id": tg_id,
            "username": username,
            "name": first_name,
            "tenant": None,
            "status": "pending",
            "requested_at": datetime.now(timezone.utc),
            "approved_at": None,
            "approved_by": None,
            "rejected_at": None,
            "rejected_by": None,
        }
        await self.db.tenants.insert_one(rec)
        return rec

    async def approve(self, tg_id: int, by: int):
        t = await self.get(tg_id)
        if not t:
            return None
        if t.get("status") == "approved":
            return t.get("tenant")
        tenant_id = None
        for _ in range(8):
            cand = secrets.token_hex(4)
            if not await self.db.tenants.find_one({"tenant": cand}):
                tenant_id = cand
                break
        if not tenant_id:
            return None
        await self.db.tenants.update_one(
            {"tg_id": tg_id},
            {
                "$set": {
                    "tenant": tenant_id,
                    "status": "approved",
                    "approved_at": datetime.now(timezone.utc),
                    "approved_by": by,
                }
            },
        )
        await self.log.event(
            f"◈ ᴛᴇɴᴀɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ\n  id: {tg_id}\n  tenant: {tenant_id}\n  by: {by}"
        )
        return tenant_id

    async def reject(self, tg_id: int, by: int):
        await self.db.tenants.update_one(
            {"tg_id": tg_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_at": datetime.now(timezone.utc),
                    "rejected_by": by,
                }
            },
        )
        await self.log.event(
            f"◈ ᴛᴇɴᴀɴᴛ ʀᴇᴊᴇᴄᴛᴇᴅ\n  id: {tg_id}\n  by: {by}"
        )

    async def pending(self) -> list:
        return await self.db.tenants.find({"status": "pending"}).to_list(None)

    async def approved(self) -> list:
        return await self.db.tenants.find({"status": "approved"}).to_list(None)

    async def tenant_of(self, tg_id: int):
        t = await self.get(tg_id)
        if not t or t.get("status") != "approved":
            return None
        return t.get("tenant")

    async def status_of(self, tg_id: int) -> str:
        t = await self.get(tg_id)
        if not t:
            return "new"
        return t.get("status", "new")

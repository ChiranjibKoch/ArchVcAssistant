import secrets
from datetime import datetime, timezone


class Tenants:
    def __init__(self, db, log) -> None:
        self.db = db
        self.log = log

    async def get(self, tg_id: int):
        return await self.db.tenants.find_one({"tg_id": int(tg_id)})

    async def request(self, tg_id: int, username, first_name):
        tg_id = int(tg_id)
        existing = await self.get(tg_id)

        if existing and existing.get("status") == "approved":
            return existing

        if existing and existing.get("status") == "pending":
            return existing

        now = datetime.now(timezone.utc)
        if existing and existing.get("status") in ("rejected", "revoked"):
            await self.db.tenants.update_one(
                {"tg_id": tg_id},
                {
                    "$set": {
                        "status": "pending",
                        "requested_at": now,
                        "username": username,
                        "name": first_name,
                        "approval_messages": {},
                    },
                    "$unset": {
                        "rejected_at": "",
                        "rejected_by": "",
                        "revoked_at": "",
                    },
                },
            )
            return await self.get(tg_id)

        rec = {
            "tg_id": tg_id,
            "username": username,
            "name": first_name,
            "status": "pending",
            "requested_at": now,
        }
        await self.db.tenants.insert_one(rec)
        return rec

    async def approve(self, tg_id: int, by: int):
        tg_id = int(tg_id)
        t = await self.get(tg_id)
        if not t:
            return None
        if t.get("status") == "approved" and t.get("tenant"):
            return t["tenant"]

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
                    "approved_by": int(by),
                }
            },
        )
        await self.log.event(
            f"◈ ᴛᴇɴᴀɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ\n  id: {tg_id}\n  tenant: {tenant_id}\n  by: {by}"
        )
        return tenant_id

    async def reject(self, tg_id: int, by: int):
        await self.db.tenants.update_one(
            {"tg_id": int(tg_id)},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_at": datetime.now(timezone.utc),
                    "rejected_by": int(by),
                }
            },
        )
        await self.log.event(
            f"◈ ᴛᴇɴᴀɴᴛ ʀᴇᴊᴇᴄᴛᴇᴅ\n  id: {tg_id}\n  by: {by}"
        )

    async def revoke(self, tg_id: int, by: int):
        await self.db.tenants.update_one(
            {"tg_id": int(tg_id)},
            {
                "$set": {
                    "status": "revoked",
                    "rejected_at": datetime.now(timezone.utc),
                    "rejected_by": int(by),
                }
            },
        )
        await self.log.event(
            f"◈ ᴛᴇɴᴀɴᴛ ʀᴇᴠᴏᴋᴇᴅ\n  id: {tg_id}\n  by: {by}"
        )

    async def attach_messages(self, tg_id: int, messages: dict) -> None:
        await self.db.tenants.update_one(
            {"tg_id": int(tg_id)},
            {"$set": {"approval_messages": messages}},
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

    async def pending_or_new(self) -> list:
        return await self.db.tenants.find(
            {"status": {"$in": ["pending", "rejected", "revoked"]}}
        ).to_list(None)

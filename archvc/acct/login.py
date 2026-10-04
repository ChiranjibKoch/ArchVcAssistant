from datetime import datetime, timezone

from pyrogram import Client


class Flow:
    def __init__(self, db, conf, herd, log) -> None:
        self.db = db
        self.conf = conf
        self.herd = herd
        self.log = log
        self.pending: dict[int, dict] = {}

    async def start(self, uid: int, phone: str) -> None:
        c = Client(
            f"in-{uid}",
            api_id=self.conf.api_id,
            api_hash=self.conf.api_hash,
            in_memory=True,
        )
        await c.connect()
        sent = await c.send_code(phone)
        self.pending[uid] = {
            "client": c,
            "phone": phone,
            "hash": sent.phone_code_hash,
            "stage": "otp",
        }
        await self.db.logins.update_one(
            {"uid": uid},
            {"$set": {"phone": phone, "at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def otp(self, uid: int, code: str) -> str:
        st = self.pending.get(uid)
        if not st:
            return "no-pending"
        c: Client = st["client"]
        try:
            await c.sign_in(
                phone_number=st["phone"],
                phone_code_hash=st["hash"],
                phone_code=code,
            )
        except Exception as e:
            name = type(e).__name__
            if "SESSION_PASSWORD_NEEDED" in name or "password" in str(e).lower():
                st["stage"] = "2fa"
                return "2fa"
            return f"fail: {e}"
        return await self._done(uid, c)

    async def pwd(self, uid: int, password: str) -> str:
        st = self.pending.get(uid)
        if not st or st["stage"] != "2fa":
            return "no-pending"
        c: Client = st["client"]
        try:
            await c.check_password(password)
        except Exception as e:
            return f"2fa-fail: {e}"
        return await self._done(uid, c)

    async def import_(self, uid: int, session: str) -> str:
        try:
            c = Client(
                f"probe-{uid}",
                api_id=self.conf.api_id,
                api_hash=self.conf.api_hash,
                session_string=session,
                in_memory=True,
            )
            await c.connect()
            me = await c.get_me()
            await c.disconnect()
        except Exception as e:
            return f"bad-session: {e}"
        aid, is_new = await self.herd.adopt(
            uid, getattr(me, "phone_number", "") or "", session
        )
        tag = "new" if is_new else "updated"
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n  method: session\n  {tag}\n  aid: {aid}\n  by: {uid}"
        )
        return "ok" if is_new else "ok (refreshed)"

    async def _done(self, uid: int, c: Client) -> str:
        sess = await c.export_session_string()
        me = await c.get_me()
        await c.disconnect()
        self.pending.pop(uid, None)
        aid, is_new = await self.herd.adopt(
            uid, getattr(me, "phone_number", "") or "", sess
        )
        tag = "new" if is_new else "updated"
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n  method: otp\n  {tag}\n  aid: {aid}\n  by: {uid}"
        )
        return "ok" if is_new else "ok (refreshed)"

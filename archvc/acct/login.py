import asyncio
import os

from pyrogram import Client
from pyrogram.errors import (
    ApiIdInvalid,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)

MAX_OTP_TRIES = 3
MAX_PWD_TRIES = 3


def _norm(raw: str) -> str:
    raw = raw.strip().replace(" ", "").replace("-", "")
    if not raw.startswith("+"):
        raw = "+" + raw
    return raw


def _valid(s: str) -> bool:
    return s.startswith("+") and s[1:].isdigit() and 8 <= len(s) - 1 <= 15


class Flow:
    def __init__(self, db, conf, herd, log) -> None:
        self.db = db
        self.conf = conf
        self.herd = herd
        self.log = log
        self.pending: dict[int, dict] = {}
        self.max = int(os.environ.get("MAX_ACCOUNTS", "200"))

    def active(self, uid: int) -> bool:
        return uid in self.pending

    def cancel(self, uid: int) -> None:
        st = self.pending.pop(uid, None)
        if st and st.get("client"):
            asyncio.create_task(_quiet(st["client"]))

    async def begin(self, uid: int, raw_phone: str) -> str:
        phone = _norm(raw_phone)
        if not _valid(phone):
            return "Invalid phone. Example: 919876543210 or +919876543210"

        count = await self.db.accounts.count_documents({"state": {"$ne": "off"}})
        if count >= self.max:
            return f"Account limit reached ({self.max})."

        existing = await self.db.accounts.find_one(
            {"phone": phone, "state": {"$ne": "off"}}
        )
        if existing:
            return f"Account already added: {phone}"

        if uid in self.pending:
            self.cancel(uid)

        c = Client(
            f"in-{uid}",
            api_id=self.conf.api_id,
            api_hash=self.conf.api_hash,
            in_memory=True,
            no_updates=True,
        )
        try:
            await c.connect()
            sent = await c.send_code(phone)
        except PhoneNumberInvalid:
            await _quiet(c)
            return "Phone number invalid."
        except ApiIdInvalid:
            await _quiet(c)
            return "API_ID / API_HASH invalid."
        except Exception as e:
            await _quiet(c)
            return f"Send code failed: {e}"

        self.pending[uid] = {
            "step": "otp",
            "phone": phone,
            "client": c,
            "hash": sent.phone_code_hash,
            "otp_tries": 0,
            "pwd_tries": 0,
        }
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅ ꜱᴛᴀʀᴛᴇᴅ\n  phone: {phone}\n  by: {uid}"
        )
        return (
            f"OTP sent to {phone}.\n"
            "Send the code as a message (spaces ok).\n"
            f"You have {MAX_OTP_TRIES} tries. /cancel to abort."
        )

    async def feed(self, uid: int, text: str) -> str:
        st = self.pending.get(uid)
        if not st:
            return ""
        if st["step"] == "otp":
            return await self._otp(uid, text)
        if st["step"] == "password":
            return await self._password(uid, text)
        return ""

    async def _otp(self, uid: int, raw: str) -> str:
        st = self.pending[uid]
        c: Client = st["client"]
        code = "".join(ch for ch in raw if ch.isdigit())
        if not code:
            return "No digits found. Send the OTP code."
        try:
            await c.sign_in(
                phone_number=st["phone"],
                phone_code_hash=st["hash"],
                phone_code=code,
            )
        except PhoneCodeInvalid:
            st["otp_tries"] += 1
            left = MAX_OTP_TRIES - st["otp_tries"]
            if left <= 0:
                self.cancel(uid)
                return "OTP invalid. No tries left. /addaccount to retry."
            return f"OTP invalid. {left} tries left. Send again."
        except PhoneCodeExpired:
            self.cancel(uid)
            return "OTP expired. /addaccount to retry."
        except SessionPasswordNeeded:
            st["step"] = "password"
            return (
                f"2FA enabled. Send your password.\n"
                f"You have {MAX_PWD_TRIES} tries."
            )
        except Exception as e:
            self.cancel(uid)
            return f"Sign-in failed: {e}"
        return await self._finish(uid)

    async def _password(self, uid: int, password: str) -> str:
        st = self.pending[uid]
        c: Client = st["client"]
        try:
            await c.check_password(password)
        except PasswordHashInvalid:
            st["pwd_tries"] += 1
            left = MAX_PWD_TRIES - st["pwd_tries"]
            if left <= 0:
                self.cancel(uid)
                return "Password invalid. No tries left. /addaccount to retry."
            return f"Invalid password. {left} tries left. Send again."
        except Exception as e:
            self.cancel(uid)
            return f"2FA failed: {e}"
        return await self._finish(uid)

    async def retry(self, uid: int) -> str:
        st = self.pending.get(uid)
        if not st:
            return "No active login."
        phone = st["phone"]
        self.cancel(uid)
        return await self.begin(uid, phone)

    async def _finish(self, uid: int) -> str:
        st = self.pending.pop(uid, None)
        if not st:
            return ""
        c: Client = st["client"]
        session = await c.export_session_string()
        me = await c.get_me()
        await _quiet(c)
        phone = getattr(me, "phone_number", "") or st["phone"]
        name = f"{me.first_name or ''} {me.last_name or ''}".strip() or me.username or "Unknown"
        aid, is_new = await self.herd.adopt(
            uid, phone, session,
            api_id=self.conf.api_id,
            api_hash=self.conf.api_hash,
            tg_name=name,
            tg_id=me.id,
        )
        tag = "new" if is_new else "updated"
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n  method: otp\n  {tag}\n"
            f"  aid: {aid}\n  phone: {phone}\n  name: {name}\n  by: {uid}"
        )
        return (
            "✔ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  aid:    {aid}\n"
            f"  phone:  {phone}\n"
            f"  name:   {name}\n"
            f"  status: {tag}"
        )

    async def import_(self, uid: int, session: str) -> str:
        c = Client(
            f"probe-{uid}",
            api_id=self.conf.api_id,
            api_hash=self.conf.api_hash,
            session_string=session,
            in_memory=True,
            no_updates=True,
        )
        try:
            await c.connect()
            me = await c.get_me()
        except Exception as e:
            await _quiet(c)
            return f"Bad session: {e}"
        await _quiet(c)
        phone = getattr(me, "phone_number", "") or ""
        name = f"{me.first_name or ''} {me.last_name or ''}".strip() or me.username or "Unknown"
        aid, is_new = await self.herd.adopt(
            uid, phone, session,
            api_id=self.conf.api_id,
            api_hash=self.conf.api_hash,
            tg_name=name,
            tg_id=me.id,
        )
        tag = "new" if is_new else "updated"
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n  method: session\n  {tag}\n  aid: {aid}\n  by: {uid}"
        )
        return (
            "✔ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  aid:    {aid}\n"
            f"  phone:  {phone}\n"
            f"  name:   {name}\n"
            f"  status: {tag}"
        )


async def _quiet(c) -> None:
    try:
        await c.disconnect()
    except Exception:
        pass

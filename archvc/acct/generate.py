import asyncio

from pyrogram import Client
from pyrogram.errors import (
    ApiIdInvalid,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)


class Generate:
    def __init__(self, herd, log) -> None:
        self.herd = herd
        self.log = log
        self.states: dict[int, dict] = {}

    def active(self, uid: int) -> bool:
        return uid in self.states

    def cancel(self, uid: int) -> None:
        s = self.states.pop(uid, None)
        if s and s.get("client"):
            asyncio.create_task(_quiet_disconnect(s["client"]))

    def begin(self, uid: int) -> str:
        self.states[uid] = {"step": "api_id"}
        return "ꜱᴇɴᴅ ʏᴏᴜʀ ᴀᴘɪ_ɪᴅ"

    async def feed(self, uid: int, text: str) -> str:
        s = self.states.get(uid)
        if not s:
            return ""

        step = s["step"]

        if step == "api_id":
            try:
                s["api_id"] = int(text)
            except ValueError:
                self.states.pop(uid, None)
                return "ᴀᴘɪ_ɪᴅ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ. ᴜꜱᴇ /generate ᴛᴏ ʀᴇꜱᴛᴀʀᴛ."
            s["step"] = "api_hash"
            return "ꜱᴇɴᴅ ʏᴏᴜʀ ᴀᴘɪ_ʜᴀꜱʜ"

        if step == "api_hash":
            s["api_hash"] = text
            s["step"] = "phone"
            return "ꜱᴇɴᴅ ᴘʜᴏɴᴇ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ\nᴇxᴀᴍᴘʟᴇ: +628xxxxxxx"

        if step == "phone":
            s["phone"] = text
            try:
                c = Client(
                    f"gen_{uid}",
                    api_id=s["api_id"],
                    api_hash=s["api_hash"],
                    in_memory=True,
                )
                await c.connect()
                sent = await c.send_code(text)
                s["client"] = c
                s["code_hash"] = sent.phone_code_hash
            except ApiIdInvalid:
                self.states.pop(uid, None)
                return "ᴀᴘɪ_ɪᴅ ᴀɴᴅ ᴀᴘɪ_ʜᴀꜱʜ ᴄᴏᴍʙɪɴᴀᴛɪᴏɴ ɪꜱ ɪɴᴠᴀʟɪᴅ."
            except PhoneNumberInvalid:
                self.states.pop(uid, None)
                return "ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪꜱ ɪɴᴠᴀʟɪᴅ."
            except Exception as e:
                self.states.pop(uid, None)
                return f"ᴇʀʀᴏʀ: {e}"
            s["step"] = "otp"
            return "ꜱᴇɴᴅ ᴛʜᴇ ᴏᴛᴘ ʟɪᴋᴇ ᴛʜɪꜱ: 1 2 3 4 5"

        if step == "otp":
            code = text.replace(" ", "")
            c = s["client"]
            try:
                await c.sign_in(s["phone"], s["code_hash"], code)
            except PhoneCodeInvalid:
                self.states.pop(uid, None)
                return "ᴏᴛᴘ ɪꜱ ɪɴᴠᴀʟɪᴅ."
            except PhoneCodeExpired:
                self.states.pop(uid, None)
                return "ᴏᴛᴘ ɪꜱ ᴇxᴘɪʀᴇᴅ."
            except SessionPasswordNeeded:
                s["step"] = "password"
                return "ᴛᴡᴏ-ꜱᴛᴇᴘ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ\nꜱᴇɴᴅ ʏᴏᴜʀ ᴘᴀꜱꜱᴡᴏʀᴅ"
            except Exception as e:
                self.states.pop(uid, None)
                return f"ᴇʀʀᴏʀ: {e}"
            return await self._finish(uid)

        if step == "password":
            c = s["client"]
            try:
                await c.check_password(text)
            except PasswordHashInvalid:
                self.states.pop(uid, None)
                return "ɪɴᴠᴀʟɪᴅ ᴘᴀꜱꜱᴡᴏʀᴅ."
            except Exception as e:
                self.states.pop(uid, None)
                return f"ᴇʀʀᴏʀ: {e}"
            return await self._finish(uid)

        return ""

    async def _finish(self, uid: int) -> str:
        s = self.states.pop(uid, None)
        if not s:
            return ""
        c = s["client"]
        session = await c.export_session_string()
        me = await c.get_me()
        await _quiet_disconnect(c)
        phone = getattr(me, "phone_number", "") or s["phone"]
        aid, is_new = await self.herd.adopt(
            uid, phone, session,
            api_id=s["api_id"], api_hash=s["api_hash"],
        )
        tag = "new" if is_new else "updated"
        await self.log.event(
            f"◈ ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ\n  method: generate\n  {tag}\n  aid: {aid}\n  by: {uid}"
        )
        return (
            "✔ ꜱᴇꜱꜱɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇᴅ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  aid: {aid}\n"
            f"  phone: {phone}\n"
            f"  status: {tag}\n\n"
            f"`{session}`"
        )


async def _quiet_disconnect(c) -> None:
    try:
        await c.disconnect()
    except Exception:
        pass

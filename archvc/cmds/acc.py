from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("addsession") & filters.private)
    async def _imp(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return await m.reply("Usage: /addsession <string>")
        res = await app.login.import_(uid, parts[1].strip())
        await m.reply(res)

    @bot.on_message(filters.command("addotp") & filters.private)
    async def _otp(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2 or not _phone(parts[1]):
            return await m.reply("Usage: /addotp +91xxxxxxxxxx")
        await app.login.start(uid, parts[1])
        await m.reply("OTP sent. Send /otp <code>")

    @bot.on_message(filters.command("otp") & filters.private)
    async def _v(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return
        res = await app.login.otp(uid, parts[1])
        await m.reply(res)

    @bot.on_message(filters.command("2fa") & filters.private)
    async def _t(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return
        res = await app.login.pwd(uid, parts[1])
        await m.reply(res)

    @bot.on_message(filters.command("accounts") & filters.private)
    async def _ls(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        ids = list(app.herd.live.keys())[:60]
        body = "\ud83d\udccb \u1d00\u1d04\u1d04\u1d0f\u1d1c\u0274\u1d1b\u0455\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        body += "  \ud83d\udfe2 " + str(app.herd.size) + " online\n"
        body += "  \ud83d\udd34 " + str(app.herd.sick) + " sick\n"
        body += "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        body += "\n".join("  \u2022 " + str(i) for i in ids) if ids else "  (none)"
        await m.reply(body)


def _phone(s: str) -> bool:
    return s.startswith("+") and s[1:].isdigit() and 8 <= len(s) - 1 <= 15

from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("generate") & filters.private)
    async def _gen(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        if app.generate.active(uid):
            app.generate.cancel(uid)
        msg = await app.generate.begin(uid)
        await m.reply(msg)

    @bot.on_message(filters.command("cancel") & filters.private)
    async def _cancel(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        if app.generate.active(uid):
            app.generate.cancel(uid)
            return await m.reply("Cancelled.")
        if app.nav.peek(uid):
            app.nav.take(uid)
            return await m.reply("Cancelled.")
        await m.reply("Nothing to cancel.")

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
        body = (
            f"📋 ᴀᴄᴄᴏᴜɴᴛꜱ\n━━━━━━━━━━━━━━━━━━━━\n"
            f"  🟢 {app.herd.size} online\n"
            f"  🔴 {app.herd.sick} sick\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            + ("\n".join(f"  • {i}" for i in ids) if ids else "  (none)")
        )
        await m.reply(body)


def _phone(s: str) -> bool:
    return s.startswith("+") and s[1:].isdigit() and 8 <= len(s) - 1 <= 15

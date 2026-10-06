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
        await m.reply(app.generate.begin(uid))

    @bot.on_message(filters.command("addaccount") & filters.private)
    async def _add(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "Usage: /addaccount 919876543210\n"
                "       /addaccount +919876543210\n\n"
                "OTP will arrive — send it as next message."
            )
        await m.reply(await app.login.begin(uid, parts[1]))

    @bot.on_message(filters.command("retry") & filters.private)
    async def _retry(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        await m.reply(await app.login.retry(uid))

    @bot.on_message(filters.command("addsession") & filters.private)
    async def _imp(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return await m.reply("Usage: /addsession <string>")
        await m.reply(await app.login.import_(uid, parts[1].strip()))

    @bot.on_message(filters.command("cancel") & filters.private)
    async def _cancel(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        if app.generate.active(uid):
            app.generate.cancel(uid)
            return await m.reply("Cancelled.")
        if app.login.active(uid):
            app.login.cancel(uid)
            return await m.reply("Cancelled.")
        if app.nav.peek(uid):
            app.nav.take(uid)
            return await m.reply("Cancelled.")
        await m.reply("Nothing to cancel.")

    @bot.on_message(filters.command("accounts") & filters.private)
    async def _ls(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        rows = await app.db.accounts.find(
            {"state": {"$ne": "off"}},
            {"account_id": 1, "phone": 1, "tg_name": 1, "state": 1},
        ).limit(60).to_list(None)
        body = (
            "📋 ᴀᴄᴄᴏᴜɴᴛꜱ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  🟢 {app.herd.size} online\n"
            f"  🔴 {app.herd.sick} sick\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
        if rows:
            for r in rows:
                icon = "🟢" if r["account_id"] in app.herd.live else "⚪"
                name = r.get("tg_name") or r.get("phone") or r["account_id"][:8]
                body += f"  {icon} {name}\n"
        else:
            body += "  (none)"
        await m.reply(body)

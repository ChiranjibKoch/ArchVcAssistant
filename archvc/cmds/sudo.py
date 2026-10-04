from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("addsudo") & filters.private)
    async def _add(_, m):
        if not app.sudo.is_owner(m.from_user.id):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /addsudo <tg_id>")
        try:
            tg = int(parts[1])
        except ValueError:
            return await m.reply("Bad id.")
        await app.sudo.add(tg, by=m.from_user.id)
        await app.log.event("\u25c8 \u1d09\u1d1c\u1d05\u1d0f \u1d00\u1d05\u1d05\u1d07\u1d05\n  id: " + str(tg) + "\n  by: " + str(m.from_user.id))
        await m.reply("Added sudo: " + str(tg))

    @bot.on_message(filters.command("rmsudo") & filters.private)
    async def _rm(_, m):
        if not app.sudo.is_owner(m.from_user.id):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return
        try:
            tg = int(parts[1])
        except ValueError:
            return
        await app.sudo.drop(tg)
        await app.log.event("\u25c8 \u1d1c\u1d05\u1d0f \u0280\u1d07\u1d0d\u1d0f\u1d20\u1d07\u1d05\n  id: " + str(tg) + "\n  by: " + str(m.from_user.id))
        await m.reply("Removed sudo: " + str(tg))

    @bot.on_message(filters.command("sudolist") & filters.private)
    async def _ls(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        rows = await app.sudo.all()
        body = "\ud83d\udc65 \u1d1c\u1d05\u1d0f\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        body += "\n".join("  \u2022 " + str(r["tg_id"]) for r in rows)
        await m.reply(body)

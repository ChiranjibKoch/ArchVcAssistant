from archvc.gate import deny_cb, deny_msg
from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("stats") & filters.private)
    async def _st(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        live = await app.fleet.alive()
        total = await app.db.proxies.count_documents({})
        text = "\u2726 \u0455\u028f\u0455\u1d1b\u1d07\u1d0d\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        text += "  \u1d00\u1d04\u1d04\u1d0f\u1d1c\u0274\u1d1b\u0455    " + str(app.herd.size) + " ok \u00b7 " + str(app.herd.sick) + " sick\n"
        text += "  \u1d18\u0280\u1d0f\u0445\u026a\u1d07\u0455      " + str(live) + " alive \u00b7 " + str(total) + " total\n"
        text += "  \u1d20\u1d04 \u0455\u1d07\u0455\u0455\u026a\u1d0f\u0274\u0455  " + str(app.calls.count() if app.calls else 0) + "\n"
        text += "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        await m.reply(text)

    @bot.on_message(filters.command("proxies") & filters.private)
    async def _px(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        live = await app.fleet.alive()
        total = await app.db.proxies.count_documents({})
        await m.reply("\ud83c\udf10 \u1d18\u0280\u1d0f\u0445\u026a\u1d07\u0455\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n  alive: " + str(live) + "\n  total: " + str(total))

    @bot.on_message(filters.command("setloggroup") & filters.private)
    async def _s(_, m):
        if not app.sudo.is_owner(m.from_user.id):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /setloggroup <chat_id>")
        try:
            gid = int(parts[1])
        except ValueError:
            return await m.reply("Bad id.")
        await app.db.settings.update_one({"k": "log_group"}, {"$set": {"v": gid}}, upsert=True)
        app.log.group = gid
        await m.reply("Log group set: " + str(gid))

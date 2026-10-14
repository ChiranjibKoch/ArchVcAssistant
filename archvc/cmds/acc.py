from pyrogram import filters

from archvc.acct import scope as sc
from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("generate") & filters.private)
    async def _gen(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        if app.generate.active(uid):
            app.generate.cancel(uid)
        await m.reply(app.generate.begin(uid))

    @bot.on_message(filters.command("addaccount") & filters.private)
    async def _add(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "Usage: /addaccount 919876543210\n"
                "OTP will arrive — send it as next message."
            )
        await m.reply(await app.login.begin(uid, parts[1], scope=sp))

    @bot.on_message(filters.command("retry") & filters.private)
    async def _retry(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        await m.reply(await app.login.retry(uid))

    @bot.on_message(filters.command("addsession") & filters.private)
    async def _imp(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return await m.reply("Usage: /addsession <string>")
        await m.reply(await app.login.import_(uid, parts[1].strip(), scope=sp))

    @bot.on_message(filters.command("cancel") & filters.private)
    async def _cancel(_, m):
        uid = m.from_user.id
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
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        rows = await app.db.accounts.find(
            {"scope": sp, "state": {"$ne": "off"}},
            {"account_id": 1, "phone": 1, "tg_name": 1, "state": 1},
        ).limit(80).to_list(None)
        live = sc.ids_for(app, sp)
        body = (
            "📋 ᴀᴄᴄᴏᴜɴᴛꜱ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  🟢 {len(live)} online\n"
            f"  📦 {len(rows)} total\n"
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

    @bot.on_message(filters.command("herd") & filters.private)
    async def _herd(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        live = sc.ids_for(app, sp)
        up = await app.db.accounts.count_documents({"scope": sp, "state": "up"})
        sick = await app.db.accounts.count_documents({"scope": sp, "state": "sick"})
        off = await app.db.accounts.count_documents({"scope": sp, "state": "off"})
        await m.reply(
            "◈ ʜᴇʀᴅ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  ᴏɴʟɪɴᴇ: {len(live)}\n"
            f"  ᴜᴘ:     {up}\n"
            f"  ꜱɪᴄᴋ:   {sick}\n"
            f"  ᴏꜰꜰ:    {off}"
        )

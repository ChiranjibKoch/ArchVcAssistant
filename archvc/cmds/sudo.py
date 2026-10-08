from pyrogram import filters

from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("addsudo") & filters.private)
    async def _add(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /addsudo <tg_id>")
        try:
            tg = int(parts[1])
        except ValueError:
            return await m.reply("Bad id.")
        added = await app.sudo.add(tg, by=uid)
        if not added:
            return await m.reply(f"Already owner or sudo: {tg}")
        await app.log.event(
            f"◈ ꜱᴜᴅᴏ ᴀᴅᴅᴇᴅ\n  id: {tg}\n  by: {uid}"
        )
        try:
            await app.bot.send_message(
                tg,
                "✅ ʏᴏᴜ'ᴠᴇ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴀꜱ ꜱᴜᴅᴏ\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ /start ᴛᴏ ᴏᴘᴇɴ ᴛʜᴇ ᴍᴇɴᴜ.",
            )
        except Exception:
            pass
        await m.reply(f"✅ Added sudo: {tg}")

    @bot.on_message(filters.command("rmsudo") & filters.private)
    async def _rm(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /rmsudo <tg_id>")
        try:
            tg = int(parts[1])
        except ValueError:
            return await m.reply("Bad id.")
        ok = await app.sudo.drop(tg)
        if not ok:
            return await m.reply(f"Can't remove: {tg} (owner or not found)")
        await app.log.event(
            f"◈ ꜱᴜᴅᴏ ʀᴇᴍᴏᴠᴇᴅ\n  id: {tg}\n  by: {uid}"
        )
        await m.reply(f"✅ Removed sudo: {tg}")

    @bot.on_message(filters.command("sudolist") & filters.private)
    async def _ls(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        rows = await app.sudo.all()
        owners = [r for r in rows if r.get("role") == "owner"]
        sudos = [r for r in rows if r.get("role") != "owner"]
        lines = ["👥 ꜱᴜᴅᴏ", "━━━━━━━━━━━━━━━━━━━━"]
        lines.append(f"  ᴏᴡɴᴇʀꜱ: {len(owners)}")
        for r in owners:
            lines.append(f"    👑 {r['tg_id']}")
        lines.append(f"  ꜱᴜᴅᴏꜱ:  {len(sudos)}")
        for r in sudos:
            lines.append(f"    • {r['tg_id']}")
        await m.reply("\n".join(lines))

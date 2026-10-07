from pyrogram import filters

from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("wipe") & filters.private)
    async def _wipe(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)

        parts = m.text.split()
        mode = parts[1] if len(parts) > 1 else "sick"

        if mode == "all":
            filter_ = {}
        elif mode == "migrated":
            filter_ = {"migrated_from": {"$exists": True}}
        else:
            filter_ = {"state": "sick"}

        n = await app.db.accounts.count_documents(filter_)
        if n == 0:
            return await m.reply(f"nothing to wipe ({mode})")

        r = await app.db.accounts.delete_many(filter_)
        await app.log.event(
            f"◈ ᴡɪᴘᴇ\n  mode: {mode}\n  deleted: {r.deleted_count}\n  by: {uid}"
        )
        await m.reply(
            "🗑 ᴡɪᴘᴇ ᴅᴏɴᴇ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  ᴍᴏᴅᴇ:     {mode}\n"
            f"  ᴅᴇʟᴇᴛᴇᴅ:  {r.deleted_count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "  ʀᴇꜱᴛᴀʀᴛ ʙᴏᴛ ᴛᴏ ʀᴇꜰʀᴇꜱʜ ʜᴇʀᴅ."
        )

    @bot.on_message(filters.command("herd") & filters.private)
    async def _herd(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)

        up = await app.db.accounts.count_documents({"state": "up"})
        sick = await app.db.accounts.count_documents({"state": "sick"})
        off = await app.db.accounts.count_documents({"state": "off"})
        migrated = await app.db.accounts.count_documents({"migrated_from": {"$exists": True}})
        await m.reply(
            "◈ ʜᴇʀᴅ ꜱᴛᴀᴛᴜꜱ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  🟢 up:        {up}\n"
            f"  🔴 sick:      {sick}\n"
            f"  ⚪ off:       {off}\n"
            f"  📥 migrated:  {migrated}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "  /wipe sick   /wipe migrated   /wipe all"
        )

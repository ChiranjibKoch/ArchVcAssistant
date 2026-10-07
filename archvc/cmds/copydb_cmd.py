from pyrogram import filters

from archvc.acct import copydb, store
from archvc.gate import deny_msg

NS = "d:"
_pending: dict = {}


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("copydb") & filters.private)
    async def _copydb(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)

        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "📥 ᴄᴏᴘʏ ᴅʙ\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "  ᴜꜱᴀɢᴇ: /copydb &lt;source_db&gt;\n\n"
                "  ꜱᴄᴀɴꜱ ᴀɴᴏᴛʜᴇʀ ᴅᴀᴛᴀʙᴀꜱᴇ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ\n"
                "  ᴍᴏɴɢᴏ ꜱᴇʀᴠᴇʀ ꜰᴏʀ ꜱᴇꜱꜱɪᴏɴꜱ ᴀɴᴅ\n"
                "  ɪᴍᴘᴏʀᴛꜱ ᴛʜᴇᴍ ɪɴᴛᴏ ᴛʜɪꜱ ʙᴏᴛ.\n\n"
                "  ᴅʀʏ ᴘʀᴇᴠɪᴇᴡ ꜰɪʀꜱᴛ, ᴛʜᴇɴ ᴄᴏɴꜰɪʀᴍ."
            )

        src_name = parts[1].strip()
        await m.reply(f"🔍 ꜱᴄᴀɴɴɪɴɢ  {src_name} ...")

        try:
            src = app.db.database(src_name)
            cols = await copydb.collections(src)
        except Exception as e:
            return await m.reply(f"❌ ᴄᴀɴ'ᴛ ᴏᴘᴇɴ {src_name}\n  {e}")

        if not cols:
            return await m.reply(f"📭 {src_name} — ᴇᴍᴘᴛʏ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ")

        records = await copydb.scan(src)

        if not records:
            lines = ["📭 ɴᴏ ꜱᴇꜱꜱɪᴏɴꜱ ꜰᴏᴜɴᴅ",
                     "━━━━━━━━━━━━━━━━━━━━",
                     f"  ᴅʙ:        {src_name}",
                     f"  ᴄᴏʟʟꜱ:     {len(cols)}"]
            for c in cols[:10]:
                try:
                    n = await src[c].count_documents({})
                    lines.append(f"    {c}: {n}")
                except Exception:
                    lines.append(f"    {c}: ?")
            return await m.reply("\n".join(lines))

        fernet = store._fernet()
        owner = app.conf.owner[0] if isinstance(app.conf.owner, (tuple, list)) else app.conf.owner
        stats = await copydb.import_records(
            app.db.accounts, records, fernet, owner,
            app.conf.api_id, app.conf.api_hash, dry=True,
        )

        _pending[uid] = {"src_name": src_name, "records": records}

        errs = ""
        if stats["errors"]:
            errs = "\n\n  ᴇʀʀᴏʀꜱ:\n" + "\n".join(f"    {e[:100]}" for e in stats["errors"])

        text = (
            "📥 ᴄᴏᴘʏ ᴅʙ — ᴘʀᴇᴠɪᴇᴡ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  ꜱᴏᴜʀᴄᴇ:     {src_name}\n"
            f"  ᴄᴏʟʟꜱ:      {len(cols)}\n"
            f"  ꜰᴏᴜɴᴅ:      {len(records)}\n\n"
            f"  ᴡᴏᴜʟᴅ ɪᴍᴘᴏʀᴛ: {stats['ok']}\n"
            f"  ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ:  {stats['dup']}\n"
            f"  ꜰᴀɪʟ:       {stats['fail']}"
            f"{errs}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "  ᴘʀᴇꜱꜱ ᴄᴏɴꜰɪʀᴍ ᴛᴏ ᴡʀɪᴛᴇ ᴛᴏ ᴅʙ."
        )

        from pyrogram.enums import ButtonStyle
        from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✔ ᴄᴏɴꜰɪʀᴍ",
                                 callback_data=NS + "go",
                                 style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("✘ ᴄᴀɴᴄᴇʟ",
                                 callback_data=NS + "no",
                                 style=ButtonStyle.DANGER),
        ]])
        await m.reply(text, reply_markup=kb)

    @bot.on_callback_query(filters.regex(f"^{NS}"))
    async def _cb(_, cb):
        uid = cb.from_user.id
        if not app.sudo.is_owner(uid):
            return await cb.answer("not authorized", show_alert=True)

        state = _pending.get(uid)
        if not state:
            return await cb.answer("nothing pending", show_alert=True)

        action = cb.data[len(NS):]
        await cb.answer()

        if action == "no":
            _pending.pop(uid, None)
            return await cb.edit_message_text("✘ ᴄᴀɴᴄᴇʟʟᴇᴅ.")

        if action == "go":
            src_name = state["src_name"]
            records = state["records"]
            _pending.pop(uid, None)

            await cb.edit_message_text(
                f"⏳ ɪᴍᴘᴏʀᴛɪɴɢ {len(records)} ʀᴇᴄᴏʀᴅꜱ ꜰʀᴏᴍ {src_name} ..."
            )

            fernet = store._fernet()
            owner = app.conf.owner[0] if isinstance(app.conf.owner, (tuple, list)) else app.conf.owner
            stats = await copydb.import_records(
                app.db.accounts, records, fernet, owner,
                app.conf.api_id, app.conf.api_hash, dry=False,
            )

            await app.log.event(
                f"◈ ᴄᴏᴘʏ ᴅʙ\n  source: {src_name}\n"
                f"  imported: {stats['ok']}\n"
                f"  duplicates: {stats['dup']}\n"
                f"  fail: {stats['fail']}\n  by: {uid}"
            )

            await cb.edit_message_text(
                "✔ ᴄᴏᴘʏ ᴅʙ ᴅᴏɴᴇ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  ꜱᴏᴜʀᴄᴇ:     {src_name}\n"
                f"  ɪᴍᴘᴏʀᴛᴇᴅ:   {stats['ok']}\n"
                f"  ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ:  {stats['dup']}\n"
                f"  ꜰᴀɪʟ:       {stats['fail']}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "  ʀᴇꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʟᴏᴀᴅ ɴᴇᴡ ᴀᴄᴄᴏᴜɴᴛꜱ."
            )

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
        print(f"[copydb] handler reached uid={uid}", flush=True)
        try:
            is_owner = app.sudo.is_owner(uid)
            print(f"[copydb] is_owner={is_owner} owners={app.sudo.owners}", flush=True)
            if not is_owner:
                return await deny_msg(m)

            parts = m.text.split()
            print(f"[copydb] parts={parts}", flush=True)
            if len(parts) < 2:
                return await m.reply(
                    "📥 ᴄᴏᴘʏ ᴅʙ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ᴜꜱᴀɢᴇ: /copydb <source_db>\n\n"
                    "  ᴇx: /copydb ULTRAHOSxT"
                )

            src_name = parts[1].strip()
            await m.reply(f"🔍 ꜱᴄᴀɴɴɪɴɢ  {src_name} ...")

            try:
                src = app.db.database(src_name)
                cols = await copydb.collections(src)
            except Exception as e:
                print(f"[copydb] open fail: {e}", flush=True)
                return await m.reply(f"❌ ᴄᴀɴ'ᴛ ᴏᴘᴇɴ {src_name}\n  {e}")

            if not cols:
                return await m.reply(f"📭 {src_name} — ᴇᴍᴘᴛʏ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ")

            records = await copydb.scan(src)
            print(f"[copydb] scanned {len(records)} records", flush=True)

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
        except Exception as e:
            import traceback
            print(f"[copydb] EXCEPTION: {e}", flush=True)
            traceback.print_exc()
            try:
                await m.reply(f"❌ ᴇʀʀᴏʀ: {type(e).__name__}: {e}")
            except Exception:
                pass

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

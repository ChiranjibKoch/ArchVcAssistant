from pyrogram import filters
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from archvc.gate import deny_msg


def _resolved_text(original: str, action: str, by: int) -> str:
    if action == "yes":
        tail = f"\n\n✅ ᴀᴘᴘʀᴏᴠᴇᴅ  ·  ʙʏ {by}"
    else:
        tail = f"\n\n❌ ʀᴇᴊᴇᴄᴛᴇᴅ  ·  ʙʏ {by}"
    return (original or "") + tail


def wire(app) -> None:
    bot = app.bot

    @bot.on_callback_query(filters.regex("^appr:"))
    async def _cb(_, cb):
        uid = cb.from_user.id
        if not app.sudo.is_owner(uid):
            return await cb.answer("only owner can approve", show_alert=True)

        parts = cb.data.split(":")
        action = parts[1]
        target = int(parts[2])
        await cb.answer()

        t = await app.tenants.get(target)
        if not t or t.get("status") != "pending":
            return await cb.answer("already resolved", show_alert=True)

        if action == "yes":
            tenant = await app.tenants.approve(target, by=uid)
            if tenant:
                await app.sudo.add(target, by=uid)
            resolved = _resolved_text(cb.message.text, "yes", uid)
        else:
            await app.tenants.reject(target, by=uid)
            resolved = _resolved_text(cb.message.text, "no", uid)

        for owner_id_str, msg_id in (t.get("approval_messages") or {}).items():
            try:
                oid = int(owner_id_str)
                if oid == uid and cb.message and cb.message.id == msg_id:
                    await cb.edit_message_text(resolved)
                else:
                    await app.bot.edit_message_text(
                        chat_id=oid, message_id=msg_id, text=resolved,
                    )
            except Exception as e:
                print(f"[approval] edit fail {owner_id_str}: {e}", flush=True)

        if action == "yes":
            tenant = await app.tenants.tenant_of(target)
            try:
                await app.bot.send_message(
                    target,
                    "✅ ᴀᴄᴄᴇꜱꜱ ᴀᴘᴘʀᴏᴠᴇᴅ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"  ᴛᴇɴᴀɴᴛ: {tenant}\n\n"
                    "ꜱᴇɴᴅ /start ᴀɢᴀɪɴ.",
                )
            except Exception:
                pass
        else:
            try:
                await app.bot.send_message(
                    target,
                    "⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ\n\n"
                    "ꜱᴇɴᴅ /start ᴀɢᴀɪɴ ᴛᴏ ʀᴇǫᴜᴇꜱᴛ.",
                )
            except Exception:
                pass

    @bot.on_callback_query(filters.regex("^rmt:"))
    async def _rm_cb(_, cb):
        uid = cb.from_user.id
        if not app.sudo.is_owner(uid):
            return await cb.answer("only owner", show_alert=True)
        parts = cb.data.split(":")
        action = parts[1]
        target = int(parts[2])
        await cb.answer()

        if action == "yes":
            await app.sudo.drop(target)
            await app.tenants.revoke(target, by=uid)
            await app.autojoin.stop_scope(f"t_{target}") if hasattr(app.autojoin, "stop_scope") else None
            try:
                await cb.edit_message_text(
                    f"🗑 ᴛᴇɴᴀɴᴛ ʀᴇᴍᴏᴠᴇᴅ\n  ɪᴅ: {target}\n  ʙʏ: {uid}"
                )
            except Exception:
                pass
            try:
                await app.bot.send_message(
                    target,
                    "⛔ ᴀᴄᴄᴇꜱꜱ ʀᴇᴠᴏᴋᴇᴅ\n\n"
                    "ꜱᴇɴᴅ /start ᴀɢᴀɪɴ ᴛᴏ ʀᴇǫᴜᴇꜱᴛ.",
                )
            except Exception:
                pass
            return

        if action == "no":
            try:
                await cb.edit_message_text("✘ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
            except Exception:
                pass

    @bot.on_message(filters.command("tenants") & filters.private)
    async def _tenants(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)

        pending = await app.tenants.pending()
        approved = await app.tenants.approved()

        lines = ["👥 ᴛᴇɴᴀɴᴛꜱ", "━━━━━━━━━━━━━━━━━━━━"]
        lines.append(f"  ᴀᴘᴘʀᴏᴠᴇᴅ: {len(approved)}")
        lines.append(f"  ᴘᴇɴᴅɪɴɢ:  {len(pending)}")

        if pending:
            lines.append("")
            lines.append("⏳ ᴘᴇɴᴅɪɴɢ")
            for t in pending:
                uname = f"@{t['username']}" if t.get("username") else "—"
                lines.append(f"  {t['tg_id']}  {uname}")

        if approved:
            lines.append("")
            lines.append("✅ ᴀᴘᴘʀᴏᴠᴇᴅ")
            for t in approved:
                uname = f"@{t['username']}" if t.get("username") else "—"
                lines.append(f"  {t['tg_id']}  {t.get('tenant')}  {uname}")

        lines.append("")
        lines.append("  /rmtenant <id>  → ʀᴇᴠᴏᴋᴇ")
        await m.reply("\n".join(lines))

    @bot.on_message(filters.command("rmtenant") & filters.private)
    async def _rmtenant(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /rmtenant <tg_id>")
        try:
            target = int(parts[1])
        except ValueError:
            return await m.reply("Bad id.")

        t = await app.tenants.get(target)
        if not t or t.get("status") != "approved":
            return await m.reply(f"Not an approved tenant: {target}")

        uname = f"@{t['username']}" if t.get("username") else "—"
        text = (
            "🗑 ʀᴇᴍᴏᴠᴇ ᴛᴇɴᴀɴᴛ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  ɪᴅ:      {target}\n"
            f"  ᴜsᴇʀ:    {uname}\n"
            f"  ᴛᴇɴᴀɴᴛ:  {t.get('tenant')}\n\n"
            "  ᴀᴄᴄᴇꜱꜱ ʀᴇᴠᴏᴋᴇᴅ, ᴛᴇɴᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛꜱ ᴅɪꜱᴀʙʟᴇᴅ.\n"
            "  ᴜꜱᴇʀ ᴄᴀɴ /start ᴀɢᴀɪɴ ᴛᴏ ʀᴇ-ʀᴇǫᴜᴇꜱᴛ."
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🗑 ᴄᴏɴꜰɪʀᴍ",
                callback_data=f"rmt:yes:{target}",
                style=ButtonStyle.DANGER,
            ),
            InlineKeyboardButton(
                "✘ ᴄᴀɴᴄᴇʟ",
                callback_data=f"rmt:no:{target}",
                style=ButtonStyle.PRIMARY,
            ),
        ]])
        await m.reply(text, reply_markup=kb)

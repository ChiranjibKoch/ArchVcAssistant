from pyrogram import filters

from archvc.gate import deny_msg


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

        if action == "yes":
            tenant = await app.tenants.approve(target, by=uid)
            if tenant:
                try:
                    await cb.edit_message_text(
                        cb.message.text + f"\n\n✅ ᴀᴘᴘʀᴏᴠᴇᴅ  ·  ᴛᴇɴᴀɴᴛ {tenant}"
                    )
                except Exception:
                    pass
                try:
                    await app.bot.send_message(
                        target,
                        "✅ ᴀᴄᴄᴇꜱꜱ ᴀᴘᴘʀᴏᴠᴇᴅ\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"  ᴛᴇɴᴀɴᴛ: {tenant}\n\n"
                        "sᴇɴᴅ /start ᴀɢᴀɪɴ.",
                    )
                except Exception:
                    pass
            else:
                await cb.answer("approval failed", show_alert=True)
            return

        if action == "no":
            await app.tenants.reject(target, by=uid)
            try:
                await cb.edit_message_text(
                    cb.message.text + "\n\n❌ ʀᴇᴊᴇᴄᴛᴇᴅ"
                )
            except Exception:
                pass
            try:
                await app.bot.send_message(
                    target,
                    "⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ",
                )
            except Exception:
                pass
            return

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
        lines.append("")

        if pending:
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

        await m.reply("\n".join(lines))

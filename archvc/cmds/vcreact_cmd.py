from archvc.gate import deny_cb, deny_msg
from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("allow") & filters.private)
    async def _allow(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            allowed = await app.autojoin.allowed()
            if not allowed:
                return await m.reply(
                    "✅ ᴀʟʟᴏᴡᴇᴅ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ᴇᴍᴘᴛʏ\n\n"
                    "  ᴜꜱᴀɢᴇ: /allow &lt;chat_id&gt;"
                )
            lines = ["✅ ᴀʟʟᴏᴡᴇᴅ", "━━━━━━━━━━━━━━━━━━━━"]
            for c in allowed:
                lines.append(f"  • {c}")
            return await m.reply("\n".join(lines))
        chat = _chat(parts[1])
        added = await app.autojoin.allow(chat)
        await m.reply(f"✅ allowed: {chat}" if added else f"already allowed: {chat}")

    @bot.on_message(filters.command("disallow") & filters.private)
    async def _disallow(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /disallow <chat_id>")
        chat = _chat(parts[1])
        removed = await app.autojoin.disallow(chat)
        await m.reply(f"removed: {chat}" if removed else f"not in list: {chat}")

    @bot.on_message(filters.command("autoreact") & filters.private)
    async def _auto(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()

        if len(parts) < 2:
            st = app.autojoin.status()
            if not st:
                return await m.reply(
                    "⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ɴᴏ ᴄʜᴀᴛꜱ ʀᴜɴɴɪɴɢ\n\n"
                    "  /autoreact &lt;chat&gt; [sec]\n"
                    "  /autoreact off\n"
                    "  /autoreact off &lt;chat&gt;"
                )
            lines = ["⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ", "━━━━━━━━━━━━━━━━━━━━"]
            for c, cfg in st.items():
                lines.append(f"  {c}  every {cfg['interval']}s")
            lines.append("")
            lines.append("  /autoreact off       stop all")
            lines.append("  /autoreact off <chat> stop one")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = await app.autojoin.stop_all()
                return await m.reply(f"stopped {n} autoreact(s)")
            chat = _chat(parts[2])
            await app.autojoin.stop(chat)
            return await m.reply(f"stopped: {chat}")

        chat = _chat(parts[1])
        interval = 45
        if len(parts) > 2:
            try:
                interval = int(parts[2])
            except ValueError:
                return await m.reply("interval must be a number (seconds)")
        res = await app.autojoin.start(chat, interval)
        if res == "started":
            await m.reply(
                "⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  chat:     {chat}\n"
                f"  interval: {max(15, interval)}s"
            )
        else:
            await m.reply(res)


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

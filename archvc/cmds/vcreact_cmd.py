from pyrogram import filters

from archvc.gate import deny_msg


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
                    "  ᴜꜱᴀɢᴇ: /allow <chat_id>"
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
                    "  /autoreact <chat>   ᴏɴ\n"
                    "  /autoreact off      ꜱᴛᴏᴘ ᴀʟʟ"
                )
            lines = ["⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ", "━━━━━━━━━━━━━━━━━━━━"]
            for c, cfg in st.items():
                lines.append(f"  {c}")
                lines.append(f"    every {cfg['interval']}s · batch {cfg['batch']}")
            lines.append("")
            lines.append("  /autoreact off   ꜱᴛᴏᴘ ᴀʟʟ")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = await app.autojoin.stop_all()
                return await m.reply(f"stopped {n} autoreact(s)")
            chat = _chat(parts[2])
            await app.autojoin.stop(chat)
            return await m.reply(f"stopped: {chat}")

        chat = _chat(parts[1])

        if not await app.autojoin.is_allowed(chat):
            await app.autojoin.allow(chat)

        res = await app.autojoin.start(chat)
        if res == "started":
            await m.reply(
                "⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  chat:     {chat}\n"
                "  interval: 60s\n"
                "  batch:    15 accounts"
            )
        else:
            await m.reply(res)


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

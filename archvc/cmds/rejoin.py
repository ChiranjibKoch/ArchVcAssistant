from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("autojoin") & filters.private)
    async def _aj(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()

        if len(parts) < 2:
            s = app.watchdog.status()
            if not s:
                return await m.reply(
                    "👁 ᴀᴜᴛᴏᴊᴏɪɴ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ɴᴏ ᴡᴀᴛᴄʜᴇᴅ ᴄʜᴀᴛꜱ\n\n"
                    "  ᴜꜱᴀɢᴇ: /autojoin &lt;chat&gt;\n"
                    "         /autojoin off"
                )
            lines = ["👁 ᴀᴜᴛᴏᴊᴏɪɴ", "━━━━━━━━━━━━━━━━━━━━"]
            for chat, st in s.items():
                lines.append(f"  {chat}: {st['in']}/{st['should']}")
            lines.append("")
            lines.append("/autojoin off          stop all")
            lines.append("/autojoin off <chat>   stop one")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = app.watchdog.unwatch_all()
                return await m.reply(f"autojoin disabled for {n} chat(s)")
            chat = _chat(parts[2])
            app.watchdog.unwatch(chat)
            return await m.reply(f"autojoin disabled: {chat}")

        chat = _chat(parts[1])
        n = app.watchdog.watch_chat(chat)
        await m.reply(
            "👁 ᴀᴜᴛᴏᴊᴏɪɴ ᴏɴ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  chat:     {chat}\n"
            f"  watching: {n} accounts\n"
            "  interval: 60s"
        )


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

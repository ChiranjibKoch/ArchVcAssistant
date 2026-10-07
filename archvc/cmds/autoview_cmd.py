from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("autoview") & filters.private)
    async def _av(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()

        if len(parts) < 2:
            st = app.autoview.status()
            if not st:
                return await m.reply(
                    "👁 ᴀᴜᴛᴏᴠɪᴇᴡ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ɴᴏ ᴛᴀʀɢᴇᴛꜱ\n\n"
                    "  ᴜꜱᴀɢᴇ: /autoview &lt;post_url&gt; [sec] [count]\n"
                    "         /autoview off\n"
                    "         /autoview off &lt;url&gt;"
                )
            lines = ["👁 ᴀᴜᴛᴏᴠɪᴇᴡ", "━━━━━━━━━━━━━━━━━━━━"]
            for url, cfg in st.items():
                lines.append(f"  {url}")
                lines.append(f"    every {cfg['interval']}s · {cfg['count']}/cycle")
            lines.append("")
            lines.append("  /autoview off       stop all")
            lines.append("  /autoview off <url> stop one")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = await app.autoview.stop_all()
                return await m.reply(f"stopped {n} autoview(s)")
            url = parts[2]
            await app.autoview.stop(url)
            return await m.reply(f"stopped: {url}")

        url = parts[1]
        interval = 120
        count = 50
        if len(parts) > 2:
            try:
                interval = int(parts[2])
            except ValueError:
                return await m.reply("interval must be a number")
        if len(parts) > 3:
            try:
                count = int(parts[3])
            except ValueError:
                return await m.reply("count must be a number")

        res = await app.autoview.start(url, interval, count)
        if res == "started":
            await m.reply(
                "👁 ᴀᴜᴛᴏᴠɪᴇᴡ ᴏɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  url:      {url}\n"
                f"  interval: {max(30, interval)}s\n"
                f"  count:    {count}"
            )
        else:
            await m.reply(res)


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

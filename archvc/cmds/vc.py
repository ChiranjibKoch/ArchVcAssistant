from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("joinvc") & filters.private)
    async def _j(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /joinvc <chat>")
        chat = _chat(parts[1])
        await m.reply("Joining...")
        res = await app.calls.join(chat)
        ok = sum(1 for v in res.values() if v == "ok")
        fail = len(res) - ok
        await m.reply("Join: " + str(ok) + " ok / " + str(fail) + " fail")
        await app.log.event("\u25a3 \u1d20\u1d04 \u1d0a\u1d0f\u026a\u0274\n  chat: " + str(chat) + "\n  ok: " + str(ok) + " | fail: " + str(fail) + "\n  by: " + str(uid))

    @bot.on_message(filters.command("leavevc") & filters.private)
    async def _l(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /leavevc <chat>")
        chat = _chat(parts[1])
        res = await app.calls.leave(chat)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply("Leave: " + str(ok) + " ok / " + str(len(res) - ok) + " fail")

    @bot.on_message(filters.command("play") & filters.private)
    async def _p(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split(maxsplit=2)
        if len(parts) < 3:
            return await m.reply("Usage: /play <chat> <source>")
        chat = _chat(parts[1])
        from archvc.vc import media
        try:
            url = await media.resolve_async(parts[2])
        except Exception as e:
            return await m.reply("Resolve failed: " + str(e))
        res = await app.calls.play_all(chat, url)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply("Play: " + str(ok) + " ok / " + str(len(res) - ok) + " fail")

    @bot.on_message(filters.command("pause") & filters.private)
    async def _pa(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /pause <chat>")
        await app.calls.pause(_chat(parts[1]))
        await m.reply("Paused.")

    @bot.on_message(filters.command("mute") & filters.private)
    async def _mu(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return
        await app.calls.mute(_chat(parts[1]))
        await m.reply("Muted.")

    @bot.on_message(filters.command("unmute") & filters.private)
    async def _um(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        parts = m.text.split()
        if len(parts) < 2:
            return
        await app.calls.unmute(_chat(parts[1]))
        await m.reply("Unmuted.")


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

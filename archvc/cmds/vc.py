from pyrogram import filters

from archvc.intx import vcreact
from archvc.gate import deny_cb, deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("joinvc") & filters.private)
    async def _j(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /joinvc <chat>")
        chat = _chat(parts[1])

        h = await app.calls.precheck(app.bot, chat)
        if h.get("error"):
            return await m.reply(
                "⛔ ᴄᴀɴ'ᴛ ᴊᴏɪɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  chat: {chat}\n"
                f"  ᴇʀʀᴏʀ: {h['error']}"
            )

        await m.reply("Joining...")
        res = await app.calls.join(chat)
        ok = sum(1 for v in res.values() if v == "ok")
        fail = len(res) - ok
        body = f"Join: {ok} ok / {fail} fail"
        errs = {}
        for v in res.values():
            if v.startswith("fail:"):
                errs[v[5:]] = errs.get(v[5:], 0) + 1
        for e, n in list(errs.items())[:3]:
            body += f"\n  {n}x  {e[:150]}"
        await m.reply(body)
        await app.log.event(
            f"▣ ᴠᴄ ᴊᴏɪɴ\n  chat: {chat}\n"
            f"  ok: {ok} | fail: {fail}\n  by: {uid}"
        )

    @bot.on_message(filters.command("leavevc") & filters.private)
    async def _l(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /leavevc <chat>")
        chat = _chat(parts[1])
        res = await app.calls.leave(chat)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply(f"Leave: {ok} ok / {len(res) - ok} fail")

    @bot.on_message(filters.command("vcreact") & filters.private)
    async def _vr(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 3:
            return await m.reply("Usage: /vcreact <chat> <emoji>")
        chat = _chat(parts[1])
        emoji = parts[2]
        res = await vcreact.burst(
            app.herd, chat, emoji, cache=app.calls.input_calls
        )
        await m.reply(f"VC reactions: {res['ok']} ok / {res['fail']} fail")
        await app.log.event(
            f"▣ ᴠᴄ ʀᴇᴀᴄᴛɪᴏɴ\n  chat: {chat}\n  emoji: {emoji}\n"
            f"  ok: {res['ok']} | fail: {res['fail']}\n  by: {uid}"
        )

    @bot.on_message(filters.command("play") & filters.private)
    async def _p(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split(maxsplit=2)
        if len(parts) < 3:
            return await m.reply("Usage: /play <chat> <source>")
        chat = _chat(parts[1])
        from archvc.vc import media
        try:
            url = await media.resolve_async(parts[2])
        except Exception as e:
            return await m.reply(f"Resolve failed: {e}")
        res = await app.calls.play_all(chat, url)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply(f"Play: {ok} ok / {len(res) - ok} fail")

    @bot.on_message(filters.command("pause") & filters.private)
    async def _pa(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /pause <chat>")
        await app.calls.pause(_chat(parts[1]))
        await m.reply("Paused.")

    @bot.on_message(filters.command("mute") & filters.private)
    async def _mu(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return
        await app.calls.mute(_chat(parts[1]))
        await m.reply("Muted.")

    @bot.on_message(filters.command("unmute") & filters.private)
    async def _um(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
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

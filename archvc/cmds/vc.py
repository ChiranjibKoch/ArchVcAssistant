from pyrogram import filters

from archvc.acct import scope as sc
from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("joinvc") & filters.private)
    async def _j(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return await m.reply(
                "Usage: /joinvc <chat>\n"
                "Formats accepted:\n"
                "  @username\n"
                "  -1001234567890\n"
                "  https://t.me/username\n"
                "  https://t.me/+invitehash\n"
                "  https://t.me/username?livestream"
            )
        chat_input = parts[1].strip()

        await m.reply("checking...")
        h = await app.calls.precheck(app.bot, chat_input)
        if h.get("error"):
            return await m.reply(
                "⛔ ᴄᴀɴ'ᴛ ᴊᴏɪɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  chat: {chat_input}\n"
                f"  {h['error']}"
            )

        await m.reply(f"Joining {h.get('id')}...")
        res = await app.calls.join_scoped(chat_input, sp)
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
            f"▣ ᴠᴄ ᴊᴏɪɴ\n  chat: {h.get('id') or chat_input}\n  scope: {sp}\n"
            f"  ok: {ok} | fail: {fail}\n  by: {uid}"
        )

    @bot.on_message(filters.command("leavevc") & filters.private)
    async def _l(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return await m.reply("Usage: /leavevc <chat>")
        res = await app.calls.leave_scoped(parts[1].strip(), sp)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply(f"Leave: {ok} ok / {len(res) - ok} fail")

    @bot.on_message(filters.command("play") & filters.private)
    async def _p(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=2)
        if len(parts) < 3:
            return await m.reply("Usage: /play <chat> <source>")
        from archvc.vc import media
        try:
            url = await media.resolve_async(parts[2])
        except Exception as e:
            return await m.reply(f"Resolve failed: {e}")
        res = await app.calls.play_all_scoped(parts[1].strip(), url, sp)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply(f"Play: {ok} ok / {len(res) - ok} fail")

    @bot.on_message(filters.command("mute") & filters.private)
    async def _mu(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return
        await app.calls.mute_scoped(parts[1].strip(), sp)
        await m.reply("Muted.")

    @bot.on_message(filters.command("unmute") & filters.private)
    async def _um(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            return
        await app.calls.unmute_scoped(parts[1].strip(), sp)
        await m.reply("Unmuted.")

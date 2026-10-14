from pyrogram import filters

from archvc.acct import scope as sc
from archvc.gate import deny_msg
from archvc.intx import vcreact


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("joinvc") & filters.private)
    async def _j(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /joinvc <chat>")
        chat = _chat(parts[1])
        await m.reply("Joining...")
        res = await app.calls.join_scoped(chat, sp)
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
            f"▣ ᴠᴄ ᴊᴏɪɴ\n  chat: {chat}\n  scope: {sp}\n"
            f"  ok: {ok} | fail: {fail}\n  by: {uid}"
        )

    @bot.on_message(filters.command("leavevc") & filters.private)
    async def _l(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /leavevc <chat>")
        chat = _chat(parts[1])
        res = await app.calls.leave_scoped(chat, sp)
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
        chat = _chat(parts[1])
        from archvc.vc import media
        try:
            url = await media.resolve_async(parts[2])
        except Exception as e:
            return await m.reply(f"Resolve failed: {e}")
        res = await app.calls.play_all_scoped(chat, url, sp)
        ok = sum(1 for v in res.values() if v == "ok")
        await m.reply(f"Play: {ok} ok / {len(res) - ok} fail")

    @bot.on_message(filters.command("mute") & filters.private)
    async def _mu(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return
        await app.calls.mute_scoped(_chat(parts[1]), sp)
        await m.reply("Muted.")

    @bot.on_message(filters.command("unmute") & filters.private)
    async def _um(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return
        await app.calls.unmute_scoped(_chat(parts[1]), sp)
        await m.reply("Unmuted.")


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

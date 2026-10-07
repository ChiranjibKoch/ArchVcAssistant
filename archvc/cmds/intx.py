from pyrogram import filters

from archvc.intx import react, views
from archvc.gate import deny_cb, deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("rx") & filters.private)
    async def _rx(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 3:
            return await m.reply("Usage: /rx <post_url> <emoji>")
        url, emoji = parts[1], parts[2]
        res = await react.burst(app.herd, url, emoji)
        await m.reply("Reactions: " + str(res["ok"]) + " ok / " + str(res["fail"]) + " fail")
        await app.log.event("\u25a3 \u0280\u1d07\u1d00\u1d04\u1d1b\u026a\u1d0f\u0274\u0455 \u0455\u1d07\u0274\u1d1b\n  post: " + url + "\n  emoji: " + emoji + "\n  ok: " + str(res["ok"]) + " | fail: " + str(res["fail"]) + "\n  by: " + str(uid))

    @bot.on_message(filters.command("views") & filters.private)
    async def _vw(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 3:
            return await m.reply("Usage: /views <post_url> <count> [emoji]")
        url = parts[1]
        try:
            n = int(parts[2])
        except ValueError:
            return await m.reply("Bad count.")
        emoji = parts[3] if len(parts) > 3 else None
        res = await views.boost(app.herd, url, n, react=emoji)
        await m.reply("Views: " + str(res["ok"]) + " ok / " + str(res["fail"]) + " fail")
        await app.log.event("\u25a3 \u1d20\u026a\u1d07\u1d21\u0455 \u1d00\u1d05\u1d05\u1d07\u1d05\n  post: " + url + "\n  target: " + str(n) + " | ok: " + str(res["ok"]) + "\n  by: " + str(uid))

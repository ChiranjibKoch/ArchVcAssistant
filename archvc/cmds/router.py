from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.private & filters.text)
    async def _input(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        text = (m.text or "").strip()
        if text.startswith("/"):
            return

        if app.generate.active(uid):
            res = await app.generate.feed(uid, text)
            if res:
                await m.reply(res)
            return

        state = app.nav.peek(uid)
        if not state:
            return
        app.nav.take(uid)

        if state == "acc:session":
            res = await app.login.import_(uid, text)
            await m.reply(res)

        elif state == "acc:phone":
            if not _phone(text):
                app.nav.set(uid, state)
                return await m.reply("Bad phone. Send in +91xxxxxxxxxx format.")
            await app.login.start(uid, text)
            await m.reply("OTP sent. Send /otp <code>")

        elif state == "vc:join":
            chat = _chat(text)
            await m.reply("Joining...")
            res = await app.calls.join(chat)
            ok = sum(1 for v in res.values() if v == "ok")
            fail = len(res) - ok
            await m.reply(f"Join: {ok} ok / {fail} fail")
            await app.log.event(
                f"▣ ᴠᴄ ᴊᴏɪɴ\n  chat: {chat}\n"
                f"  ok: {ok} | fail: {fail}\n  by: {uid}"
            )

        elif state == "vc:leave":
            chat = _chat(text)
            res = await app.calls.leave(chat)
            ok = sum(1 for v in res.values() if v == "ok")
            await m.reply(f"Leave: {ok} ok / {len(res) - ok} fail")

        elif state == "intx:rx":
            parts = text.split()
            if len(parts) < 2:
                app.nav.set(uid, state)
                return await m.reply("Format: <post_url> <emoji>")
            from archvc.intx import react
            res = await react.burst(app.herd, parts[0], parts[1])
            await m.reply(f"Reactions: {res['ok']} ok / {res['fail']} fail")

        elif state == "intx:views":
            parts = text.split()
            if len(parts) < 2:
                app.nav.set(uid, state)
                return await m.reply("Format: <post_url> <count> [emoji]")
            from archvc.intx import views
            try:
                n = int(parts[1])
            except ValueError:
                app.nav.set(uid, state)
                return await m.reply("Bad count.")
            emoji = parts[2] if len(parts) > 2 else None
            res = await views.boost(app.herd, parts[0], n, react=emoji)
            await m.reply(f"Views: {res['ok']} ok / {res['fail']} fail")


def _phone(s: str) -> bool:
    return s.startswith("+") and s[1:].isdigit() and 8 <= len(s) - 1 <= 15


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

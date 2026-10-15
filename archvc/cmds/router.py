from pyrogram import filters


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.private & filters.text, group=1)
    async def _input(_, m):
        uid = m.from_user.id
        text = (m.text or "").strip()
        if text.startswith("/"):
            return

        # login flow
        if app.login.active(uid):
            res = await app.login.feed(uid, text)
            if res:
                await m.reply(res)
            return

        # generate flow
        if app.generate.active(uid):
            res = await app.generate.feed(uid, text)
            if res:
                await m.reply(res)
            return

        state = app.nav.peek(uid)
        if not state:
            return
        app.nav.take(uid)

        from archvc.acct import scope as _sc

        if state == "acc:session":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            await m.reply(await app.login.import_(uid, text, scope=sp))

        elif state == "sd:add":
            if not app.sudo.is_owner(uid):
                return
            try:
                tg = int(text.strip())
            except ValueError:
                app.nav.set(uid, state)
                return await m.reply("Bad id.")
            added = await app.sudo.add(tg, by=uid)
            if not added:
                return await m.reply("Already owner or sudo: " + str(tg))
            await app.log.event(
                "SUDO ADDED\n  id: " + str(tg) + "\n  by: " + str(uid)
            )
            try:
                await app.bot.send_message(
                    tg,
                    "You've been added as sudo.\nSend /start to open menu.",
                )
            except Exception:
                pass
            await m.reply("Added sudo: " + str(tg))

        elif state == "sd:rm":
            if not app.sudo.is_owner(uid):
                return
            try:
                tg = int(text.strip())
            except ValueError:
                app.nav.set(uid, state)
                return await m.reply("Bad id.")
            ok = await app.sudo.drop(tg)
            if not ok:
                return await m.reply("Can't remove: " + str(tg))
            await app.log.event(
                "SUDO REMOVED\n  id: " + str(tg) + "\n  by: " + str(uid)
            )
            await m.reply("Removed sudo: " + str(tg))

        elif state == "vc:join":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat_input = text.strip()
            await m.reply("checking...")
            h = await app.calls.precheck(app.bot, chat_input)
            if h.get("error"):
                return await m.reply(
                    "Cannot join\nchat: " + chat_input + "\n" + str(h["error"])
                )
            await m.reply("Joining " + str(h.get("id")) + "...")
            res = await app.calls.join_scoped(chat_input, sp)
            ok = sum(1 for v in res.values() if v == "ok")
            fail = len(res) - ok
            body = "Join: " + str(ok) + " ok / " + str(fail) + " fail"
            errs = {}
            for v in res.values():
                if v.startswith("fail:"):
                    errs[v[5:]] = errs.get(v[5:], 0) + 1
            for e, n in list(errs.items())[:3]:
                body = body + "\n  " + str(n) + "x  " + e[:150]
            await m.reply(body)
            await app.log.event(
                "VC JOIN\n  chat: " + str(h.get("id") or chat_input)
                + "\n  ok: " + str(ok) + " | fail: " + str(fail)
                + "\n  by: " + str(uid)
            )

        elif state == "vc:leave":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            res = await app.calls.leave_scoped(text.strip(), sp)
            ok = sum(1 for v in res.values() if v == "ok")
            await m.reply(
                "Leave: " + str(ok) + " ok / " + str(len(res) - ok) + " fail"
            )

        elif state == "vc:mute":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            await app.calls.mute_scoped(text.strip(), sp)
            await m.reply("Muted.")

        elif state == "vc:unmute":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            await app.calls.unmute_scoped(text.strip(), sp)
            await m.reply("Unmuted.")

        elif state == "vc:pause":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            await app.calls.pause_scoped(text.strip(), sp)
            await m.reply("Paused.")

        elif state == "vc:play":
            from archvc.vc import media
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                app.nav.set(uid, "vc:play")
                return await m.reply("Format: chat source")
            chat = parts[0].strip()
            try:
                url = await media.resolve_async(parts[1].strip())
            except Exception as e:
                return await m.reply("Resolve failed: " + str(e))
            res = await app.calls.play_all_scoped(chat, url, sp)
            ok = sum(1 for v in res.values() if v == "ok")
            await m.reply(
                "Play: " + str(ok) + " ok / " + str(len(res) - ok) + " fail"
            )

        elif state == "vcrt:chat":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            sm = getattr(app.calls.herd, "scope", {})
            present = sum(
                1 for a in app.calls.live
                if sm.get(a) == sp and chat in app.calls.joined.get(a, set())
            )
            total = sum(1 for a in app.calls.live if sm.get(a) == sp)
            await m.reply("accounts: " + str(present) + "/" + str(total) + " in VC")
            res = await app.vcreactor.start(sp, chat)
            if res == "started":
                await m.reply(
                    "VC RT LOOP ON\n"
                    "  chat: " + str(chat) + "\n"
                    "  interval: 90s\n"
                    "  /vcrt off to stop"
                )
            else:
                await m.reply("start failed: " + str(res))

        elif state == "intx:rx":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            from archvc.intx import react
            parts = text.split()
            if len(parts) < 1:
                app.nav.set(uid, state)
                return await m.reply("Format: post_url [emoji]")
            url = parts[0]
            emoji = parts[1] if len(parts) > 1 else None
            SAFE = ["👍", "❤️", "🔥", "🎉", "👏", "😁", "🥰", "🤔", "🙏"]
            if emoji and emoji not in SAFE:
                return await m.reply("Emoji not allowed. Safe set: " + " ".join(SAFE))
            if emoji:
                res = await react.burst_scoped(app, url, emoji, sp)
            else:
                res = await react.random_burst_scoped(app, url, SAFE, sp)
            await m.reply("Reactions: " + str(res["ok"]) + " ok / " + str(res["fail"]) + " fail")

        elif state == "intx:views":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            from archvc.intx import views
            parts = text.split()
            if len(parts) < 2:
                app.nav.set(uid, state)
                return await m.reply("Format: post_url count")
            url = parts[0]
            try:
                n = int(parts[1])
            except ValueError:
                app.nav.set(uid, state)
                return await m.reply("Bad count.")
            res = await views.boost_scoped(app, url, n, sp)
            await m.reply("Views: " + str(res["ok"]) + " ok / " + str(res["fail"]) + " fail")

        elif state == "views:manual":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            from archvc.intx import views
            url = text.strip()
            await m.reply("Boosting... (2-5 min)")
            res = await views.boost_scoped(app, url, 40, sp)
            await m.reply("Views: " + str(res["ok"]) + " ok / " + str(res["fail"]) + " fail")

        elif state == "views:auto":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            try:
                from pyrogram.enums import ChatMemberStatus
                me = await app.bot.get_me()
                member = await app.bot.get_chat_member(chat, me.id)
                if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                    return await m.reply("Bot not admin in: " + str(chat))
            except Exception as e:
                return await m.reply("Cannot check: " + str(e))
            await app.postwatch.add(sp, chat)
            await m.reply(
                "AutoView ON\n"
                "  channel: " + str(chat) + "\n"
                "  watching for new posts"
            )

        elif state == "aj:add":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            n = app.watchdog.watch_chat(sp, chat)
            await m.reply(
                "AutoJoin ON\n  chat: " + str(chat) + "\n  watching: " + str(n)
            )

        elif state == "aj:rm":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            ok = app.watchdog.unwatch(sp, chat)
            await m.reply("removed: " + str(chat) if ok else "not watching: " + str(chat))

        elif state == "ar:add":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            if not await app.autojoin.is_allowed(sp, chat):
                await app.autojoin.allow(sp, chat)
            res = await app.autojoin.start(sp, chat)
            if res == "started":
                await m.reply("AutoReact ON\n  chat: " + str(chat) + "\n  interval: 60s")
            else:
                await m.reply(str(res))

        elif state == "ar:allow":
            sp = await _sc.resolve(app, uid)
            if not sp:
                return await m.reply("Not authorized.")
            chat = _chat(text)
            added = await app.autojoin.allow(sp, chat)
            await m.reply(
                "allowed: " + str(chat) if added else "already allowed: " + str(chat)
            )

        elif state == "px:add":
            from archvc.prox.fleet import _row
            r = _row(text)
            if not r:
                app.nav.set(uid, state)
                return await m.reply("Bad proxy URL.")
            await app.db.proxies.update_one(
                {"pid": r["pid"]},
                {
                    "$set": {"url": r["url"], "kind": r["kind"], "secret": r["secret"]},
                    "$setOnInsert": {"health": "unknown", "lent": [], "checked": None},
                },
                upsert=True,
            )
            await app.fleet.stats(force=True)
            await m.reply("Added proxy: " + r["pid"])


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

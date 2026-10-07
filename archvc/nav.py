import asyncio

from pyrogram import filters
from pyrogram.errors import MessageNotModified

from archvc import kbd

ROOT = """◈ ᴀʀᴄʜ
ᴠᴄ ᴀꜱꜱɪꜱᴛᴀɴᴛ
━━━━━━━━━━━━━━━━━━━━

  🟢  {accounts} ᴀᴄᴄᴏᴜɴᴛꜱ
  🌐  {proxies} ᴘʀᴏxɪᴇꜱ
  🎙  {sessions} ꜱᴇꜱꜱɪᴏɴꜱ

━━━━━━━━━━━━━━━━━━━━
{role}"""

ACC = """◈ ᴀᴄᴄᴏᴜɴᴛꜱ
━━━━━━━━━━━━━━━━━━━━

  🟢  {up} ᴏɴʟɪɴᴇ
  🔴  {sick} ꜱɪᴄᴋ
  ⚪  {off} ᴏꜰꜰ

━━━━━━━━━━━━━━━━━━━━
ᴛᴏᴛᴀʟ  {total}"""

VC = """◈ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ
━━━━━━━━━━━━━━━━━━━━

  🎙  ᴀᴄᴛɪᴠᴇ: {active}
  👥  ɪɴ ᴠᴄ: {joined}

━━━━━━━━━━━━━━━━━━━━
ᴄʜᴀᴛ: {chat}"""

INTX = """◈ ɪɴᴛᴇʀᴀᴄᴛɪᴏɴ
━━━━━━━━━━━━━━━━━━━━

  🔥  ʀᴇᴀᴄᴛɪᴏɴꜱ  ·  ᴇᴍᴏᴊɪ ᴏɴ ᴘᴏꜱᴛ
  👁  ᴠɪᴇᴡꜱ     ·  ᴘᴏꜱᴛ ᴠɪᴇᴡ ʙᴏᴏꜱᴛ

━━━━━━━━━━━━━━━━━━━━
ꜱᴇɴᴅ ᴀ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ /rx /views"""

PROXY = """◈ ᴘʀᴏxʏ ꜰʟᴇᴇᴛ
━━━━━━━━━━━━━━━━━━━━

  🟢  {up} ᴀʟɪᴠᴇ
  🔴  {down} ᴅᴇᴀᴅ
  ⚪  {unknown} ᴜɴᴋɴᴏᴡɴ

  🌐  ꜰᴀᴋᴇᴛʟꜱ  {fake_tls}
  🔵  ᴍᴛᴘʀᴏᴛᴏ  {mtproto}

━━━━━━━━━━━━━━━━━━━━
ᴛᴏᴛᴀʟ  {total}"""

SYS = """✦ ꜱʏꜱᴛᴇᴍ
━━━━━━━━━━━━━━━━━━━━

  ᴀᴄᴄᴏᴜɴᴛꜱ    {up} ok  ·  {sick} ꜱɪᴄᴋ
  ᴘʀᴏxɪᴇꜱ      {px_live} alive · {px_total} ᴛᴏᴛᴀʟ
  ᴠᴄ ꜱᴇꜱꜱɪᴏɴꜱ  {sessions}

━━━━━━━━━━━━━━━━━━━━"""


class Nav:
    def __init__(self) -> None:
        self.state: dict[int, str] = {}

    def set(self, uid: int, state: str) -> None:
        self.state[uid] = state

    def take(self, uid: int) -> str | None:
        return self.state.pop(uid, None)

    def peek(self, uid: int) -> str | None:
        return self.state.get(uid)


async def _edit(cb, text: str, markup) -> None:
    try:
        await cb.edit_message_text(text, reply_markup=markup)
    except MessageNotModified:
        pass


def mount(app) -> None:
    bot = app.bot
    nav = Nav()
    app.nav = nav

    @bot.on_callback_query(filters.regex(f"^{kbd.NS}"))
    async def _route(_, cb):
        uid = cb.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await cb.answer("not authorized", show_alert=False)

        data = cb.data[len(kbd.NS):]
        asyncio.create_task(_safe_answer(cb))
        owner = app.sudo.is_owner(uid)

        if data == "nav:root":
            nav.state.pop(uid, None)
            s = await app.fleet.stats()
            await _edit(cb, ROOT.format(
                accounts=app.herd.size,
                proxies=s["up"],
                sessions=app.calls.count() if app.calls else 0,
                role="ᴏᴡɴᴇʀ" if owner else "ꜱᴜᴅᴏ",
            ), kbd.root(owner))

        elif data == "nav:acc":
            nav.state.pop(uid, None)
            await _edit(cb, await _acc_text(app), kbd.accounts())

        elif data == "nav:vc":
            nav.state.pop(uid, None)
            await _edit(cb, await _vc_text(app), kbd.voice())

        elif data == "nav:intx":
            nav.state.pop(uid, None)
            await _edit(cb, INTX, kbd.interaction())

        elif data == "nav:px":
            nav.state.pop(uid, None)
            await _edit(cb, await _px_text(app), kbd.proxy())

        elif data == "nav:sys":
            nav.state.pop(uid, None)
            await _edit(cb, await _sys_text(app), kbd.system(owner))

        elif data == "nav:sd" and owner:
            nav.state.pop(uid, None)
            await _edit(
                cb,
                "👥 ꜱᴜᴅᴏ\n━━━━━━━━━━━━━━━━━━━━",
                kbd.sudo(),
            )

        elif data == "px:refresh":
            await _edit(
                cb,
                "🔄 ʀᴇꜰʀᴇꜱʜɪɴɢ...\n━━━━━━━━━━━━━━━━━━━━",
                kbd.back("px"),
            )
            await app.fleet.refresh()
            await _edit(cb, await _px_text(app, force=True), kbd.proxy())

        elif data == "px:check":
            await _edit(
                cb,
                "✅ ᴄʜᴇᴄᴋɪɴɢ...\n━━━━━━━━━━━━━━━━━━━━",
                kbd.back("px"),
            )
            await app.fleet._probe_all()
            await _edit(cb, await _px_text(app, force=True), kbd.proxy())

        elif data == "px:clean":
            n = await app.fleet.clean()
            await _edit(
                cb,
                f"🗑 ᴄʟᴇᴀɴᴇᴅ  {n} ᴅᴇᴀᴅ ᴘʀᴏxɪᴇꜱ\n━━━━━━━━━━━━━━━━━━━━",
                kbd.back("px"),
            )

        elif data == "px:stats":
            await _edit(cb, await _px_text(app), kbd.proxy())

        elif data == "px:list":
            rows = await app.db.proxies.find(
                {}, {"pid": 1, "kind": 1, "health": 1}
            ).sort("health", 1).limit(20).to_list(None)
            lines = ["📋 ᴘʀᴏxʏ ʟɪꜱᴛ", "━━━━━━━━━━━━━━━━━━━━"]
            for r in rows:
                icon = {"up": "🟢", "down": "🔴"}.get(r.get("health"), "⚪")
                kind = "ꜰ" if r.get("kind") == "fake_tls" else "ᴍ"
                lines.append(f"  {icon} {kind}  {r['pid'][:12]}")
            if not rows:
                lines.append("  (none)")
            await _edit(cb, "\n".join(lines), kbd.back("px"))

        elif data == "px:faketls":
            n = await app.db.proxies.count_documents({"kind": "fake_tls"})
            await _edit(
                cb,
                f"🌐 ꜰᴀᴋᴇᴛʟꜱ\n━━━━━━━━━━━━━━━━━━━━\n\n  ᴄᴏᴜɴᴛ: {n}",
                kbd.back("px"),
            )

        elif data == "px:mtproto":
            n = await app.db.proxies.count_documents({"kind": "mtproto"})
            await _edit(
                cb,
                f"🔵 ᴍᴛᴘʀᴏᴛᴏ\n━━━━━━━━━━━━━━━━━━━━\n\n  ᴄᴏᴜɴᴛ: {n}",
                kbd.back("px"),
            )

        elif data == "px:add":
            nav.set(uid, "px:add")
            await _edit(
                cb,
                "➕ ᴀᴅᴅ ᴘʀᴏxʏ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴀ ᴛɢ://ᴘʀᴏxʏ? ʟɪɴᴋ:",
                kbd.back("px"),
            )

        elif data == "nav:acc:add":
            await _edit(
                cb,
                "➕ ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ\n━━━━━━━━━━━━━━━━━━━━\n\nᴄʜᴏᴏꜱᴇ ᴀ ᴍᴇᴛʜᴏᴅ:",
                kbd.accounts(),
            )
        elif data == "acc:add:s":
            nav.set(uid, "acc:session")
            await _edit(
                cb,
                "🔑 ꜱᴇꜱꜱɪᴏɴ ɪᴍᴘᴏʀᴛ\n━━━━━━━━━━━━━━━━━━━━\n\nꜱᴇɴᴅ ᴛʜᴇ ꜱᴇꜱꜱɪᴏɴ ꜱᴛʀɪɴɢ:",
                kbd.back("acc"),
            )
        elif data == "acc:add:o":
            nav.state.pop(uid, None)
            await _edit(
                cb,
                "📱 ᴘʜᴏɴᴇ ʟᴏɢɪɴ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ: <code>/addaccount +91xxxxxxxxxx</code>\n\n"
                "ᴏᴛᴘ ᴡɪʟʟ ᴀʀʀɪᴠᴇ — ꜱᴇɴᴅ ᴀꜱ ɴᴇxᴛ ᴍᴇꜱꜱᴀɢᴇ.",
                kbd.back("acc"),
            )
        elif data == "acc:refresh":
            await _edit(cb, await _acc_text(app), kbd.accounts())

        elif data == "nav:vc:join":
            nav.set(uid, "vc:join")
            await _edit(
                cb,
                "🎙 ᴊᴏɪɴ ᴠᴄ\n━━━━━━━━━━━━━━━━━━━━\n\nꜱᴇɴᴅ ᴄʜᴀᴛ ɪᴅ ᴏʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ:",
                kbd.back("vc"),
            )
        elif data == "nav:vc:leave":
            nav.set(uid, "vc:leave")
            await _edit(
                cb,
                "🔇 ʟᴇᴀᴠᴇ ᴠᴄ\n━━━━━━━━━━━━━━━━━━━━\n\nꜱᴇɴᴅ ᴄʜᴀᴛ ɪᴅ:",
                kbd.back("vc"),
            )
        elif data == "vc:play":
            nav.set(uid, "vc:play")
            await _edit(
                cb,
                "🎵 ᴀᴜᴅɪᴏ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/play &lt;chat&gt; &lt;source&gt;</code>",
                kbd.back("vc"),
            )
        elif data == "nav:intx:rx":
            nav.set(uid, "intx:rx")
            await _edit(
                cb,
                "🔥 ʀᴇᴀᴄᴛɪᴏɴꜱ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/rx &lt;post_url&gt; &lt;emoji&gt;</code>",
                kbd.back("intx"),
            )
        elif data == "nav:intx:views":
            nav.set(uid, "intx:views")
            await _edit(
                cb,
                "👁 ᴠɪᴇᴡꜱ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/views &lt;post_url&gt; &lt;count&gt;</code>",
                kbd.back("intx"),
            )

        elif data == "nav:autojoin":
            nav.state.pop(uid, None)
            await _edit(cb, await _aj_text(app), kbd.autojoin())

        elif data == "nav:autoreact":
            nav.state.pop(uid, None)
            await _edit(cb, await _ar_text(app), kbd.autoreact())

        elif data == "aj:status":
            await _edit(cb, await _aj_text(app), kbd.autojoin())

        elif data == "aj:add":
            nav.set(uid, "aj:add")
            await _edit(
                cb,
                "👁 ᴀᴅᴅ ᴀᴜᴛᴏᴊᴏɪɴ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴛʜᴇ ᴄʜᴀᴛ ɪᴅ:",
                kbd.back("autojoin"),
            )

        elif data == "aj:offall":
            n = app.watchdog.unwatch_all()
            await _edit(
                cb,
                "👁 ᴏꜰꜰ ᴀʟʟ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                f"  ᴅɪꜱᴀʙʟᴇᴅ {n} ᴄʜᴀᴛ(ꜱ)",
                kbd.back("autojoin"),
            )

        elif data == "ar:status":
            await _edit(cb, await _ar_text(app), kbd.autoreact())

        elif data == "ar:add":
            nav.set(uid, "ar:add")
            await _edit(
                cb,
                "⚡ ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏʀᴇᴀᴄᴛ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴛʜᴇ ᴄʜᴀᴛ ɪᴅ:",
                kbd.back("autoreact"),
            )

        elif data == "ar:allow":
            nav.set(uid, "ar:allow")
            await _edit(
                cb,
                "✅ ᴀʟʟᴏᴡ ᴄʜᴀᴛ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴛʜᴇ ᴄʜᴀᴛ ɪᴅ:",
                kbd.back("autoreact"),
            )

        elif data == "ar:offall":
            n = await app.autojoin.stop_all()
            await _edit(
                cb,
                "⚡ ᴏꜰꜰ ᴀʟʟ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                f"  ꜱᴛᴏᴘᴘᴇᴅ {n}",
                kbd.back("autoreact"),
            )

        elif data == "ar:list":
            allowed = await app.autojoin.allowed()
            if not allowed:
                body = "📋 ᴀʟʟᴏᴡᴇᴅ\n━━━━━━━━━━━━━━━━━━━━\n\n  ᴇᴍᴘᴛʏ"
            else:
                lines = ["📋 ᴀʟʟᴏᴡᴇᴅ", "━━━━━━━━━━━━━━━━━━━━"]
                for c in allowed:
                    lines.append(f"  • {c}")
                body = "\n".join(lines)
            await _edit(cb, body, kbd.back("autoreact"))


async def _safe_answer(cb) -> None:
    try:
        await cb.answer()
    except Exception:
        pass


async def _acc_text(app) -> str:
    up = app.herd.size
    sick = app.herd.sick
    off = await app.db.accounts.count_documents({"state": "off"})
    return ACC.format(up=up, sick=sick, off=off, total=up + sick + off)


async def _vc_text(app) -> str:
    active = app.calls.count() if app.calls else 0
    return VC.format(active=active, joined=app.herd.size, chat="—")


async def _px_text(app, force: bool = False) -> str:
    s = await app.fleet.stats(force=force)
    return PROXY.format(**s)


async def _sys_text(app) -> str:
    s = await app.fleet.stats()
    return SYS.format(
        up=app.herd.size,
        sick=app.herd.sick,
        px_live=s["up"],
        px_total=s["total"],
        sessions=app.calls.count() if app.calls else 0,
    )

from pyrogram import filters

from archvc import kbd

ROOT = """◈ ᴀʀᴄʜ
ᴠᴄ ᴀꜱꜱɪꜱᴛᴀɴᴛ
━━━━━━━━━━━━━━━━━━━━

  🟢  {accounts} ᴀᴄᴄᴏᴜɴᴛꜱ ᴏɴʟɪɴᴇ
  🌐  {proxies} ᴘʀᴏxɪᴇꜱ ᴀʟɪᴠᴇ
  🎙  {sessions} ᴠᴄ ꜱᴇꜱꜱɪᴏɴꜱ

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
  🎵  ᴀᴜᴅɪᴏ     ·  ᴀᴜᴅɪᴏ ɪɴ ᴠᴄ

━━━━━━━━━━━━━━━━━━━━
ꜱᴇɴᴅ ᴀ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ /rx /views /play"""

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
        await cb.answer()
        owner = app.sudo.is_owner(uid)

        if data == "nav:root":
            nav.state.pop(uid, None)
            await cb.edit_message_text(
                await _root_text(app, uid),
                reply_markup=kbd.root(owner),
            )
        elif data == "nav:acc":
            nav.state.pop(uid, None)
            await cb.edit_message_text(
                await _acc_text(app),
                reply_markup=kbd.accounts(),
            )
        elif data == "nav:vc":
            nav.state.pop(uid, None)
            await cb.edit_message_text(
                await _vc_text(app),
                reply_markup=kbd.voice(),
            )
        elif data == "nav:intx":
            nav.state.pop(uid, None)
            await cb.edit_message_text(INTX, reply_markup=kbd.interaction())
        elif data == "nav:sys":
            nav.state.pop(uid, None)
            await cb.edit_message_text(
                await _sys_text(app),
                reply_markup=kbd.system(owner),
            )
        elif data == "nav:sd" and owner:
            nav.state.pop(uid, None)
            await cb.edit_message_text(
                "👥 ꜱᴜᴅᴏ\n━━━━━━━━━━━━━━━━━━━━",
                reply_markup=kbd.sudo(),
            )

        elif data == "nav:acc:add":
            await cb.edit_message_text(
                "➕ ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ\n━━━━━━━━━━━━━━━━━━━━\n\nᴄʜᴏᴏꜱᴇ ᴀ ᴍᴇᴛʜᴏᴅ:",
                reply_markup=kbd.accounts(),
            )
        elif data == "acc:add:s":
            nav.set(uid, "acc:session")
            await cb.edit_message_text(
                "🔑 ꜱᴇꜱꜱɪᴏɴ ɪᴍᴘᴏʀᴛ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴛʜᴇ ꜱᴇꜱꜱɪᴏɴ ꜱᴛʀɪɴɢ:",
                reply_markup=kbd.back("acc"),
            )
        elif data == "acc:add:o":
            nav.set(uid, "acc:phone")
            await cb.edit_message_text(
                "📱 ᴘʜᴏɴᴇ + ᴏᴛᴘ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴛʜᴇ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91...):",
                reply_markup=kbd.back("acc"),
            )
        elif data == "acc:refresh":
            await cb.edit_message_text(
                await _acc_text(app),
                reply_markup=kbd.accounts(),
            )

        elif data == "nav:vc:join":
            nav.set(uid, "vc:join")
            await cb.edit_message_text(
                "🎙 ᴊᴏɪɴ ᴠᴄ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴄʜᴀᴛ ɪᴅ ᴏʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ:",
                reply_markup=kbd.back("vc"),
            )
        elif data == "nav:vc:leave":
            nav.set(uid, "vc:leave")
            await cb.edit_message_text(
                "🔇 ʟᴇᴀᴠᴇ ᴠᴄ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜱᴇɴᴅ ᴄʜᴀᴛ ɪᴅ:",
                reply_markup=kbd.back("vc"),
            )
        elif data == "vc:play":
            nav.set(uid, "vc:play")
            await cb.edit_message_text(
                "🎵 ᴀᴜᴅɪᴏ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/play &lt;chat&gt; &lt;source&gt;</code>\n"
                "ꜱᴏᴜʀᴄᴇ: ʏᴛ ʟɪɴᴋ, ᴜʀʟ, ᴏʀ ʟᴏᴄᴀʟ ᴘᴀᴛʜ",
                reply_markup=kbd.back("vc"),
            )

        elif data == "nav:intx:rx":
            nav.set(uid, "intx:rx")
            await cb.edit_message_text(
                "🔥 ʀᴇᴀᴄᴛɪᴏɴꜱ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/rx &lt;post_url&gt; &lt;emoji&gt;</code>",
                reply_markup=kbd.back("intx"),
            )
        elif data == "nav:intx:views":
            nav.set(uid, "intx:views")
            await cb.edit_message_text(
                "👁 ᴠɪᴇᴡꜱ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                "ꜰᴏʀᴍᴀᴛ: <code>/views &lt;post_url&gt; &lt;count&gt; [emoji]</code>",
                reply_markup=kbd.back("intx"),
            )


async def _root_text(app, uid: int) -> str:
    return ROOT.format(
        accounts=app.herd.size,
        proxies=await app.fleet.alive(),
        sessions=app.calls.count() if app.calls else 0,
        role="ᴏᴡɴᴇʀ" if app.sudo.is_owner(uid) else "ꜱᴜᴅᴏ",
    )


async def _acc_text(app) -> str:
    up = app.herd.size
    sick = app.herd.sick
    off = await app.db.accounts.count_documents({"state": "off"})
    return ACC.format(up=up, sick=sick, off=off, total=up + sick + off)


async def _vc_text(app) -> str:
    active = app.calls.count() if app.calls else 0
    return VC.format(active=active, joined=app.herd.size, chat="—")


async def _sys_text(app) -> str:
    px_live = await app.fleet.alive()
    px_total = await app.db.proxies.count_documents({})
    return SYS.format(
        up=app.herd.size,
        sick=app.herd.sick,
        px_live=px_live,
        px_total=px_total,
        sessions=app.calls.count() if app.calls else 0,
    )

from pyrogram import filters

from archvc import kbd


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("start") & filters.private)
    async def _start(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        await m.reply(await _root(app, uid), reply_markup=kbd.root(app.sudo.is_owner(uid)))

    @bot.on_message(filters.command("menu") & filters.private)
    async def _menu(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        await m.reply(await _root(app, uid), reply_markup=kbd.root(app.sudo.is_owner(uid)))


async def _root(app, uid: int) -> str:
    return (
        "◈ ᴀʀᴄʜ\n"
        "ᴠᴄ ᴀꜱꜱɪꜱᴛᴀɴᴛ\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  🟢  {app.herd.size} ᴀᴄᴄᴏᴜɴᴛꜱ ᴏɴʟɪɴᴇ\n"
        f"  🌐  {await app.fleet.alive()} ᴘʀᴏxɪᴇꜱ ᴀʟɪᴠᴇ\n"
        f"  🎙  {app.calls.count() if app.calls else 0} ᴠᴄ ꜱᴇꜱꜱɪᴏɴꜱ\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + ("ᴏᴡɴᴇʀ" if app.sudo.is_owner(uid) else "ꜱᴜᴅᴏ")
    )

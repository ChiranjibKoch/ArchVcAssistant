from pyrogram import filters

from archvc import kbd


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("proxies") & filters.private)
    async def _px(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return
        s = await app.fleet.stats()
        body = (
            f"◈ ᴘʀᴏxʏ ꜰʟᴇᴇᴛ\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"  🟢  {s['up']} ᴀʟɪᴠᴇ\n"
            f"  🔴  {s['down']} ᴅᴇᴀᴅ\n"
            f"  ⚪  {s['unknown']} ᴜɴᴋɴᴏᴡɴ\n\n"
            f"  🌐  ꜰᴀᴋᴇᴛʟꜱ  {s['fake_tls']}\n"
            f"  🔵  ᴍᴛᴘʀᴏᴛᴏ  {s['mtproto']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\nᴛᴏᴛᴀʟ  {s['total']}"
        )
        await m.reply(body, reply_markup=kbd.proxy())

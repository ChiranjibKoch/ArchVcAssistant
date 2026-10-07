from pyrogram import filters

from archvc import kbd
from archvc.gate import deny_msg

WELCOME_VIDEO = "https://telegra.ph/file/36221d40afde82941ffff.mp4"

CAPTION = """◈ ᴀʀᴄʜ
ᴠᴄ ᴀꜱꜱɪꜱᴛᴀɴᴛ
━━━━━━━━━━━━━━━━━━━━

ᴍᴜʟᴛɪ-ᴀᴄᴄᴏᴜɴᴛ ᴛᴇʟᴇɢʀᴀᴍ ᴠᴄ ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ

  🟢  {accounts} ᴀᴄᴄᴏᴜɴᴛꜱ
  🌐  {proxies} ᴘʀᴏxɪᴇꜱ
  🎙  {sessions} ꜱᴇꜱꜱɪᴏɴꜱ

━━━━━━━━━━━━━━━━━━━━
{role}"""


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("start") & filters.private)
    async def _start(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        s = await app.fleet.stats()
        text = CAPTION.format(
            accounts=app.herd.size,
            proxies=s["up"],
            sessions=app.calls.count() if app.calls else 0,
            role="ᴏᴡɴᴇʀ" if app.sudo.is_owner(uid) else "ꜱᴜᴅᴏ",
        )
        await m.reply_video(
            video=WELCOME_VIDEO,
            caption=text,
            reply_markup=kbd.root(app.sudo.is_owner(uid)),
        )

    @bot.on_message(filters.command("menu") & filters.private)
    async def _menu(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        s = await app.fleet.stats()
        text = CAPTION.format(
            accounts=app.herd.size,
            proxies=s["up"],
            sessions=app.calls.count() if app.calls else 0,
            role="ᴏᴡɴᴇʀ" if app.sudo.is_owner(uid) else "ꜱᴜᴅᴏ",
        )
        await m.reply_video(
            video=WELCOME_VIDEO,
            caption=text,
            reply_markup=kbd.root(app.sudo.is_owner(uid)),
        )

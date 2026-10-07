from pyrogram.types import CallbackQuery, Message

DENY_TEXT = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  ⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ

  ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴘʀɪᴠᴀᴛᴇ.
  ᴀꜱᴋ ᴛʜᴇ ᴏᴡɴᴇʀ ꜰᴏʀ ᴀᴄᴄᴇꜱꜱ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""


async def deny_msg(m: Message) -> None:
    try:
        uid = m.from_user.id if m.from_user else 0
        await m.reply(DENY_TEXT.format(uid=uid))
    except Exception:
        pass


async def deny_cb(cb: CallbackQuery) -> None:
    try:
        await cb.answer("⛔ access denied", show_alert=True)
    except Exception:
        pass

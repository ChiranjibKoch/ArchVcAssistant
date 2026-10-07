from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters

from archvc import kbd

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

NEW_REQ = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  📥 ᴀᴄᴄᴇꜱꜱ ʀᴇǫᴜᴇꜱᴛ sᴇɴᴛ

  ᴛʜᴇ ᴏᴡɴᴇʀ ᴡɪʟʟ ʀᴇᴠɪᴇᴡ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ.
  ʏᴏᴜ'ʟʟ ɢᴇᴛ ᴀ ᴍᴇssᴀɢᴇ ᴏɴᴄᴇ ᴀᴘᴘʀᴏᴠᴇᴅ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""

PENDING = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  ⏳ ᴀᴄᴄᴇꜱꜱ ᴘᴇɴᴅɪɴɢ

  ᴡᴀɪᴛɪɴɢ ꜰᴏʀ ᴏᴡɴᴇʀ ᴀᴘᴘʀᴏᴠᴀʟ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""

REJECTED = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  ⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ

  ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""

APPROVED_INFO = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  ✅ ᴀᴄᴄᴇꜱꜱ ɢʀᴀɴᴛᴇᴅ

  ᴛᴇɴᴀɴᴛ: {tenant}
  sᴛᴀᴛᴜs: ᴀᴄᴛɪᴠᴇ

━━━━━━━━━━━━━━━━━━━━
ᴀᴄᴄᴇꜱꜱ ᴛᴏ ꜰᴜʟʟ ꜰᴇᴀᴛᴜʀᴇs ɪs
ᴘᴇɴᴅɪɴɢ — ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ.ᴀ"""

OWNER_MSG = """📥 ᴀᴄᴄᴇꜱꜱ ʀᴇǫᴜᴇꜱᴛ
━━━━━━━━━━━━━━━━━━━━

  👤 ɴᴀᴍᴇ:   {name}
  🆔 ᴜsᴇʀ:   {username}
  🔢 ɪᴅ:     {uid}
  📅 ᴛɪᴍᴇ:   {ts}"""


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("start") & filters.private)
    async def _start(_, m):
        uid = m.from_user.id
        if app.sudo.is_owner(uid) or app.sudo.has(uid):
            return await _show_owner(app, m, uid)
        await _route_tenant(app, m)

    @bot.on_message(filters.command("menu") & filters.private)
    async def _menu(_, m):
        uid = m.from_user.id
        if app.sudo.is_owner(uid) or app.sudo.has(uid):
            return await _show_owner(app, m, uid)
        await _route_tenant(app, m)


async def _route_tenant(app, m) -> None:
    uid = m.from_user.id
    st = await app.tenants.status_of(uid)

    if st == "approved":
        tenant = await app.tenants.tenant_of(uid)
        return await m.reply(APPROVED_INFO.format(tenant=tenant))

    if st == "pending":
        return await m.reply(PENDING.format(uid=uid))

    if st == "rejected":
        return await m.reply(REJECTED.format(uid=uid))

    rec = await app.tenants.request(
        uid,
        m.from_user.username,
        m.from_user.first_name or "",
    )
    await m.reply(NEW_REQ.format(uid=uid))
    await _notify_owners(app, rec, uid)


async def _notify_owners(app, rec, requester_id: int) -> None:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    uname = f"@{rec['username']}" if rec.get("username") else "—"
    text = OWNER_MSG.format(
        name=rec.get("name") or "—",
        username=uname,
        uid=requester_id,
        ts=ts,
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "✔ ᴀᴘᴘʀᴏᴠᴇ",
            callback_data=f"appr:yes:{requester_id}",
            style=ButtonStyle.SUCCESS,
        ),
        InlineKeyboardButton(
            "✘ ʀᴇᴊᴇᴄᴛ",
            callback_data=f"appr:no:{requester_id}",
            style=ButtonStyle.DANGER,
        ),
    ]])
    for owner_id in app.sudo.owners:
        try:
            await app.bot.send_message(owner_id, text, reply_markup=kb)
        except Exception:
            pass


async def _show_owner(app, m, uid: int) -> None:
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

from datetime import datetime, timezone

from pyrogram import filters
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
  ʏᴏᴜ'ʟʟ ɢᴇᴛ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴏɴᴄᴇ ᴀᴘᴘʀᴏᴠᴇᴅ.

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

  ʏᴏᴜʀ ʟᴀꜱᴛ ʀᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ.

  ꜱᴇɴᴅ /start ᴀɢᴀɪɴ ᴛᴏ ʀᴇQᴜᴇꜱᴛ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""

REVOKED = """◈ ᴀʀᴄʜ
━━━━━━━━━━━━━━━━━━━━

  🚫 ᴀᴄᴄᴇꜱꜱ ʀᴇᴠᴏᴋᴇᴅ

  ʏᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴡᴀꜱ ʀᴇᴍᴏᴠᴇᴅ.

  ꜱᴇɴᴅ /start ᴀɢᴀɪɴ ᴛᴏ ʀᴇQᴜᴇꜱᴛ.

━━━━━━━━━━━━━━━━━━━━
ʏᴏᴜʀ ɪᴅ: {uid}"""

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
        await _route(app, m)

    @bot.on_message(filters.command("menu") & filters.private)
    async def _menu(_, m):
        await _route(app, m)


async def _route(app, m) -> None:
    uid = m.from_user.id

    if app.sudo.is_owner(uid):
        return await _show_menu(app, m, uid, "ᴏᴡɴᴇʀ")

    if app.sudo.has(uid):
        return await _show_menu(app, m, uid, "ꜱᴜᴅᴏ")

    t = await app.tenants.get(uid)
    status = (t or {}).get("status", "new")

    if status == "approved":
        role = f"ᴛᴇɴᴀɴᴛ {(t or {}).get('tenant')}"
        return await _show_menu(app, m, uid, role)

    if status == "pending":
        return await m.reply(PENDING.format(uid=uid))

    if status == "rejected":
        await m.reply(REJECTED.format(uid=uid))
        rec = await app.tenants.request(
            uid, m.from_user.username, m.from_user.first_name or ""
        )
        await _notify_owners(app, rec, uid)
        return

    if status == "revoked":
        await m.reply(REVOKED.format(uid=uid))
        rec = await app.tenants.request(
            uid, m.from_user.username, m.from_user.first_name or ""
        )
        await _notify_owners(app, rec, uid)
        return

    rec = await app.tenants.request(
        uid, m.from_user.username, m.from_user.first_name or ""
    )
    await m.reply(NEW_REQ.format(uid=uid))
    await _notify_owners(app, rec, uid)


async def _show_menu(app, m, uid, role: str) -> None:
    from archvc.acct import scope as sc
    sp = await sc.resolve(app, uid)
    live = sc.ids_for(app, sp) if sp else []
    s = await app.fleet.stats()
    text = CAPTION.format(
        accounts=len(live),
        proxies=s["up"],
        sessions=len(live),
        role=role,
    )
    is_owner = app.sudo.is_owner(uid)
    try:
        await m.reply_video(
            video=WELCOME_VIDEO,
            caption=text,
            reply_markup=kbd.root(is_owner),
        )
    except Exception:
        await m.reply(text, reply_markup=kbd.root(is_owner))


async def _notify_owners(app, rec, requester_id: int) -> None:
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
    sent = {}
    for owner_id in app.sudo.owners:
        try:
            msg = await app.bot.send_message(owner_id, text, reply_markup=kb)
            sent[str(owner_id)] = msg.id
            print(f"[approval] sent to owner {owner_id}", flush=True)
        except Exception as e:
            print(f"[approval] FAIL owner {owner_id}: {type(e).__name__}: {e}", flush=True)
    if sent:
        await app.tenants.attach_messages(requester_id, sent)

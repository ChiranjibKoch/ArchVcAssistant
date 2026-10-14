from pyrogram import filters
from pyrogram.enums import ParseMode

from archvc.gate import deny_msg
from archvc.intx import vcreact as vcreact_mod


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("vcrt") & filters.private)
    async def _vcrt(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "Usage: /vcrt <chat_id>\n"
                "Auto-joins assistants, sends one VC reaction\n"
                "per account (3-5s apart, random safe emoji)."
            )
        chat = _chat(parts[1])
        await _do(app, m, chat)

    @bot.on_message(filters.command("allow") & filters.private)
    async def _allow(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            allowed = await app.autojoin.allowed()
            if not allowed:
                return await m.reply("Allowed list empty. /allow <chat_id>")
            return await m.reply(
                "\n".join(["✅ ᴀʟʟᴏᴡᴇᴅ"] + [f"  • {c}" for c in allowed])
            )
        chat = _chat(parts[1])
        added = await app.autojoin.allow(chat)
        await m.reply(f"✅ allowed: {chat}" if added else f"already allowed: {chat}")

    @bot.on_message(filters.command("disallow") & filters.private)
    async def _disallow(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply("Usage: /disallow <chat_id>")
        chat = _chat(parts[1])
        removed = await app.autojoin.disallow(chat)
        await m.reply(f"removed: {chat}" if removed else f"not in list: {chat}")

    @bot.on_message(filters.command("autoreact") & filters.private)
    async def _auto(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()

        if len(parts) < 2:
            st = app.autojoin.status()
            if not st:
                return await m.reply(
                    "⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ɴᴏ ᴄʜᴀᴛꜱ ʀᴜɴɴɪɴɢ\n\n"
                    "  /autoreact <chat>   ᴏɴ\n"
                    "  /autoreact off      ꜱᴛᴏᴘ ᴀʟʟ"
                )
            lines = ["⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ", "━━━━━━━━━━━━━━━━━━━━"]
            for c, cfg in st.items():
                lines.append(f"  {c}")
                lines.append(f"    every {cfg['interval']}s · batch {cfg['batch']}")
            lines.append("")
            lines.append("  /autoreact off   ꜱᴛᴏᴘ ᴀʟʟ")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = await app.autojoin.stop_all()
                return await m.reply(f"stopped {n} autoreact(s)")
            chat = _chat(parts[2])
            await app.autojoin.stop(chat)
            return await m.reply(f"stopped: {chat}")

        chat = _chat(parts[1])
        if not await app.autojoin.is_allowed(chat):
            await app.autojoin.allow(chat)
        res = await app.autojoin.start(chat)
        if res == "started":
            await m.reply(
                "⚡ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏɴ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"  chat:     {chat}\n"
                "  interval: 60s\n"
                "  batch:    15 accounts"
            )
        else:
            await m.reply(res)


async def _do(app, m, chat):
    present = sum(
        1 for a in app.calls.live
        if chat in app.calls.joined.get(a, set())
    )
    total = len(app.calls.live)
    missing = total - present
    status = f"👥 accounts: {present}/{total} in VC"
    if missing > 0:
        status += f"\n  joining {missing}..."
    await m.reply(status)

    res = await vcreact_mod.one_shot(app.calls, chat, log=app.log)

    body = (
        "▣ ᴠᴄ ʀᴇᴀᴄᴛɪᴏɴ\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"  chat:     {chat}\n"
        f"  already:  {res.get('already', 0)}\n"
        f"  joined:   {res.get('joined', 0)}\n"
        f"  present:  {res.get('present', 0)}\n"
        f"  reacted:  {res['ok']}\n"
        f"  skipped:  {res.get('skipped', 0)}\n"
        f"  failed:   {res['fail']}"
    )
    errs = res.get("errors") or {}
    for k, v in list(errs.items())[:3]:
        body += f"\n  {v}x {k[:100]}"
    await m.reply(body, parse_mode=ParseMode.DISABLED)

    await app.log.event(
        f"▣ ᴠᴄ ʀᴇᴀᴄᴛɪᴏɴ\n  chat: {chat}\n"
        f"  present: {res.get('present', 0)}\n"
        f"  reacted: {res['ok']}\n"
        f"  skipped: {res.get('skipped', 0)}\n"
        f"  by: {m.from_user.id}"
    )


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("watch") & filters.private)
    async def _watch(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()

        if len(parts) < 2:
            chans = app.postwatch.list_all()
            if not chans:
                return await m.reply(
                    "👁 ᴀᴜᴛᴏᴘᴏꜱᴛ\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "  ɴᴏ ᴄʜᴀɴɴᴇʟꜱ ᴡᴀᴛᴄʜᴇᴅ\n\n"
                    "  /watch <channel_id>\n"
                    "  /watch off"
                )
            lines = ["👁 ᴀᴜᴛᴏᴘᴏꜱᴛ", "━━━━━━━━━━━━━━━━━━━━"]
            for c, cfg in chans.items():
                lines.append(f"  {c}")
                lines.append(f"    react {cfg['react_count']} · view {cfg['view_count']}")
            lines.append("")
            lines.append("  /watch off   ꜱᴛᴏᴘ ᴀʟʟ")
            return await m.reply("\n".join(lines))

        if parts[1] == "off":
            if len(parts) < 3:
                n = await app.postwatch.remove_all()
                return await m.reply(f"stopped {n} watch(es)")
            chat = _chat(parts[2])
            r = await app.postwatch.remove(chat)
            return await m.reply(f"stopped: {chat}" if r else f"not watching: {chat}")

        chat = _chat(parts[1])

        try:
            me = await app.bot.get_me()
            member = await app.bot.get_chat_member(chat, me.id)
            st = member.status
            if st not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                return await m.reply(
                    f"⛔ ʙᴏᴛ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ {chat}\n"
                    "  ᴀᴅᴅ ʙᴏᴛ ᴀꜱ ᴀᴅᴍɪɴ ꜰɪʀꜱᴛ."
                )
        except Exception as e:
            return await m.reply(f"❌ ᴄᴀɴ'ᴛ ᴄʜᴇᴄᴋ {chat}\n  {e}")

        await app.postwatch.add(chat)
        await m.reply(
            "👁 ᴀᴜᴛᴏᴘᴏꜱᴛ ᴏɴ\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"  channel:  {chat}\n"
            "  reactions: 30 per post\n"
            "  views:    100 per post\n"
            "  ᴡᴀᴛᴄʜɪɴɢ ꜰᴏʀ ɴᴇᴡ ᴘᴏꜱᴛꜱ"
        )

    @bot.on_message(filters.channel)
    async def _new_post(_, m):
        try:
            chat_id = m.chat.id if m.chat else None
            if not chat_id:
                return
            if not app.postwatch.active(chat_id):
                return
            if not m.id:
                return
            if getattr(m, "edit_date", None):
                return
            if getattr(m, "empty", False):
                return
            print(f"[postwatch] new post chat={chat_id} msg={m.id}", flush=True)
            asyncio.create_task(app.postwatch.on_post(chat_id, m.id))
        except Exception as e:
            print(f"[postwatch] handler error: {e}", flush=True)


def _chat(s: str):
    try:
        return int(s)
    except ValueError:
        return s

from pyrogram.enums import ChatMemberStatus

from archvc.vc import chat as chat_parser

ADMIN_STATES = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


async def _resolve(bot, chat):
    kind, value = chat_parser.parse(chat)
    if not kind:
        return None, "bad chat input"
    try:
        if kind == "invite":
            info = await bot.get_chat(f"https://t.me/+{value}")
        elif kind == "username":
            info = await bot.get_chat(f"@{value}")
        else:
            info = await bot.get_chat(value)
        return info, None
    except Exception as e:
        return None, f"resolve: {type(e).__name__}: {str(e)[:120]}"


async def check(bot, chat) -> dict:
    out = {"chat": chat, "id": None, "admin": False, "active": False,
           "not_empty": False, "error": None}

    info, err = await _resolve(bot, chat)
    if err:
        out["error"] = err
        return out

    out["id"] = info.id

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(info.id, me.id)
        out["admin"] = member.status in ADMIN_STATES
    except Exception as e:
        out["error"] = f"admin check: {type(e).__name__}: {str(e)[:100]}"
        return out

    if not out["admin"]:
        out["error"] = "bot is not an admin in this chat"
        return out

    out["active"] = bool(getattr(info, "call_active", False))
    out["not_empty"] = bool(getattr(info, "call_not_empty", False))
    if not out["active"]:
        out["error"] = "no active voice chat in this chat"

    return out

from pyrogram.enums import ChatMemberStatus

ADMIN_STATES = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


async def bot_admin_status(bot, chat) -> tuple:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat, me.id)
        is_admin = member.status in ADMIN_STATES
        can_manage = bool(getattr(member, "can_manage_voice_chats", False))
        return is_admin, can_manage, None
    except Exception as e:
        return False, False, f"{type(e).__name__}: {str(e)[:120]}"


async def call_active(bot, chat) -> tuple:
    try:
        info = await bot.get_chat(chat)
        active = bool(getattr(info, "call_active", False))
        not_empty = bool(getattr(info, "call_not_empty", False))
        return active, not_empty, None
    except Exception as e:
        return False, False, f"{type(e).__name__}: {str(e)[:120]}"


async def check(bot, chat) -> dict:
    out = {"chat": chat, "admin": False, "can_manage": False,
           "active": False, "not_empty": False, "error": None}

    is_admin, can_manage, err = await bot_admin_status(bot, chat)
    out["admin"] = is_admin
    out["can_manage"] = can_manage
    if err:
        out["error"] = err
        return out

    if not is_admin:
        out["error"] = "bot is not an admin in this chat"
        return out

    active, not_empty, err2 = await call_active(bot, chat)
    out["active"] = active
    out["not_empty"] = not_empty
    if err2:
        out["error"] = err2
    elif not active:
        out["error"] = "no active voice chat in this chat"

    return out

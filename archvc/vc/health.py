from pyrogram.enums import ChatMemberStatus

from archvc.vc import chat as chat_parser

ADMIN_STATES = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


def pick_client(calls):
    for aid, c in calls.clients.items():
        return c
    return None


async def check_via_client(client, chat) -> dict:
    out = {"chat": chat, "id": None, "active": False,
           "not_empty": False, "error": None}

    kind, value = chat_parser.parse(chat)
    if not kind:
        out["error"] = "bad chat input"
        return out

    arg = chat_parser.to_link(kind, value)

    # try resolve
    try:
        info = await client.get_chat(arg)
    except Exception as e:
        # try join first
        try:
            info = await client.join_chat(arg)
        except Exception as e2:
            msg = str(e2).lower()
            if "already" in msg:
                try:
                    info = await client.get_chat(arg)
                except Exception as e3:
                    out["error"] = f"resolve: {type(e3).__name__}: {str(e3)[:120]}"
                    return out
            else:
                out["error"] = f"resolve: {type(e2).__name__}: {str(e2)[:120]}"
                return out

    out["id"] = info.id
    out["active"] = bool(getattr(info, "call_active", False))
    out["not_empty"] = bool(getattr(info, "call_not_empty", False))

    if not out["active"]:
        out["error"] = "no active voice chat in this chat"

    return out


async def check(calls, chat) -> dict:
    """Precheck via assistant client (bot not needed)."""
    client = pick_client(calls)
    if client is None:
        return {"chat": chat, "error": "no assistant accounts loaded", "id": None}
    return await check_via_client(client, chat)

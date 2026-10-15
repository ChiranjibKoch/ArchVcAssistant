from pyrogram.enums import ChatMemberStatus

from archvc.vc import chat as chat_parser

ADMIN_STATES = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


def pick_client(calls):
    for aid, c in calls.clients.items():
        return c
    return None


async def check_via_client(client, chat) -> dict:
    from pyrogram.raw.functions.channels import GetFullChannel
    from pyrogram.raw.functions.messages import GetFullChat
    from pyrogram.raw.types import InputChannel, InputPeerChannel, InputPeerChat

    out = {"chat": chat, "id": None, "active": False,
           "not_empty": False, "error": None}

    kind, value = chat_parser.parse(chat)
    if not kind:
        out["error"] = "bad chat input"
        return out

    arg = chat_parser.to_link(kind, value)

    # resolve peer
    try:
        peer = await client.resolve_peer(arg)
    except Exception as e:
        # try join
        try:
            await client.join_chat(arg)
            peer = await client.resolve_peer(arg)
        except Exception as e2:
            msg = str(e2).lower()
            if "already" in msg:
                try:
                    peer = await client.resolve_peer(arg)
                except Exception as e3:
                    out["error"] = f"resolve: {type(e3).__name__}: {str(e3)[:120]}"
                    return out
            else:
                out["error"] = f"resolve: {type(e2).__name__}: {str(e2)[:120]}"
                return out

    out["id"] = getattr(peer, "channel_id", None) or getattr(peer, "chat_id", None)

    # raw full chat to get call
    call = None
    try:
        if isinstance(peer, InputPeerChannel):
            full = await client.invoke(
                GetFullChannel(
                    channel=InputChannel(
                        channel_id=peer.channel_id,
                        access_hash=peer.access_hash,
                    )
                )
            )
            call = getattr(full.full_chat, "call", None)
        elif isinstance(peer, InputPeerChat):
            full = await client.invoke(GetFullChat(chat_id=peer.chat_id))
            call = getattr(full.full_chat, "call", None)
    except Exception as e:
        out["error"] = f"full_chat: {type(e).__name__}: {str(e)[:120]}"
        return out

    if call is None:
        out["error"] = "no active voice chat in this chat"
        return out

    out["active"] = True
    return out


async def check(calls, chat) -> dict:
    """Precheck via assistant client (bot not needed)."""
    client = pick_client(calls)
    if client is None:
        return {"chat": chat, "error": "no assistant accounts loaded", "id": None}
    return await check_via_client(client, chat)

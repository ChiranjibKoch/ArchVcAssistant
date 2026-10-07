import asyncio
import random

from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.phone import SendGroupCallMessage
from pyrogram.raw.types import (
    InputChannel,
    InputPeerChannel,
    InputPeerChat,
    TextWithEntities,
)


async def resolve_input_call(client, chat):
    peer = await client.resolve_peer(chat)

    if isinstance(peer, InputPeerChannel):
        full = await client.invoke(
            GetFullChannel(
                channel=InputChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                )
            )
        )
        return full.full_chat.call

    if isinstance(peer, InputPeerChat):
        full = await client.invoke(GetFullChat(chat_id=peer.chat_id))
        return full.full_chat.call

    return None


async def burst(accounts, chat, emoji, limit=None, cache=None):
    clients = list(accounts.live.values())
    if limit:
        clients = clients[:limit]
    ok = 0
    fail = 0

    async def one(aid, c):
        nonlocal ok, fail
        try:
            call = None
            if cache is not None:
                call = cache.get(aid)
            if call is None:
                call = await resolve_input_call(c, chat)
                if cache is not None and call is not None:
                    cache[aid] = call
            if call is None:
                fail += 1
                return
            await c.invoke(
                SendGroupCallMessage(
                    call=call,
                    random_id=random.randint(-2**63, 2**63 - 1),
                    message=TextWithEntities(text=emoji, entities=[]),
                )
            )
            ok += 1
        except Exception:
            fail += 1

    items = [(aid, c) for aid, c in accounts.live.items()]
    if limit:
        items = items[:limit]
    await asyncio.gather(*(one(aid, c) for aid, c in items))
    return {"ok": ok, "fail": fail}


async def send_one(client, input_call, emoji):
    await client.invoke(
        SendGroupCallMessage(
            call=input_call,
            random_id=random.randint(-2**63, 2**63 - 1),
            message=TextWithEntities(text=emoji, entities=[]),
        )
    )

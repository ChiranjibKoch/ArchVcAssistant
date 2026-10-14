import asyncio
import random
import time

from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.phone import SendGroupCallMessage
from pyrogram.raw.types import (
    InputChannel,
    InputPeerChannel,
    InputPeerChat,
    TextWithEntities,
)

COOLDOWN_SEC = 30
SAFE_VC_EMOJIS = ["🔥", "❤️", "👍", "🎉", "👏", "😁", "🥰", "🤔", "🙏", "💯", "⚡"]


def _is_already(exc: Exception) -> bool:
    s = str(exc).lower()
    n = type(exc).__name__.lower()
    return (
        "already" in s
        or "alreadyjoined" in n
        or "groupcallalreadyjoined" in n
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


async def send_one(client, input_call, emoji):
    await client.invoke(
        SendGroupCallMessage(
            call=input_call,
            random_id=random.randint(-2**63, 2**63 - 1),
            message=TextWithEntities(text=emoji, entities=[]),
        )
    )


async def burst(accounts, chat, emoji, limit=None, cache=None):
    items = list(accounts.live.items())
    if limit:
        items = items[:limit]
    ok = 0
    fail = 0
    last_err = None

    async def one(aid, c):
        nonlocal ok, fail, last_err
        try:
            call = None
            if cache is not None:
                call = cache.get((chat, aid))
            if call is None:
                call = await resolve_input_call(c, chat)
                if cache is not None and call is not None:
                    cache[(chat, aid)] = call
            if call is None:
                fail += 1
                last_err = "resolve returned None"
                return
            await send_one(c, call, emoji)
            ok += 1
        except Exception as e:
            fail += 1
            last_err = f"{type(e).__name__}: {str(e)[:150]}"
            print(f"[vcreact] {aid}: {last_err}", flush=True)

    await asyncio.gather(*(one(aid, c) for aid, c in items))
    return {"ok": ok, "fail": fail, "last_err": last_err}


async def one_shot(calls, chat, log=None, emojis=None):
    pool = emojis or SAFE_VC_EMOJIS
    all_aids = list(calls.live.keys())

    already = [a for a in all_aids if chat in calls.joined.get(a, set())]
    need_join = [a for a in all_aids if a not in already]

    print(
        f"[vcreact] chat={chat} total={len(all_aids)} "
        f"already={len(already)} need_join={len(need_join)}",
        flush=True,
    )

    joined_now = 0
    join_fail = 0
    if need_join:
        jobs = [(aid, _wrap_join(calls, aid, chat)) for aid in need_join]
        jres = await calls.q.fire(jobs)
        for aid, v in jres.items():
            if v == "ok" or "already" in v.lower():
                joined_now += 1
                calls.joined.setdefault(aid, set()).add(chat)
            else:
                join_fail += 1
                print(f"[vcreact] join fail {aid}: {v[:100]}", flush=True)

    present = [a for a in all_aids if chat in calls.joined.get(a, set())]
    if not present:
        return {
            "ok": 0, "fail": 0, "skipped": 0,
            "joined": 0, "join_fail": join_fail,
            "already": len(already), "present": 0,
            "error": "no accounts in VC",
        }

    if getattr(calls, "_cooldown", None) is None:
        calls._cooldown = {}
    cooldown = calls._cooldown

    ok = 0
    fail = 0
    skipped = 0
    errs = {}
    now = time.monotonic()

    async def one(aid):
        nonlocal ok, fail, skipped
        last = cooldown.get((chat, aid), 0)
        if now - last < COOLDOWN_SEC:
            skipped += 1
            return
        client = calls.clients.get(aid)
        if not client:
            fail += 1
            return
        emoji = random.choice(pool)
        try:
            input_call = calls.input_calls.get((chat, aid))
            if input_call is None:
                input_call = await resolve_input_call(client, chat)
                if input_call is None:
                    fail += 1
                    return
                calls.input_calls[(chat, aid)] = input_call
            await send_one(client, input_call, emoji)
            ok += 1
            cooldown[(chat, aid)] = time.monotonic()
        except Exception as e:
            if _is_already(e):
                ok += 1
                return
            fail += 1
            k = f"{type(e).__name__}: {str(e)[:80]}"
            errs[k] = errs.get(k, 0) + 1
            s = str(e).lower()
            if "groupcall" in s or "not in" in s or "no active" in s:
                calls.input_calls.pop((chat, aid), None)
                jset = calls.joined.get(aid)
                if jset:
                    jset.discard(chat)

    tasks = []
    for aid in present:
        tasks.append(asyncio.create_task(one(aid)))
        await asyncio.sleep(random.uniform(3.0, 5.0))
    await asyncio.gather(*tasks, return_exceptions=True)

    if errs and log:
        try:
            await log.event(
                "⚠ ᴠᴄ ʀᴇᴀᴄᴛ ᴇʀʀ\n  "
                + " | ".join(f"{v}x {k[:50]}" for k, v in list(errs.items())[:3])
            )
        except Exception:
            pass

    return {
        "ok": ok, "fail": fail, "skipped": skipped,
        "joined": joined_now, "join_fail": join_fail,
        "already": len(already), "present": len(present),
        "errors": errs,
    }


def _wrap_join(calls, aid, chat):
    async def _f():
        await calls.join_one(aid, chat)
    return _f

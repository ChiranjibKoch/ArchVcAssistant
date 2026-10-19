from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from archvc.vc import health, queue


class Calls:
    def __init__(self, herd, workers: int) -> None:
        self.herd = herd
        self.q = queue.Queue(workers)
        self.live: dict[str, PyTgCalls] = {}
        self.clients: dict[str, object] = {}
        self.joined: dict[str, set[int]] = {}
        self.input_calls: dict[str, object] = {}

    async def spawn(self) -> None:
        for aid, client in self.herd.live.items():
            if aid in self.live:
                continue
            await self.spawn_one(aid, client)

    async def spawn_one(self, aid: str, client) -> None:
        if aid in self.live:
            return
        try:
            c = PyTgCalls(client)
            await c.start()
            self.live[aid] = c
            self.clients[aid] = client
        except Exception:
            pass

    async def kill(self) -> None:
        for c in self.live.values():
            try:
                await c.stop()
            except Exception:
                pass
        self.live.clear()
        self.clients.clear()
        self.input_calls.clear()
        self.joined.clear()

    async def precheck(self, bot, chat) -> dict:
        return await health.check(self, chat)

    async def join(self, chat, mute: bool = True) -> dict:
        jobs = [
            (aid, _join(c, self.clients.get(aid), chat, mute))
            for aid, c in self.live.items()
        ]
        res = await self.q.fire(jobs)
        for aid, status in res.items():
            if status == "ok":
                self.joined.setdefault(aid, set()).add(chat)
        return res

    async def join_one(self, aid: str, chat, mute: bool = True) -> None:
        c = self.live.get(aid)
        if not c:
            raise KeyError(f"no live call for {aid}")
        client = self.clients.get(aid)
        await _ensure_member(client, chat)
        await _do_join(c, chat)
        if mute:
            try:
                await c.mute(chat)
            except Exception:
                pass
        self.joined.setdefault(aid, set()).add(chat)

    async def leave(self, chat) -> dict:
        jobs = [(aid, _leave(c, chat)) for aid, c in self.live.items()]
        res = await self.q.fire(jobs)
        for aid, status in res.items():
            if status == "ok":
                s = self.joined.get(aid)
                if s:
                    s.discard(chat)
        for k in [k for k in self.input_calls if isinstance(k, tuple) and k[0] == chat]:
            self.input_calls.pop(k, None)
        return res

    async def mute(self, chat) -> dict:
        jobs = [(aid, _mute(c, chat)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

    async def unmute(self, chat) -> dict:
        jobs = [(aid, _unmute(c, chat)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

    async def play(self, aid: str, chat, src: str) -> None:
        c = self.live.get(aid)
        if not c:
            raise KeyError(f"no live call for {aid}")
        await _audio(c, chat, src)

    async def play_all(self, chat, src: str) -> dict:
        jobs = [(aid, _audio(c, chat, src)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

    async def play_each(self, chat, mapping: dict[str, str]) -> dict:
        jobs = []
        for aid, src in mapping.items():
            c = self.live.get(aid)
            if c:
                jobs.append((aid, _audio(c, chat, src)))
        return await self.q.fire(jobs)

    async def pause(self, chat) -> dict:
        jobs = [(aid, _pause(c, chat)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

    async def resume(self, chat) -> dict:
        jobs = [(aid, _resume(c, chat)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)


    async def join_scoped(self, chat, scope, mute: bool = True) -> dict:
        aids = self._ids_for_scope(scope)
        if not aids:
            return {}
        jobs = [
            (aid, _join(c, self.clients.get(aid), chat, mute))
            for aid, c in self.live.items()
            if aid in aids
        ]
        res = await self.q.fire(jobs)
        for aid, status in res.items():
            if status == "ok":
                self.joined.setdefault(aid, set()).add(chat)
        return res

    async def leave_scoped(self, chat, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _leave(c, chat)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)

    async def mute_scoped(self, chat, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _mute(c, chat)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)

    async def unmute_scoped(self, chat, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _unmute(c, chat)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)

    async def play_all_scoped(self, chat, src, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _audio(c, chat, src)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)


    async def pause_scoped(self, chat, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _pause(c, chat)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)

    async def resume_scoped(self, chat, scope) -> dict:
        ids = self._ids_for_scope(scope)
        jobs = [(aid, _resume(c, chat)) for aid, c in self.live.items() if aid in ids]
        return await self.q.fire(jobs)

    def _ids_for_scope(self, scope) -> set:
        if not scope:
            return set()
        return {
            aid for aid, s in getattr(self.herd, "scope", {}).items()
            if s == scope and aid in self.live
        }

    def count(self) -> int:
        return len(self.live)


async def _ensure_member(client, chat):
    """Ensure the client is member of the chat. Returns (resolved_id, err)."""
    if client is None:
        return None, "no client"
    from archvc.vc import chat as chat_parser
    kind, value = chat_parser.parse(chat)
    if not kind:
        return None, "bad chat"

    join_arg = chat_parser.to_link(kind, value)

    try:
        result = await client.join_chat(join_arg)
        return result.id, None
    except UserAlreadyParticipant:
        try:
            info = await client.get_chat(join_arg)
            return info.id, None
        except Exception as e:
            return None, f"resolve: {type(e).__name__}: {str(e)[:100]}"
    except Exception as e:
        return None, f"join: {type(e).__name__}: {str(e)[:120]}"



def _is_already_joined(exc: Exception) -> bool:
    s = str(exc).lower()
    name = type(exc).__name__.lower()
    return (
        "already" in s
        or "groupcallalreadyjoined" in name
        or "alreadyjoined" in name
        or "already in" in s
    )


def _is_no_call(exc: Exception) -> bool:
    s = str(exc).lower()
    name = type(exc).__name__.lower()
    return (
        "noactivegroupcall" in name
        or "no active" in s
        or "no group call" in s
    )


async def _do_join(call, chat) -> None:
    try:
        await call.play(chat)
    except Exception as e:
        if _is_already_joined(e):
            return
        raise


def _join(call, client, chat, mute):
    async def _f():
        resolved, err = await _ensure_member(client, chat)
        if err:
            raise ValueError(f"join_chat: {err}")
        target = resolved if resolved else chat
        try:
            await _do_join(call, target)
        except Exception as e:
            if _is_already_joined(e):
                pass
            elif _is_no_call(e):
                raise ValueError("no active VC")
            else:
                raise
        if mute:
            try:
                await call.mute(target)
            except Exception:
                pass
    return _f


def _leave(call, chat):
    async def _f():
        try:
            await call.leave_call(chat)
        except Exception as e:
            if _is_already_joined(e) or "not in" in str(e).lower():
                return
            raise
    return _f


def _mute(call, chat):
    async def _f():
        await call.mute(chat)
    return _f


def _unmute(call, chat):
    async def _f():
        await call.unmute(chat)
    return _f


def _audio(call, chat, src):
    async def _f():
        try:
            await call.unmute(chat)
        except Exception:
            pass
        await call.play(chat, MediaStream(src))
    return _f


def _pause(call, chat):
    async def _f():
        await call.pause(chat)
    return _f


def _resume(call, chat):
    async def _f():
        await call.resume(chat)
    return _f

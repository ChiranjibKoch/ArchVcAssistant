from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from archvc.vc import queue


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
        self.input_calls.clear()
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

    def count(self) -> int:
        return len(self.live)


async def _ensure_member(client, chat) -> None:
    if client is None:
        return
    try:
        await client.join_chat(chat)
    except UserAlreadyParticipant:
        pass
    except Exception:
        pass


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
        or "groupcall_forbidden" in name
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
        await _ensure_member(client, chat)
        try:
            await _do_join(call, chat)
        except Exception as e:
            if _is_already_joined(e):
                pass
            elif _is_no_call(e):
                raise ValueError("no active VC")
            else:
                raise
        if mute:
            try:
                await call.mute(chat)
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

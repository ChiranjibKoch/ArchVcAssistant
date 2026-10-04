from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from archvc.vc import queue

SILENT = MediaStream("")


class Calls:
    def __init__(self, herd, workers: int) -> None:
        self.herd = herd
        self.q = queue.Queue(workers)
        self.live: dict[str, PyTgCalls] = {}
        self.input_calls: dict[str, object] = {}

    async def spawn(self) -> None:
        for aid, client in self.herd.live.items():
            try:
                c = PyTgCalls(client)
                await c.start()
                self.live[aid] = c
            except Exception:
                continue

    async def kill(self) -> None:
        for c in self.live.values():
            try:
                await c.stop()
            except Exception:
                pass
        self.live.clear()
        self.input_calls.clear()

    async def join(self, chat, mute: bool = True) -> dict:
        jobs = [(aid, _join(c, chat, mute)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

    async def leave(self, chat) -> dict:
        self.input_calls.clear()
        jobs = [(aid, _leave(c, chat)) for aid, c in self.live.items()]
        return await self.q.fire(jobs)

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


def _join(call, chat, mute):
    async def _f():
        await call.join_group_call(chat, SILENT)
        if mute:
            try:
                await call.mute(chat)
            except Exception:
                pass
    return _f


def _leave(call, chat):
    async def _f():
        await call.leave_call(chat)
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
        await call.pause_stream(chat)
    return _f


def _resume(call, chat):
    async def _f():
        await call.resume_stream(chat)
    return _f

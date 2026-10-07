import asyncio

CHECK_INTERVAL = 60


class Watchdog:
    def __init__(self, calls, log) -> None:
        self.calls = calls
        self.log = log
        self.watch: dict[int, set[str]] = {}
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def watch_chat(self, chat: int) -> int:
        aids = set(self.calls.live.keys())
        self.watch[chat] = aids
        self.start()
        return len(aids)

    def unwatch(self, chat: int) -> bool:
        return self.watch.pop(chat, None) is not None

    def unwatch_all(self) -> int:
        n = len(self.watch)
        self.watch.clear()
        return n

    def active(self, chat: int) -> bool:
        return chat in self.watch

    def status(self) -> dict:
        out = {}
        for chat, aids in self.watch.items():
            inside = sum(
                1 for a in aids if chat in self.calls.joined.get(a, set())
            )
            out[chat] = {"should": len(aids), "in": inside}
        return out

    async def _loop(self) -> None:
        while True:
            try:
                await self._heal()
            except Exception:
                pass
            await asyncio.sleep(CHECK_INTERVAL)

    async def _heal(self) -> None:
        for chat, aids in list(self.watch.items()):
            missing = [
                aid for aid in aids
                if aid in self.calls.live
                and chat not in self.calls.joined.get(aid, set())
            ]
            if not missing:
                continue
            jobs = [(aid, self._rejoin(aid, chat)) for aid in missing]
            res = await self.calls.q.fire(jobs)
            ok = sum(1 for v in res.values() if v == "ok")
            if ok:
                await self.log.event(
                    f"▣ ᴀᴜᴛᴏᴊᴏɪɴ\n  chat: {chat}\n"
                    f"  healed: {ok}/{len(missing)}"
                )

    def _rejoin(self, aid: str, chat: int):
        async def _f():
            await self.calls.join_one(aid, chat)
        return _f

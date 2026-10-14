import asyncio

CHECK_INTERVAL = 60


class Watchdog:
    def __init__(self, calls, log) -> None:
        self.calls = calls
        self.log = log
        self.watch: dict[int, dict] = {}
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

    def watch_chat(self, chat: int, mute: bool = True) -> int:
        self.watch[chat] = {"mute": mute}
        self.start()
        return len(self.calls.live)

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
        for chat, cfg in self.watch.items():
            total = len(self.calls.live)
            inside = sum(
                1 for a in self.calls.live
                if chat in self.calls.joined.get(a, set())
            )
            out[chat] = {"should": total, "in": inside}
        return out

    async def _loop(self) -> None:
        while True:
            try:
                await self._heal()
            except Exception as e:
                print(f"[autojoin] heal error: {type(e).__name__}: {e}", flush=True)
            await asyncio.sleep(CHECK_INTERVAL)

    async def _heal(self) -> None:
        for chat, cfg in list(self.watch.items()):
            missing = [
                aid for aid in self.calls.live
                if chat not in self.calls.joined.get(aid, set())
            ]
            if not missing:
                continue
            print(f"[autojoin] {chat}: healing {len(missing)}/{len(self.calls.live)}", flush=True)
            jobs = [(aid, self._rejoin(aid, chat, cfg["mute"])) for aid in missing]
            res = await self.calls.q.fire(jobs)
            ok = sum(1 for v in res.values() if v == "ok")
            if ok:
                await self.log.event(
                    f"▣ ᴀᴜᴛᴏᴊᴏɪɴ\n  chat: {chat}\n"
                    f"  healed: {ok}/{len(missing)}"
                )

    def _rejoin(self, aid: str, chat: int, mute: bool):
        async def _f():
            await self.calls.join_one(aid, chat, mute)
        return _f

import asyncio

from pyrogram.raw.functions.account import UpdateStatus

PING_INTERVAL = 180
BATCH_GAP = 0.3


class OnlineKeeper:
    def __init__(self, herd, log) -> None:
        self.herd = herd
        self.log = log
        self._task = None

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

    async def ping_all(self) -> dict:
        ok = 0
        fail = 0
        for aid, c in list(self.herd.live.items()):
            try:
                await c.invoke(UpdateStatus(offline=False))
                ok += 1
            except Exception:
                fail += 1
            await asyncio.sleep(BATCH_GAP)
        return {"ok": ok, "fail": fail}

    async def _loop(self) -> None:
        await asyncio.sleep(30)
        while True:
            try:
                res = await self.ping_all()
                print(f"[online] ping ok={res['ok']} fail={res['fail']}", flush=True)
            except Exception as e:
                print(f"[online] loop err: {type(e).__name__}: {e}", flush=True)
            await asyncio.sleep(PING_INTERVAL)

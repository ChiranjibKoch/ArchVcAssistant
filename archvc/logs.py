import asyncio
import time
from datetime import datetime, timezone

BATCH = 10
WINDOW = 2.0


class Feed:
    def __init__(self, db, group: int) -> None:
        self.db = db
        self.group = group
        self.bot = None
        self.q: asyncio.Queue[str] = asyncio.Queue()
        self._job: asyncio.Task | None = None

    def pipe(self, bot) -> None:
        self.bot = bot

    def start(self) -> None:
        self._job = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._job:
            self._job.cancel()
            try:
                await self._job
            except asyncio.CancelledError:
                pass

    async def note(self, text: str) -> None:
        await self.q.put(f"✦ ꜱʏꜱᴛᴇᴍ\n  {text}")

    async def event(self, text: str) -> None:
        await self.q.put(text)

    async def err(self, text: str) -> None:
        await self.q.put(f"⚠ ᴇʀʀᴏʀ\n  {text}")

    async def _loop(self) -> None:
        while True:
            batch = await self._grab()
            if batch:
                await self._ship(batch)

    async def _grab(self) -> list[str]:
        out: list[str] = []
        try:
            out.append(await asyncio.wait_for(self.q.get(), WINDOW))
        except asyncio.TimeoutError:
            return out
        t0 = time.monotonic()
        while len(out) < BATCH and time.monotonic() - t0 < WINDOW:
            try:
                out.append(await asyncio.wait_for(self.q.get(), 0.2))
            except asyncio.TimeoutError:
                break
        return out

    async def _ship(self, batch: list[str]) -> None:
        body = "\n\n".join(batch)
        now = datetime.now(timezone.utc)
        try:
            await self.db.logs.insert_many([{"at": now, "t": x} for x in batch])
        except Exception:
            pass
        if not self.bot:
            return
        try:
            await self.bot.send_message(self.group, body)
        except Exception:
            pass  # log group down shouldn't kill tasks

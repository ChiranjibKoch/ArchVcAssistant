import asyncio
from collections import deque


class Queue:
    def __init__(self, workers: int, gap: float = 3.0) -> None:
        self.sem = asyncio.Semaphore(workers)
        self.gap = gap
        self.retry: deque = deque()

    async def fire(self, jobs):
        out: dict[str, str] = {}

        async def one(k, fn):
            async with self.sem:
                try:
                    await fn()
                    out[k] = "ok"
                except Exception as e:
                    out[k] = f"fail:{type(e).__name__}"
                    self.retry.append((k, fn))
                await asyncio.sleep(0.05)

        await asyncio.gather(*(one(k, f) for k, f in jobs))

        if self.retry:
            wave = list(self.retry)
            self.retry.clear()
            await asyncio.sleep(self.gap)
            await asyncio.gather(*(one(k, f) for k, f in wave))

        return out

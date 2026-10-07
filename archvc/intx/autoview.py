import asyncio

from archvc.intx import views
from archvc.intx.views import parse_url

DEFAULT_INTERVAL = 120
DEFAULT_COUNT = 50


class AutoViewer:
    def __init__(self, db, herd, log) -> None:
        self.db = db
        self.herd = herd
        self.log = log
        self.running: dict[str, dict] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    async def _persist(self) -> None:
        data = {url: cfg for url, cfg in self.running.items()}
        await self.db.settings.update_one(
            {"k": "autoview_running"},
            {"$set": {"v": data}},
            upsert=True,
        )

    async def resume_all(self) -> int:
        doc = await self.db.settings.find_one({"k": "autoview_running"})
        data = dict(doc.get("v", {})) if doc else {}
        n = 0
        for url, cfg in data.items():
            self.running[url] = cfg
            self._tasks[url] = asyncio.create_task(self._loop(url))
            n += 1
        return n

    async def start(
        self,
        url: str,
        interval: int = DEFAULT_INTERVAL,
        count: int = DEFAULT_COUNT,
        react: str | None = None,
        join: bool = False,
        from_resume: bool = False,
    ) -> str:
        if url in self.running:
            return "already running"
        chat, mid = parse_url(url)
        if not mid:
            return "bad post url"
        cfg = {
            "interval": max(30, int(interval)),
            "count": int(count),
            "react": react,
            "join": join,
        }
        self.running[url] = cfg
        self._tasks[url] = asyncio.create_task(self._loop(url))
        await self._persist()
        if not from_resume:
            await self.log.event(
                f"◈ ᴀᴜᴛᴏᴠɪᴇᴡ ᴏɴ\n  url: {url}\n  every: {cfg['interval']}s\n"
                f"  count: {cfg['count']}"
            )
        return "started"

    async def stop(self, url: str) -> bool:
        existed = url in self.running
        self.running.pop(url, None)
        t = self._tasks.pop(url, None)
        if t:
            t.cancel()
        await self._persist()
        if existed:
            await self.log.event(f"◈ ᴀᴜᴛᴏᴠɪᴇᴡ ᴏꜰꜰ\n  url: {url}")
        return existed

    async def stop_all(self) -> int:
        urls = list(self.running.keys())
        for u in urls:
            await self.stop(u)
        return len(urls)

    def active(self, url: str) -> bool:
        return url in self.running

    def status(self) -> dict:
        return dict(self.running)

    async def _loop(self, url: str) -> None:
        await asyncio.sleep(5)
        while url in self.running:
            cfg = self.running[url]
            try:
                res = await views.boost(
                    self.herd, url, cfg["count"],
                    react=cfg.get("react"), join=cfg.get("join", False),
                )
                if res.get("ok"):
                    await self.log.event(
                        f"▣ ᴀᴜᴛᴏᴠɪᴇᴡ\n  url: {url}\n"
                        f"  ok: {res['ok']} | fail: {res['fail']}"
                    )
            except Exception:
                pass
            await asyncio.sleep(cfg["interval"])

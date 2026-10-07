import asyncio
import random

from archvc.intx import vcreact

DEFAULT_INTERVAL = 45
DEFAULT_EMOJIS = ["🔥", "❤️", "👍", "🎉", "💯", "⚡"]


class AutoReactor:
    def __init__(self, db, herd, calls, log) -> None:
        self.db = db
        self.herd = herd
        self.calls = calls
        self.log = log
        self.running: dict[int, dict] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    async def allowed(self) -> list:
        doc = await self.db.settings.find_one({"k": "allowed_chats"})
        return list(doc.get("v", [])) if doc else []

    async def is_allowed(self, chat) -> bool:
        return chat in await self.allowed()

    async def allow(self, chat) -> bool:
        allowed = await self.allowed()
        if chat in allowed:
            return False
        allowed.append(chat)
        await self.db.settings.update_one(
            {"k": "allowed_chats"}, {"$set": {"v": allowed}}, upsert=True
        )
        return True

    async def disallow(self, chat) -> bool:
        allowed = await self.allowed()
        if chat not in allowed:
            return False
        allowed.remove(chat)
        await self.db.settings.update_one(
            {"k": "allowed_chats"}, {"$set": {"v": allowed}}, upsert=True
        )
        await self.stop(chat)
        return True

    def active(self, chat) -> bool:
        return chat in self.running

    def status(self) -> dict:
        return dict(self.running)

    async def _persist(self) -> None:
        await self.db.settings.update_one(
            {"k": "autoreact_running"},
            {"$set": {"v": list(self.running.keys())}},
            upsert=True,
        )

    async def resume_all(self) -> int:
        doc = await self.db.settings.find_one({"k": "autoreact_running"})
        chats = list(doc.get("v", [])) if doc else []
        n = 0
        for chat in chats:
            if await self.is_allowed(chat):
                res = await self.start(chat, from_resume=True)
                if res == "started":
                    n += 1
        return n

    async def start(self, chat, interval: int = DEFAULT_INTERVAL,
                    emojis=None, from_resume: bool = False) -> str:
        if chat in self.running:
            return "already running"
        if not from_resume and not await self.is_allowed(chat):
            return "chat not in allowed list. use /allow <chat> first."
        if not self.calls.live:
            return "no accounts loaded. add an account first."
        cfg = {
            "interval": max(15, int(interval)),
            "emojis": emojis or DEFAULT_EMOJIS,
        }
        self.running[chat] = cfg
        self._tasks[chat] = asyncio.create_task(self._loop(chat))
        await self._persist()
        await self.log.event(
            f"◈ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏɴ\n  chat: {chat}\n  every: {cfg['interval']}s"
        )
        return "started"

    async def stop(self, chat) -> bool:
        existed = chat in self.running
        self.running.pop(chat, None)
        t = self._tasks.pop(chat, None)
        if t:
            t.cancel()
        await self._persist()
        if existed:
            await self.log.event(
                f"◈ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏꜰꜰ\n  chat: {chat}"
            )
        return existed

    async def stop_all(self) -> int:
        chats = list(self.running.keys())
        for c in chats:
            await self.stop(c)
        return len(chats)

    async def _loop(self, chat) -> None:
        await asyncio.sleep(5)
        while chat in self.running:
            cfg = self.running[chat]
            emoji = random.choice(cfg["emojis"])
            try:
                res = await vcreact.burst(
                    self.herd, chat, emoji, cache=self.calls.input_calls
                )
                if res["ok"]:
                    await self.log.event(
                        f"▣ ᴀᴜᴛᴏʀᴇᴀᴄᴛ\n  chat: {chat}\n"
                        f"  emoji: {emoji}\n  ok: {res['ok']} | fail: {res['fail']}"
                    )
            except Exception:
                pass
            await asyncio.sleep(cfg["interval"])

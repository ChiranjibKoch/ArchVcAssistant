import asyncio
import random
import time
from collections import defaultdict

from archvc.intx import vcreact

DEFAULT_INTERVAL = 60
DEFAULT_EMOJIS = [
    "🔥", "❤️", "👍", "🎉", "💯", "⚡", "😍", "👏", "😂", "🤩",
    "🥰", "😎", "🤔", "🙏", "👌", "🤝", "💪", "🫡", "😱", "😮",
    "🥳", "😇", "🤗", "😜", "🙃", "🫠", "😴", "🤤", "🥴", "🤠",
]
DEFAULT_BATCH = 15
DEFAULT_STAGGER = 0.4
COOLDOWN_PER_ACCOUNT = 6.0


class AutoReactor:
    def __init__(self, db, herd, calls, log) -> None:
        self.db = db
        self.herd = herd
        self.calls = calls
        self.log = log
        self.running: dict[int, dict] = {}
        self._tasks: dict[int, asyncio.Task] = {}
        self._last_used: dict[str, float] = defaultdict(float)

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
        data = {}
        for chat, cfg in self.running.items():
            data[str(chat)] = {
                "interval": cfg["interval"],
                "batch": cfg["batch"],
                "stagger": cfg["stagger"],
            }
        await self.db.settings.update_one(
            {"k": "autoreact_running"},
            {"$set": {"v": data}},
            upsert=True,
        )

    async def resume_all(self) -> int:
        doc = await self.db.settings.find_one({"k": "autoreact_running"})
        data = dict(doc.get("v", {})) if doc else {}
        n = 0
        for chat_str, cfg in data.items():
            try:
                chat = int(chat_str)
            except ValueError:
                continue
            if await self.is_allowed(chat):
                res = await self.start(
                    chat,
                    interval=cfg.get("interval", DEFAULT_INTERVAL),
                    batch=cfg.get("batch", DEFAULT_BATCH),
                    stagger=cfg.get("stagger", DEFAULT_STAGGER),
                    from_resume=True,
                )
                if res == "started":
                    n += 1
        return n

    async def start(self, chat, interval: int = DEFAULT_INTERVAL,
                    batch: int = DEFAULT_BATCH, stagger: float = DEFAULT_STAGGER,
                    emojis=None, from_resume: bool = False) -> str:
        if chat in self.running:
            return "already running"
        if not from_resume and not await self.is_allowed(chat):
            return "chat not in allowed list. /allow <chat> first."
        if not self.calls.live:
            return "no accounts loaded."

        cfg = {
            "interval": max(20, int(interval)),
            "batch": max(5, min(int(batch), 50)),
            "stagger": max(0.05, float(stagger)),
            "emojis": emojis or list(DEFAULT_EMOJIS),
        }
        self.running[chat] = cfg
        self._tasks[chat] = asyncio.create_task(self._loop(chat))
        await self._persist()
        print(f"[autoreact] started chat={chat} interval={cfg['interval']}s batch={cfg['batch']}", flush=True)
        await self.log.event(
            f"◈ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏɴ\n  chat: {chat}\n"
            f"  every: {cfg['interval']}s\n  batch: {cfg['batch']} accounts"
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
            print(f"[autoreact] stopped chat={chat}", flush=True)
            await self.log.event(f"◈ ᴀᴜᴛᴏʀᴇᴀᴄᴛ ᴏꜰꜰ\n  chat: {chat}")
        return existed

    async def stop_all(self) -> int:
        chats = list(self.running.keys())
        for c in chats:
            await self.stop(c)
        return len(chats)

    def _pick_accounts(self, chat, batch: int) -> list:
        now = time.monotonic()
        cooled = [
            aid for aid in self.calls.live
            if (now - self._last_used.get(f"{chat}:{aid}", 0)) >= COOLDOWN_PER_ACCOUNT
        ]
        if len(cooled) < batch:
            cooled = list(self.calls.live.keys())
            self._last_used.clear()
        random.shuffle(cooled)
        return cooled[:batch]

    def _assign_emojis(self, picks, pool_src):
        pool = list(pool_src)
        random.shuffle(pool)
        out = {}
        idx = 0
        for aid in picks:
            if idx >= len(pool):
                random.shuffle(pool)
                idx = 0
            out[aid] = pool[idx]
            idx += 1
        return out

    async def _loop(self, chat) -> None:
        print(f"[autoreact] loop entry chat={chat}", flush=True)
        await asyncio.sleep(5)
        while chat in self.running:
            cfg = self.running[chat]
            if not await self.is_allowed(chat):
                print(f"[autoreact] {chat} removed from allowed, stop", flush=True)
                self.running.pop(chat, None)
                self._tasks.pop(chat, None)
                await self._persist()
                return

            picks = self._pick_accounts(chat, cfg["batch"])
            if not picks:
                await asyncio.sleep(cfg["interval"])
                continue

            per = self._assign_emojis(picks, cfg["emojis"])
            distinct = len(set(per.values()))
            print(f"[autoreact] cycle chat={chat} batch={len(picks)} distinct={distinct}", flush=True)

            res = await self._fire(chat, per, cfg["stagger"])
            print(f"[autoreact] result chat={chat} ok={res['ok']} fail={res['fail']}", flush=True)

            if res["ok"]:
                await self.log.event(
                    f"▣ ᴀᴜᴛᴏʀᴇᴀᴄᴛ\n  chat: {chat}\n"
                    f"  emojis: {distinct} distinct\n"
                    f"  batch: {res['ok']}/{len(picks)}\n  fails: {res['fail']}"
                )
            await asyncio.sleep(cfg["interval"])

    async def _fire(self, chat, per: dict, stagger: float) -> dict:
        ok = 0
        fail = 0

        async def one(aid, emoji):
            nonlocal ok, fail
            call = self.calls.live.get(aid)
            client = self.calls.clients.get(aid)
            if not call or not client:
                fail += 1
                return
            try:
                input_call = self.calls.input_calls.get((chat, aid))
                if input_call is None:
                    input_call = await vcreact.resolve_input_call(client, chat)
                    if input_call is None:
                        fail += 1
                        return
                    self.calls.input_calls[(chat, aid)] = input_call
                await vcreact.send_one(client, input_call, emoji)
                ok += 1
                self._last_used[f"{chat}:{aid}"] = time.monotonic()
            except Exception as e:
                fail += 1
                msg = f"{type(e).__name__}: {str(e)[:120]}"
                print(f"[autoreact] {aid}: {msg}", flush=True)
                if "GROUPCALL" in str(e) or "CALL" in str(e):
                    self.calls.input_calls.pop((chat, aid), None)

        items = list(per.items())
        for i, (aid, emoji) in enumerate(items):
            asyncio.create_task(one(aid, emoji))
            await asyncio.sleep(stagger)
        await asyncio.sleep(len(items) * stagger + 2.0)
        return {"ok": ok, "fail": fail}

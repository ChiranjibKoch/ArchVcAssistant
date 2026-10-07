import asyncio
import random

from archvc.intx import react, views

DEFAULT_REACT = 30
DEFAULT_VIEWS = 100
DEFAULT_DELAY = 5.0
DEFAULT_EMOJIS = ["🔥", "❤️", "👍", "🎉", "💯", "⚡", "😍", "👏", "😂", "🤩"]


class PostWatch:
    def __init__(self, db, herd, log) -> None:
        self.db = db
        self.herd = herd
        self.log = log
        self.channels: dict[int, dict] = {}

    async def load(self) -> None:
        doc = await self.db.settings.find_one({"k": "postwatch"})
        data = dict(doc.get("v", {})) if doc else {}
        for k, v in data.items():
            try:
                self.channels[int(k)] = v
            except ValueError:
                continue

    async def save(self) -> None:
        data = {str(k): v for k, v in self.channels.items()}
        await self.db.settings.update_one(
            {"k": "postwatch"}, {"$set": {"v": data}}, upsert=True
        )

    def active(self, chat: int) -> bool:
        return chat in self.channels

    def list_all(self) -> dict:
        return dict(self.channels)

    async def add(self, chat: int, react_count: int = DEFAULT_REACT,
                  view_count: int = DEFAULT_VIEWS,
                  emojis=None, delay: float = DEFAULT_DELAY) -> None:
        self.channels[chat] = {
            "react_count": int(react_count),
            "view_count": int(view_count),
            "emojis": emojis or list(DEFAULT_EMOJIS),
            "delay": float(delay),
        }
        await self.save()

    async def remove(self, chat: int) -> bool:
        existed = chat in self.channels
        self.channels.pop(chat, None)
        if existed:
            await self.save()
        return existed

    async def remove_all(self) -> int:
        n = len(self.channels)
        self.channels.clear()
        await self.save()
        return n

    async def on_post(self, chat: int, msg_id: int) -> dict:
        cfg = self.channels.get(chat)
        if not cfg:
            return {}
        await asyncio.sleep(cfg["delay"])

        chat_str = str(chat)
        if chat_str.startswith("-100"):
            url = f"https://t.me/c/{chat_str[4:]}/{msg_id}"
        else:
            url = f"https://t.me/{chat_str.lstrip('-')}/{msg_id}"

        pool = list(cfg["emojis"])
        random.shuffle(pool)
        dist = {}
        for i in range(cfg["react_count"]):
            e = pool[i % len(pool)]
            dist[e] = dist.get(e, 0) + 1

        result = {"url": url, "react_ok": 0, "view_ok": 0, "dist": dist}

        try:
            r = await react.distribute(self.herd, url, dist)
            result["react_ok"] = r.get("ok", 0)
        except Exception as e:
            print(f"[postwatch] react fail: {e}", flush=True)

        try:
            v = await views.boost(self.herd, url, cfg["view_count"])
            result["view_ok"] = v.get("ok", 0)
        except Exception as e:
            print(f"[postwatch] view fail: {e}", flush=True)

        await self.log.event(
            f"▣ ᴀᴜᴛᴏᴘᴏꜱᴛ\n  chat: {chat}\n  msg: {msg_id}\n"
            f"  reactions: {result['react_ok']}\n"
            f"  views: {result['view_ok']}"
        )
        return result

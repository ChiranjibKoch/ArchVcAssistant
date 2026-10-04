#!/usr/bin/env python3
import asyncio
import signal
import sys

import uvloop

from archvc import conf, db, logs, nav, sudo
from archvc.acct import herd, login
from archvc.cmds import wire
from archvc.prox import fleet
from archvc.vc import calls


class Arch:
    def __init__(self) -> None:
        self.conf = None
        self.db = None
        self.log = None
        self.bot = None
        self.sudo = None
        self.fleet = None
        self.herd = None
        self.login = None
        self.calls = None
        self.nav = None

    async def boot(self) -> None:
        self.conf = conf.load()

        self.db = db.DB(self.conf.mongo_uri, self.conf.mongo_db)
        await self.db.ready()

        self.log = logs.Feed(self.db, self.conf.log_group)
        self.log.start()

        self.bot = await _bot(self.conf)
        self.log.pipe(self.bot)
        await self.log.note("bot up")

        self.sudo = sudo.Roster(self.db, self.conf.owner)
        await self.sudo.seed()

        self.fleet = fleet.Fleet(self.db)
        await self.fleet.refresh()
        await self.log.note(f"fleet: {await self.fleet.alive()} live")

        self.herd = herd.Herd(self.db, self.conf, self.fleet)
        await self.herd.graze()
        await self.log.note(
            f"herd: {self.herd.size} up, {self.herd.sick} sick"
        )

        self.login = login.Flow(self.db, self.conf, self.herd, self.log)
        self.calls = calls.Calls(self.herd, self.conf.vc_workers)
        await self.calls.spawn()

        wire(self)
        nav.mount(self)
        await self.log.note("online")

    async def run(self) -> None:
        from pyrogram import idle
        await idle()

    async def drain(self) -> None:
        if self.calls:
            await self.calls.kill()
        if self.fleet:
            self.fleet.halt()
        if self.herd:
            await self.herd.scatter()
        if self.log:
            await self.log.stop()
        if self.bot:
            try:
                await self.bot.stop()
            except Exception:
                pass
        if self.db:
            self.db.close()

    def on_signal(self) -> None:
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    s, lambda: asyncio.create_task(self._exit())
                )
            except NotImplementedError:
                pass

    async def _exit(self) -> None:
        await self.drain()
        sys.exit(0)


async def _bot(cfg):
    from pyrogram import Client
    c = Client(
        "archvc",
        api_id=cfg.api_id,
        api_hash=cfg.api_hash,
        bot_token=cfg.bot_token,
    )
    await c.start()
    return c


async def main() -> None:
    app = Arch()
    try:
        await app.boot()
        app.on_signal()
        await app.run()
    finally:
        await app.drain()


if __name__ == "__main__":
    uvloop.install()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

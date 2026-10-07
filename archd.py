#!/usr/bin/env python3
import asyncio
import signal
import sys

import uvloop

from archvc import conf, db, logs, nav, sudo, tenants
from archvc.acct import generate, herd, login
from archvc.cmds import wire
from archvc.prox import fleet
from archvc.intx import autojoin, autoview
from archvc.vc import calls, watchdog


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
        self.generate = None
        self.calls = None
        self.nav = None
        self.autojoin = None
        self.tenants = None
        self.autoview = None
        self.watchdog = None

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
        self.tenants = tenants.Tenants(self.db, self.log)
        for t in await self.tenants.approved():
            await self.sudo.add(t["tg_id"], by=0)

        self.fleet = fleet.Fleet(self.db)
        await self.fleet.refresh()
        await self.log.note(f"fleet: {await self.fleet.alive()} live")

        self.herd = herd.Herd(self.db, self.conf, self.fleet)
        await self.herd.graze()
        await self.log.note(
            f"herd: {self.herd.size} up, {self.herd.sick} sick"
        )

        self.login = login.Flow(self.db, self.conf, self.herd, self.log)
        self.generate = generate.Generate(self.herd, self.log)
        self.calls = calls.Calls(self.herd, self.conf.vc_workers)
        await self.calls.spawn()
        self.herd.on_new = self.calls.spawn_one
        self.autojoin = autojoin.AutoReactor(
            self.db, self.herd, self.calls, self.log
        )
        self.watchdog = watchdog.Watchdog(self.calls, self.log)
        self.autoview = autoview.AutoViewer(
            self.db, self.herd, self.log
        )
        av_resumed = await self.autoview.resume_all()
        if av_resumed:
            await self.log.note(f"autoview resumed: {av_resumed}")
        resumed = await self.autojoin.resume_all()
        if resumed:
            await self.log.note(f"autoreact resumed: {resumed}")

        wire(self)
        nav.mount(self)
        await self.log.note("online")

    async def run(self) -> None:
        from pyrogram import idle
        await idle()

    async def drain(self) -> None:
        if self.watchdog:
            await self.watchdog.stop()
        if self.autoview:
            await self.autoview.stop_all()
        if self.autojoin:
            await self.autojoin.stop_all()
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

from pyrogram import filters

from archvc.gate import deny_msg


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("backfillscope") & filters.private)
    async def _bf(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)

        await m.reply("backfilling scope...")

        total = await app.db.accounts.count_documents({})
        missing = await app.db.accounts.count_documents(
            {"$or": [{"scope": {"$exists": False}}, {"scope": None}]}
        )
        r = await app.db.accounts.update_many(
            {"$or": [{"scope": {"$exists": False}}, {"scope": None}]},
            {"$set": {"scope": "owner"}},
        )
        scopes = await app.db.accounts.distinct("scope")

        await m.reply(
            "backfill done\n"
            f"  total:      {total}\n"
            f"  missing:    {missing}\n"
            f"  backfilled: {r.modified_count}\n"
            f"  scopes:     {scopes}"
        )

    @bot.on_message(filters.command("diag") & filters.private)
    async def _diag(_, m):
        uid = m.from_user.id
        if not app.sudo.is_owner(uid):
            return await deny_msg(m)

        # DB counts
        db_total = await app.db.accounts.count_documents({})
        db_up = await app.db.accounts.count_documents({"state": "up"})
        db_sick = await app.db.accounts.count_documents({"state": "sick"})

        # herd live
        herd_total = len(app.herd.live)
        herd_sizes = len(getattr(app.herd, "scope", {}))

        # scope breakdown
        scope_counts = {}
        for aid, s in getattr(app.herd, "scope", {}).items():
            scope_counts[s] = scope_counts.get(s, 0) + 1

        # calls live
        calls_total = len(app.calls.live)
        calls_clients = len(getattr(app.calls, "clients", {}))

        await m.reply(
            "diag\n"
            f"  db total:    {db_total}\n"
            f"  db up:       {db_up}\n"
            f"  db sick:     {db_sick}\n"
            f"  herd live:   {herd_total}\n"
            f"  herd scope:  {herd_sizes}\n"
            f"  scope dist:  {scope_counts}\n"
            f"  calls live:  {calls_total}\n"
            f"  calls cli:   {calls_clients}"
        )

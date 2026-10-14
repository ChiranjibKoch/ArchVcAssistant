from pyrogram import filters
from pyrogram.enums import ParseMode

from archvc.acct import scope as sc
from archvc.gate import deny_msg
from archvc.intx import react, views

SAFE_EMOJIS = ["👍", "❤️", "🔥", "🎉", "👏", "😁", "🥰", "🤔", "🙏"]


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("rx") & filters.private)
    async def _rx(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "Usage: /rx <post_url> [emoji]\n"
                f"Random per account from:\n{' '.join(SAFE_EMOJIS)}"
            )
        url = parts[1]
        emoji = parts[2] if len(parts) > 2 else None
        if emoji and emoji not in SAFE_EMOJIS:
            return await m.reply(
                f"{emoji} not allowed\nSafe: {' '.join(SAFE_EMOJIS)}",
                parse_mode=ParseMode.DISABLED,
            )
        await m.reply("Sending...")
        if emoji:
            res = await react.burst_scoped(app, url, emoji, sp)
            label = emoji
        else:
            res = await react.random_burst_scoped(app, url, SAFE_EMOJIS, sp)
            label = "random"
        body = f"Reactions: {res['ok']} ok / {res['fail']} fail"
        for k, v in list((res.get("errors") or {}).items())[:3]:
            body += f"\n  {v}x  {k[:120]}"
        await m.reply(body, parse_mode=ParseMode.DISABLED)
        await app.log.event(
            f"▣ ʀx\n  scope: {sp}\n  post: {url}\n"
            f"  emoji: {label}\n  ok: {res['ok']}\n  by: {uid}"
        )

    @bot.on_message(filters.command("views") & filters.private)
    async def _vw(_, m):
        uid = m.from_user.id
        sp = await sc.resolve(app, uid)
        if not sp:
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 3:
            return await m.reply("Usage: /views <post_url> <count>")
        url = parts[1]
        try:
            n = int(parts[2])
        except ValueError:
            return await m.reply("Bad count.")
        await m.reply("Boosting...")
        res = await views.boost_scoped(app, url, n, sp)
        body = f"Views: {res['ok']} ok / {res['fail']} fail"
        for k, v in list((res.get("errors") or {}).items())[:3]:
            body += f"\n  {v}x  {k[:120]}"
        await m.reply(body, parse_mode=ParseMode.DISABLED)

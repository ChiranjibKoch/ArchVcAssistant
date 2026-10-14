from pyrogram import filters
from pyrogram.enums import ParseMode

from archvc.gate import deny_msg
from archvc.intx import react, views

SAFE_EMOJIS = ["👍", "❤️", "🔥", "🎉", "👏", "😁", "🥰", "🤔", "🙏"]


def wire(app) -> None:
    bot = app.bot

    @bot.on_message(filters.command("rx") & filters.private)
    async def _rx(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 2:
            return await m.reply(
                "Usage: /rx <post_url> [emoji]\n"
                f"If emoji omitted - random per account from:\n"
                f"{' '.join(SAFE_EMOJIS)}",
                parse_mode=ParseMode.DISABLED,
            )
        url = parts[1]
        emoji = parts[2] if len(parts) > 2 else None

        if emoji and emoji not in SAFE_EMOJIS:
            return await m.reply(
                f"{emoji} not allowed for non-premium accounts\n"
                f"Safe set: {' '.join(SAFE_EMOJIS)}",
                parse_mode=ParseMode.DISABLED,
            )

        await m.reply("Sending...")
        if emoji:
            res = await react.burst(app.herd, url, emoji)
            label = emoji
        else:
            res = await react.random_burst(app.herd, url, SAFE_EMOJIS)
            label = "random"

        body = f"Reactions: {res['ok']} ok / {res['fail']} fail"
        errs = res.get("errors") or {}
        for k, v in list(errs.items())[:3]:
            body += f"\n  {v}x  {k[:120]}"
        await m.reply(body, parse_mode=ParseMode.DISABLED)
        await app.log.event(
            f"▣ ʀᴇᴀᴄᴛɪᴏɴꜱ ꜱᴇɴᴛ\n  post: {url}\n  emoji: {label}\n"
            f"  ok: {res['ok']} | fail: {res['fail']}\n  by: {uid}"
        )

    @bot.on_message(filters.command("views") & filters.private)
    async def _vw(_, m):
        uid = m.from_user.id
        if not (app.sudo.is_owner(uid) or app.sudo.has(uid)):
            return await deny_msg(m)
        parts = m.text.split()
        if len(parts) < 3:
            return await m.reply("Usage: /views <post_url> <count> [emoji]")
        url = parts[1]
        try:
            n = int(parts[2])
        except ValueError:
            return await m.reply("Bad count.")
        emoji = parts[3] if len(parts) > 3 else None
        if emoji and emoji not in SAFE_EMOJIS:
            return await m.reply(
                f"{emoji} not allowed\nSafe set: {' '.join(SAFE_EMOJIS)}",
                parse_mode=ParseMode.DISABLED,
            )
        await m.reply("Boosting...")
        res = await views.boost(app.herd, url, n, react=emoji)
        body = f"Views: {res['ok']} ok / {res['fail']} fail"
        errs = res.get("errors") or {}
        for k, v in list(errs.items())[:3]:
            body += f"\n  {v}x  {k[:120]}"
        await m.reply(body, parse_mode=ParseMode.DISABLED)
        await app.log.event(
            f"▣ ᴠɪᴇᴡꜱ ᴀᴅᴅᴇᴅ\n  post: {url}\n"
            f"  target: {n} | ok: {res['ok']}\n  by: {uid}"
        )

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

NS = "c:"

_MODE = None


def _mode():
    global _MODE
    if _MODE is not None:
        return _MODE
    try:
        from pyrogram.types import KeyboardButtonStyle  # noqa: F401
        _MODE = "object"
    except ImportError:
        try:
            InlineKeyboardButton("x", callback_data="x", style="primary")
            _MODE = "string"
        except TypeError:
            _MODE = "none"
    return _MODE


def _btn(label, data, kind):
    mode = _mode()
    if mode == "object":
        from pyrogram.types import KeyboardButtonStyle
        kw = {f"bg_{kind}": True}
        try:
            return InlineKeyboardButton(
                label,
                callback_data=NS + data,
                style=KeyboardButtonStyle(**kw),
            )
        except TypeError:
            pass
    if mode == "string":
        try:
            return InlineKeyboardButton(
                label, callback_data=NS + data, style=kind
            )
        except TypeError:
            pass
    return InlineKeyboardButton(label, callback_data=NS + data)


def prim(label, data):
    return _btn(label, data, "primary")


def succ(label, data):
    return _btn(label, data, "success")


def dang(label, data):
    return _btn(label, data, "danger")


def root(is_owner):
    rows = [
        [succ("➕ ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", "nav:acc:add"),
         prim("📋 ᴀᴄᴄᴏᴜɴᴛꜱ", "nav:acc")],
        [succ("🎙 ᴊᴏɪɴ ᴠᴄ", "nav:vc:join"),
         dang("🔇 ʟᴇᴀᴠᴇ ᴠᴄ", "nav:vc:leave")],
        [prim("🔥 ʀᴇᴀᴄᴛɪᴏɴꜱ", "nav:intx:rx"),
         prim("👁 ᴠɪᴇᴡꜱ", "nav:intx:views")],
        [succ("🎵 ᴀᴜᴅɪᴏ", "nav:vc:play"),
         prim("🌐 ᴘʀᴏxɪᴇꜱ", "nav:sys:proxies")],
        [prim("📜 ʟᴏɢꜱ", "nav:sys:logs"),
         prim("⚙ ꜱʏꜱᴛᴇᴍ", "nav:sys")],
    ]
    if is_owner:
        rows.append([prim("👥 ꜱᴜᴅᴏ", "nav:sd")])
    return InlineKeyboardMarkup(rows)


def accounts():
    return InlineKeyboardMarkup([
        [succ("➕ ᴀᴅᴅ", "nav:acc:add"),
         dang("🗑 ʀᴇᴍᴏᴠᴇ", "acc:rm")],
        [prim("🔑 ꜱᴇꜱꜱɪᴏɴ", "acc:add:s"),
         prim("📱 ᴏᴛᴘ", "acc:add:o")],
        [prim("🔍 ꜱᴇᴀʀᴄʜ", "acc:search"),
         prim("🔄 ʀᴇꜰʀᴇꜱʜ", "acc:refresh")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def voice():
    return InlineKeyboardMarkup([
        [succ("🎙 ᴊᴏɪɴ", "nav:vc:join"),
         dang("🔇 ʟᴇᴀᴠᴇ", "nav:vc:leave")],
        [prim("🔊 ᴜɴᴍᴜᴛᴇ", "vc:unmute"),
         prim("🔈 ᴍᴜᴛᴇ", "vc:mute")],
        [succ("▶ ᴘʟᴀʏ", "vc:play"),
         dang("⏸ ᴘᴀᴜꜱᴇ", "vc:pause")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def interaction():
    return InlineKeyboardMarkup([
        [prim("🔥 ʀᴇᴀᴄᴛɪᴏɴꜱ", "nav:intx:rx")],
        [prim("👁 ᴠɪᴇᴡꜱ", "nav:intx:views")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def system(is_owner):
    rows = [
        [prim("✦ ꜱᴛᴀᴛꜱ", "sys:stats"),
         prim("🌐 ᴘʀᴏxɪᴇꜱ", "sys:proxies")],
        [prim("📜 ʟᴏɢꜱ", "sys:logs")],
    ]
    if is_owner:
        rows.append([prim("📌 ꜱᴇᴛ ʟᴏɢ ɢʀᴏᴜᴘ", "sys:setlog")])
    rows.append([prim("◀ ʙᴀᴄᴋ", "nav:root")])
    return InlineKeyboardMarkup(rows)


def sudo():
    return InlineKeyboardMarkup([
        [prim("👥 ʟɪꜱᴛ", "sd:list")],
        [succ("➕ ᴀᴅᴅ", "sd:add"),
         dang("🗑 ʀᴇᴍᴏᴠᴇ", "sd:rm")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def confirm(action, destructive=False):
    yes = dang("✔ ᴄᴏɴꜰɪʀᴍ", f"ok:{action}") if destructive \
        else succ("✔ ᴄᴏɴꜰɪʀᴍ", f"ok:{action}")
    no = prim("✘ ᴄᴀɴᴄᴇʟ", "nav:root")
    return InlineKeyboardMarkup([[yes, no]])


def back(to="root"):
    return InlineKeyboardMarkup([[prim("◀ ʙᴀᴄᴋ", f"nav:{to}")]])

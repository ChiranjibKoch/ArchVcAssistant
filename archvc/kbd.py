from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

NS = "c:"


def _b(label, data, style=ButtonStyle.DEFAULT):
    try:
        return InlineKeyboardButton(label, callback_data=NS + data, style=style)
    except TypeError:
        return InlineKeyboardButton(label, callback_data=NS + data)


def prim(label, data):
    return _b(label, data, ButtonStyle.PRIMARY)


def succ(label, data):
    return _b(label, data, ButtonStyle.SUCCESS)


def dang(label, data):
    return _b(label, data, ButtonStyle.DANGER)


def root(is_owner):
    rows = [
        [succ("➕ ᴀᴅᴅ", "nav:acc:add"), prim("📋 ᴀᴄᴄᴏᴜɴᴛꜱ", "nav:acc"),
         succ("🎙 ᴊᴏɪɴ", "nav:vc:join"), dang("🔇 ʟᴇᴀᴠᴇ", "nav:vc:leave")],
        [prim("🔥 ʀx", "nav:intx:rx"), prim("👁 ᴠɪᴇᴡꜱ", "nav:intx:views"),
         succ("🎵 ᴘʟᴀʏ", "nav:vc:play"), prim("🌐 ᴘʀᴏxʏ", "nav:px")],
        [prim("📜 ʟᴏɢꜱ", "nav:sys:logs"), prim("⚙ ꜱʏꜱᴛᴇᴍ", "nav:sys")],
    ]
    if is_owner:
        rows.append([prim("👥 ꜱᴜᴅᴏ", "nav:sd")])
    return InlineKeyboardMarkup(rows)


def accounts():
    return InlineKeyboardMarkup([
        [succ("➕ ᴀᴅᴅ", "nav:acc:add"), dang("🗑 ʀᴇᴍᴏᴠᴇ", "acc:rm")],
        [prim("🔑 ꜱᴇꜱꜱɪᴏɴ", "acc:add:s"), prim("📱 ᴏᴛᴘ", "acc:add:o")],
        [prim("🔍 ꜱᴇᴀʀᴄʜ", "acc:search"), prim("🔄 ʀᴇꜰʀᴇꜱʜ", "acc:refresh")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def voice():
    return InlineKeyboardMarkup([
        [succ("🎙 ᴊᴏɪɴ", "nav:vc:join"), dang("🔇 ʟᴇᴀᴠᴇ", "nav:vc:leave")],
        [prim("🔊 ᴜɴᴍᴜᴛᴇ", "vc:unmute"), prim("🔈 ᴍᴜᴛᴇ", "vc:mute")],
        [succ("▶ ᴘʟᴀʏ", "vc:play"), dang("⏸ ᴘᴀᴜꜱᴇ", "vc:pause")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def interaction():
    return InlineKeyboardMarkup([
        [prim("🔥 ʀᴇᴀᴄᴛɪᴏɴꜱ", "nav:intx:rx"),
         prim("👁 ᴠɪᴇᴡꜱ", "nav:intx:views")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def proxy():
    return InlineKeyboardMarkup([
        [prim("🔄 ʀᴇꜰʀᴇꜱʜ", "px:refresh"),
         succ("✅ ᴄʜᴇᴄᴋ", "px:check"),
         succ("➕ ᴀᴅᴅ", "px:add"),
         dang("🗑 ᴄʟᴇᴀɴ", "px:clean")],
        [prim("📊 ꜱᴛᴀᴛꜱ", "px:stats"),
         prim("📋 ʟɪꜱᴛ", "px:list"),
         prim("🌐 ꜰᴀᴋᴇᴛʟꜱ", "px:faketls"),
         prim("🔵 ᴍᴛᴘʀᴏᴛᴏ", "px:mtproto")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def system(is_owner):
    rows = [
        [prim("✦ ꜱᴛᴀᴛꜱ", "sys:stats"), prim("🌐 ᴘʀᴏxɪᴇꜱ", "sys:proxies")],
        [prim("📜 ʟᴏɢꜱ", "sys:logs")],
    ]
    if is_owner:
        rows.append([prim("📌 ꜱᴇᴛ ʟᴏɢ", "sys:setlog")])
    rows.append([prim("◀ ʙᴀᴄᴋ", "nav:root")])
    return InlineKeyboardMarkup(rows)


def sudo():
    return InlineKeyboardMarkup([
        [prim("👥 ʟɪꜱᴛ", "sd:list")],
        [succ("➕ ᴀᴅᴅ", "sd:add"), dang("🗑 ʀᴇᴍᴏᴠᴇ", "sd:rm")],
        [prim("◀ ʙᴀᴄᴋ", "nav:root")],
    ])


def confirm(action, destructive=False):
    yes = dang("✔ ᴄᴏɴꜰɪʀᴍ", f"ok:{action}") if destructive \
        else succ("✔ ᴄᴏɴꜰɪʀᴍ", f"ok:{action}")
    return InlineKeyboardMarkup([[yes, prim("✘ ᴄᴀɴᴄᴇʟ", "nav:root")]])


def back(to="root"):
    return InlineKeyboardMarkup([[prim("◀ ʙᴀᴄᴋ", f"nav:{to}")]])

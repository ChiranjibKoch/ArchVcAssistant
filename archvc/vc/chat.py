"""Parse any Telegram chat input into (kind, value)."""


def parse(chat):
    """
    Returns (kind, value):
      ('id', int)          — numeric chat id
      ('username', str)    — public @username
      ('invite', str)      — invite hash (from +abc or joinchat/abc)
    """
    if isinstance(chat, int):
        return "id", chat
    s = str(chat).strip()
    if not s:
        return None, None

    # strip protocol
    for pfx in ("https://", "http://"):
        if s.startswith(pfx):
            s = s[len(pfx):]
            break
    for dom in ("t.me/", "telegram.me/", "www.t.me/"):
        if s.startswith(dom):
            s = s[len(dom):]
            break

    # strip query and fragment (?livestream, #xyz)
    if "?" in s:
        s = s.split("?", 1)[0]
    if "#" in s:
        s = s.split("#", 1)[0]
    s = s.strip("/")
    if not s:
        return None, None

    # numeric id
    body = s.lstrip("-")
    if body.isdigit():
        return "id", int(s)

    # private message link: t.me/c/123/456
    parts = [p for p in s.split("/") if p]
    if parts and parts[0] == "c" and len(parts) >= 2 and parts[1].isdigit():
        return "id", int("-100" + parts[1])

    # invite: +abc or joinchat/abc
    if s.startswith("+"):
        return "invite", s[1:]
    if s.startswith("joinchat/"):
        return "invite", s[9:]

    # public username
    if s.startswith("@"):
        s = s[1:]
    # strip trailing path segment (t.me/username/123)
    if "/" in s:
        s = s.split("/", 1)[0]
    return "username", s


def to_link(kind, value):
    if kind == "invite":
        return f"https://t.me/+{value}"
    if kind == "username":
        return f"@{value}"
    return value

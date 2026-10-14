def owner_scope() -> str:
    return "owner"


async def resolve(app, uid: int) -> str | None:
    if app.sudo.is_owner(uid):
        return "owner"
    t = await app.tenants.get(uid)
    if t and t.get("status") == "approved":
        tid = t.get("tenant")
        if tid:
            return f"t_{tid}"
    return None


def ids_for(app, scope: str) -> list:
    if not scope:
        return []
    return [
        aid for aid, s in app.herd.scope.items()
        if s == scope
    ]


def live_for(app, scope: str) -> dict:
    if not scope:
        return {}
    return {
        aid: c for aid, c in app.herd.live.items()
        if app.herd.scope.get(aid) == scope
    }


def scope_label(scope: str) -> str:
    if scope == "owner":
        return "ᴏᴡɴᴇʀ"
    if scope and scope.startswith("t_"):
        return f"ᴛᴇɴᴀɴᴛ {scope[2:]}"
    return scope or "—"

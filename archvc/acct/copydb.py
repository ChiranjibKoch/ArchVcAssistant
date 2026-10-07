import base64
import hashlib
import random
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

FAKER_KEY = b"c7f1b9a3e6d4082f5a91c3b7e0d2f4a8"

_DEVICES = [
    "Samsung Galaxy S23", "Samsung Galaxy S24", "Samsung Galaxy A54",
    "Google Pixel 8", "Google Pixel 8 Pro", "Google Pixel 7a",
    "Xiaomi Redmi Note 12", "Xiaomi 13 Pro", "OnePlus 11", "OnePlus Nord 3",
    "iPhone 14 Pro", "iPhone 15", "iPhone 15 Pro Max", "iPhone 13",
    "Realme GT Neo 5", "Nothing Phone 2", "Motorola Edge 40",
    "Vivo V29 Pro", "Oppo Reno 10 Pro", "Asus Zenfone 10",
]

_SYSTEMS = [
    "SDK 33", "SDK 34", "SDK 35",
    "Android 13", "Android 14", "Android 15",
    "iOS 17.4", "iOS 17.5", "iOS 18.0",
]

_APPS = [
    "10.2.0 (4234)", "10.3.1 (4298)", "10.4.0 (4352)",
    "10.4.2 (4380)", "10.5.0 (4411)",
]

SESSION_FIELDS = ("session", "session_string", "string_session", "sessionString")


def fingerprint(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:16]


def device_for(aid: str) -> dict:
    rng = random.Random(int(aid[:8], 16))
    return {
        "device_model": rng.choice(_DEVICES),
        "system_version": rng.choice(_SYSTEMS),
        "app_version": rng.choice(_APPS),
    }


def aes_dec(b64: str, key: bytes = FAKER_KEY) -> str:
    if not b64:
        return ""
    data = base64.b64decode(b64)
    return AESGCM(key).decrypt(data[:12], data[12:], None).decode()


async def scan(src) -> list:
    found = []
    try:
        cols = await src.list_collection_names()
    except Exception:
        return found

    if "user_settings" in cols:
        async for doc in src["user_settings"].find({}):
            owner = doc.get("_id", 0)
            for c in doc.get("cli") or []:
                if c.get("dis"):
                    continue
                es = c.get("es", "")
                if not es:
                    continue
                found.append({
                    "kind": "faker",
                    "aid": c.get("aid"),
                    "owner": owner,
                    "session_enc": es,
                    "phone_enc": c.get("ph", ""),
                    "source": f"user_settings:{owner}:{c.get('aid')}",
                })

    for name in cols:
        if name == "user_settings":
            continue
        col = src[name]
        sample = await col.find_one({})
        if not sample:
            continue
        sf = None
        for f in SESSION_FIELDS:
            if f in sample:
                sf = f
                break
        if not sf:
            continue
        async for doc in col.find({}):
            s = doc.get(sf, "")
            if not s or not isinstance(s, str):
                continue
            found.append({
                "kind": "generic",
                "owner": doc.get("owner") or doc.get("user_id") or doc.get("_id") or 0,
                "session_raw": s,
                "phone": doc.get("phone") or doc.get("phone_number") or "",
                "source": f"{name}:{doc.get('_id', '?')}",
            })

    return found


async def import_records(dst, records, fernet, owner_default,
                         api_id, api_hash, dry=True) -> dict:
    stats = {"ok": 0, "dup": 0, "fail": 0, "errors": []}
    for r in records:
        try:
            if r["kind"] == "faker":
                session = aes_dec(r["session_enc"])
                phone = aes_dec(r["phone_enc"])
            else:
                session = r["session_raw"]
                phone = r.get("phone", "")

            if not session:
                stats["fail"] += 1
                continue

            aid = fingerprint(session)
            if await dst.find_one({"account_id": aid}):
                stats["dup"] += 1
                continue

            rec = {
                "account_id": aid,
                "owner": r.get("owner") or owner_default,
                "phone": phone,
                "session": fernet.encrypt(session.encode()).decode(),
                "proxy": None,
                "state": "up",
                "api_id": api_id,
                "api_hash": api_hash,
                "tg_name": None,
                "tg_id": None,
                "device": device_for(aid),
                "migrated_from": r.get("source"),
                "migrated_at": datetime.now(timezone.utc),
            }
            if not dry:
                await dst.insert_one(rec)
            stats["ok"] += 1
        except Exception as e:
            stats["fail"] += 1
            if len(stats["errors"]) < 5:
                stats["errors"].append(f"{r.get('source')}: {type(e).__name__}: {e}")
    return stats


async def collections(src) -> list:
    try:
        return await src.list_collection_names()
    except Exception:
        return []

import asyncio
import base64
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from motor.motor_asyncio import AsyncIOMotorClient

FAKER_KEY = b"c7f1b9a3e6d4082f5a91c3b7e0d2f4a8"


def aes_dec(b64):
    data = base64.b64decode(b64)
    return AESGCM(FAKER_KEY).decrypt(data[:12], data[12:], None).decode()


async def t(uri, src_db):
    c = AsyncIOMotorClient(uri, tz_aware=True)
    db = c[src_db]
    doc = await db.user_settings.find_one({"cli.0": {"$exists": True}})
    if not doc:
        print("no doc with clients")
        return
    cli = doc["cli"][0]
    es = cli.get("es")
    print("source uid:", doc["_id"])
    print("client aid:", cli.get("aid"))
    print("es first 60:", es[:60] if es else None)

    plain = aes_dec(es)
    print("\nplain length (chars):", len(plain))
    print("plain first 80:", plain[:80])

    raw = None
    for enc in ("urlsafe", "std"):
        try:
            pad = "=" * (-len(plain) % 4)
            if enc == "urlsafe":
                raw = base64.urlsafe_b64decode(plain + pad)
            else:
                raw = base64.b64decode(plain + pad)
            print(f"\n{enc} b64 decode OK")
            break
        except Exception as e:
            print(f"{enc} fail:", e)

    if raw:
        print("decoded length (bytes):", len(raw))
        print("first 64 hex:", raw[:64].hex())
        print("last 32 hex:", raw[-32:].hex())
        print("total expected pyrogram: 271")

    c.close()


if __name__ == "__main__":
    asyncio.run(t(sys.argv[1], sys.argv[2]))

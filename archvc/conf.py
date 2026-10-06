import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _validate_session_key(k: str) -> str:
    if not k or len(k) < 40:
        raise RuntimeError(
            "SESSION_KEY missing or too short.\n"
            "Generate with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
            "Then set as SESSION_KEY in .env / Heroku config."
        )
    try:
        from cryptography.fernet import Fernet
        Fernet(k.encode())
    except Exception as e:
        raise RuntimeError(
            f"SESSION_KEY invalid: {e}\n"
            "Regenerate with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return k


@dataclass(frozen=True)
class Conf:
    api_id: int
    api_hash: str
    bot_token: str
    owner: int
    log_group: int
    mongo_uri: str
    mongo_db: str
    vc_workers: int
    session_key: str


def load() -> Conf:
    load_dotenv()
    e = os.environ
    return Conf(
        api_id=int(e["API_ID"]),
        api_hash=e["API_HASH"],
        bot_token=e["BOT_TOKEN"],
        owner=int(e["OWNER_ID"]),
        log_group=int(e["LOG_GROUP_ID"]),
        mongo_uri=e.get("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db=e.get("MONGO_DB", "archvc"),
        vc_workers=int(e.get("VC_WORKERS", "8")),
        session_key=_validate_session_key(e.get("SESSION_KEY", "")),
    )

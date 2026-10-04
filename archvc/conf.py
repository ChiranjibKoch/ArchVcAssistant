import os
from dataclasses import dataclass

from dotenv import load_dotenv


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
        vc_workers=int(e.get("VC_WORKERS", "20")),
        session_key=e["SESSION_KEY"],
    )

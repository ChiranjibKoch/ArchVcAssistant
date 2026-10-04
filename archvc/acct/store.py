import hashlib

from cryptography.fernet import Fernet, InvalidToken

_f = None


def _fernet() -> Fernet:
    global _f
    if _f is None:
        from archvc import conf
        _f = Fernet(conf.load().session_key.encode())
    return _f


def fingerprint(session: str) -> str:
    return hashlib.sha256(session.encode()).hexdigest()[:16]


def seal(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def open_(blob: str) -> str:
    try:
        return _fernet().decrypt(blob.encode()).decode()
    except InvalidToken:
        raise ValueError("session blob corrupt or key rotated")


def new_key() -> str:
    return Fernet.generate_key().decode()

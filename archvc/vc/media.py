import asyncio
from pathlib import Path

import yt_dlp


def resolve(src: str) -> str:
    if src.startswith("file://"):
        return src
    p = Path(src)
    if p.exists():
        return str(p.resolve())
    if src.startswith(("http://", "https://")) and not _is_yt(src):
        return src
    return _yt(src)


async def resolve_async(src: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, resolve, src)


def _is_yt(s: str) -> bool:
    return "youtube.com" in s or "youtu.be" in s


def _yt(url: str) -> str:
    opts = {
        "format": "bestaudio[ext=webm]/bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info["url"]

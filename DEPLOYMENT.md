# ArchVcAssistant — Deployment Guide

Multi-account Telegram voice chat automation bot.

**Repo:** https://github.com/ChiranjibKoch/ArchVcAssistant
**Last updated:** 2026-10-04
**Python:** 3.10+ (3.12 recommended)

---

## Requirements (all platforms)

| Var | Required | Note |
|---|---|---|
| `API_ID` | yes | my.telegram.org |
| `API_HASH` | yes | my.telegram.org |
| `BOT_TOKEN` | yes | @BotFather |
| `OWNER_ID` | yes | your TG numeric ID |
| `LOG_GROUP_ID` | yes | group/channel for logs |
| `SESSION_KEY` | yes | Fernet key for account sessions |
| `MONGO_URI` | yes | local mongodb://localhost:27017 or Atlas |
| `MONGO_DB` | no | default archvc |
| `VC_WORKERS` | no | default 20 |

Generate SESSION_KEY:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

MongoDB is external for all cloud platforms — use MongoDB Atlas free tier (M0). Connection string format:

    mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

Atlas IP allowlist must include 0.0.0.0/0 for cloud platforms (dynamic IPs).

---

## 1. Railway

Cost: ~$5/mo Hobby plan. Worker service, no sleep.

Steps:

1. railway.app -> New Project -> Deploy from GitHub -> select ArchVcAssistant
2. Railway detects railway.json -> uses Dockerfile builder
3. Add service Variables:
   - API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOG_GROUP_ID, SESSION_KEY
   - MONGO_URI = Atlas connection string
   - MONGO_DB = archvc
   - VC_WORKERS = 20
4. Deploy. Logs tab -> boot sequence visible.

Notes:

- Railway restarts crashed services automatically (ON_FAILURE policy in railway.json).
- Procfile is ignored when railway.json with DOCKERFILE builder is present.
- Custom Dockerfile path: set RAILWAY_DOCKERFILE_PATH variable.

---

## 2. Render

Cost: Starter worker ~$7/mo. Free tier sleeps after 15 min.

Steps:

1. render.com -> New -> Blueprint -> connect repo -> render.yaml detected
2. Fill env vars in dashboard (sync: false fields)
3. Select Background Worker (not Web Service) — bot has no HTTP server
4. Deploy.

Notes:

- Free tier: worker sleeps after 15 min -> use Starter for 24/7.
- MongoDB: Atlas, set MONGO_URI.
- render.yaml defines worker type — Render UI creates it as background worker.

---

## 3. Heroku

Cost: Eco dyno $5/mo (1000 hrs). Worker dyno required.

Steps (container stack):

    heroku create archvc
    heroku stack:set container
    heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... OWNER_ID=... \
      LOG_GROUP_ID=... SESSION_KEY=... MONGO_URI=... MONGO_DB=archvc VC_WORKERS=20
    heroku container:login
    heroku container:push worker
    heroku container:release worker
    heroku ps:scale worker=1

Steps (buildpack, no Docker):

    heroku create archvc
    heroku buildpacks:set heroku/python
    heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... OWNER_ID=... \
      LOG_GROUP_ID=... SESSION_KEY=... MONGO_URI=... MONGO_DB=archvc VC_WORKERS=20
    git push heroku main
    heroku ps:scale worker=1

Notes:

- No free tier since Nov 2022.
- Procfile defines worker: — scale with ps:scale worker=1.
- No native MongoDB — use Atlas, set MONGO_URI.
- Eco dynos sleep after 30 min inactivity — use Basic for 24/7.

---

## 4. Arch Linux VPS

Cost: VPS from Hetzner/DigitalOcean/Contabo — $4-10/mo.

Steps:

    sudo pacman -Syu --noconfirm
    sudo pacman -S --noconfirm python python-pip ffmpeg git

    sudo useradd -m -s /bin/bash archvc
    sudo mkdir -p /opt/ArchVcAssistant
    sudo chown archvc:archvc /opt/ArchVcAssistant

    sudo -u archvc git clone https://github.com/ChiranjibKoch/ArchVcAssistant.git /opt/ArchVcAssistant
    cd /opt/ArchVcAssistant

    sudo -u archvc python -m venv venv
    sudo -u archvc ./venv/bin/pip install --upgrade pip wheel
    sudo -u archvc ./venv/bin/pip install -r requirements.txt

    sudo -u archvc cp .env.example .env
    sudo -u archvc nano .env

    sudo cp archvc.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now archvc.service

    sudo journalctl -u archvc.service -f

Notes:

- Arch does not have mongodb in official repos — use mongodb-bin from AUR.
- Or use MongoDB Atlas — set MONGO_URI.
- archvc.service uses User=archvc — matches created user.

---

## 5. Generic Docker

    docker build -t archvc .
    docker run -d --name archvc \
      --env-file .env \
      --restart unless-stopped \
      archvc

Logs:

    docker logs -f archvc

---

## Platform comparison

| Platform | Type | Cost | Sleeps | Notes |
|---|---|---|---|---|
| Railway | Container | $5/mo Hobby | No | Best DX, auto-restart |
| Render | Background worker | $7/mo Starter | Free tier yes | Web-worker distinction |
| Heroku | Worker dyno | $5/mo Eco | Eco yes | Needs heroku.yml for container |
| Arch VPS | systemd | VPS cost | No | Full control, needs setup |
| Docker | Container | self-host | No | Works anywhere |

Recommendation for 100-150 accounts:

- Railway or Arch VPS.
- Railway — less ops, $5/mo, auto-restart, DOCKERFILE build.
- Arch VPS — full control, ~$5/mo, no rate limits from PaaS, but you manage everything.

---

## Post-deploy checklist

1. Bot /start responds on Telegram (owner ID)
2. Log group receives boot message
3. /stats shows 0 accounts, proxies alive count
4. /addsession <string> adds first account
5. /accounts lists it
6. /joinvc <chat> joins VC
7. /vcreact <chat> 🔥 sends in-call reaction

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| ntgcalls import error | Check ffmpeg installed + build-essential in Docker image |
| MongoServerSelectionError | MONGO_URI wrong, or Atlas IP allowlist missing 0.0.0.0/0 |
| Bot silent on /start | OWNER_ID mismatch, or bot token wrong |
| Permission denied (publickey) on git | Use HTTPS remote: git remote set-url origin https://github.com/... |
| Container builds but exits immediately | .env missing in container, or SESSION_KEY not set |
| bot up never logged | API_ID/HASH wrong — check my.telegram.org |
| Heroku app sleeps | Scale worker dyno: heroku ps:scale worker=1 |

---

## Repo structure

    ArchVcAssistant/
    ├── archd.py                entry point
    ├── Dockerfile
    ├── .dockerignore
    ├── railway.json
    ├── render.yaml
    ├── Procfile
    ├── heroku.yml
    ├── archvc.service          systemd unit
    ├── deploy.sh               VPS helper
    ├── DEPLOYMENT.md           this file
    ├── .env.example
    ├── requirements.txt
    └── archvc/
        ├── conf.py  db.py  logs.py  sudo.py  kbd.py  nav.py
        ├── acct/   store.py  herd.py  login.py
        ├── vc/     queue.py  media.py  calls.py
        ├── prox/   sources.py  fleet.py
        ├── intx/   react.py  views.py  join.py  vcreact.py
        └── cmds/   __init__.py  router.py  sudo.py  acc.py  vc.py  intx.py  sys.py

---

## Coding style

| Rule | Detail |
|---|---|
| No comments | No # comments, no docstrings. Code reads itself. |
| Naming | snake_case functions, PascalCase classes. Verb-based modules (herd, calls, fleet) — not Manager/Engine/Handler. |
| Imports | from pyrogram import Client, filters — PyPI is kurigram, import is pyrogram (drop-in fork). |
| UI text | Small caps (ᴠᴄ ᴊᴏɪɴ, ᴀᴄᴄᴏᴜɴᴛꜱ), English only. Values (ID, phone, chat, URL) regular font. |
| Separators | ━━━━━━━━━━━━━━━━━━━━ heavy box drawing. |
| Bullets | ◈ ▣ ✦ ⚠ |
| Layout | Frozen dataclass conf, property-based DB access, async everywhere, module-per-concern. |
| Fallbacks | Silent degrade — colored button 3-mode, proxy health, retry queue. |
| Log strings | Small caps labels + regular values. |

---

## Updates

Push to main -> auto-deploy on Railway/Render/Heroku (if enabled).

For VPS:

    cd /opt/ArchVcAssistant
    sudo -u archvc git pull
    sudo ./deploy.sh

---

## License

Private — ChiranjibKoch

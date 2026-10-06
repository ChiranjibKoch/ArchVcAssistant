# ArchVcAssistant

Multi-account Telegram voice chat automation bot.

**Repo:** https://github.com/ChiranjibKoch/ArchVcAssistant

---

## Deploy

### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/ChiranjibKoch/ArchVcAssistant)

Button click karo, Heroku env vars form dikhayega. Bharke Deploy dabao. Container stack build hoti hai, worker dyno scale manual:

    heroku ps:scale worker=1 -a <app-name>

### Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template?template=https://github.com/ChiranjibKoch/ArchVcAssistant)

### Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ChiranjibKoch/ArchVcAssistant)

---

## Requirements

| Var | Required | Note |
|---|---|---|
| API_ID | yes | my.telegram.org |
| API_HASH | yes | my.telegram.org |
| BOT_TOKEN | yes | @BotFather |
| OWNER_ID | yes | your Telegram numeric ID |
| LOG_GROUP_ID | yes | group or channel for logs |
| SESSION_KEY | yes | Fernet key for account sessions |
| MONGO_URI | yes | MongoDB connection string (Atlas) |
| MONGO_DB | no | default archvc |
| VC_WORKERS | no | default 20 |

Generate SESSION_KEY:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

---

## Commands

| Command | Action |
|---|---|
| /start | Root menu |
| /addsudo <id> | Add sudo (owner) |
| /rmsudo <id> | Remove sudo (owner) |
| /sudolist | Sudo list |
| /addsession <string> | Import session |
| /addotp +91... | Start phone OTP flow |
| /otp <code> | Submit OTP |
| /2fa <pwd> | Submit 2FA password |
| /accounts | Herd status |
| /joinvc <chat> | Bulk VC join, automute |
| /leavevc <chat> | Bulk leave |
| /vcreact <chat> <emoji> | In-call reactions |
| /play <chat> <source> | Play audio |
| /pause <chat> | Pause stream |
| /mute <chat> | Bulk mute |
| /unmute <chat> | Bulk unmute |
| /rx <url> <emoji> | Batch message reactions |
| /views <url> <n> [emoji] | View boost |
| /stats | System health |
| /proxies | Proxy fleet |
| /setloggroup <id> | Set log group (owner) |

---

## Development

    git clone https://github.com/ChiranjibKoch/ArchVcAssistant.git
    cd ArchVcAssistant
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    nano .env
    python archd.py

Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Style

| Rule | Detail |
|---|---|
| No comments | Code reads itself |
| Naming | snake_case functions, PascalCase classes, verb-based modules |
| Imports | PyPI is kurigram, import is pyrogram (drop-in fork) |
| UI text | Small caps labels, regular values, English only |

---

## License

Private — ChiranjibKoch

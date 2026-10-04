#!/usr/bin/env bash
set -e

APP_DIR=/opt/ArchVcAssistant
VENV=$APP_DIR/venv

if [ ! -d "$VENV" ]; then
    python -m venv "$VENV"
fi

source "$VENV/bin/activate"
pip install --upgrade pip wheel
pip install -r "$APP_DIR/requirements.txt"

if [ ! -f "$APP_DIR/.env" ]; then
    echo "No .env found at $APP_DIR/.env — create it before starting."
    exit 1
fi

sudo systemctl daemon-reload
sudo systemctl enable archvc.service
sudo systemctl restart archvc.service

echo "archvc deployed."
sudo systemctl status archvc.service --no-pager | head -20

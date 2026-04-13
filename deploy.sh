#!/usr/bin/env bash
set -euo pipefail
# Restart Mason agent (Telegram) and FastAPI dashboard API after deploy.
sudo systemctl restart mason-agent
sudo systemctl restart mason-api

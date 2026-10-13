#!/usr/bin/env bash
# Refresh the Portfolio dashboard: edit data.json (no figures!), then run this.
set -e; cd "$(dirname "$0")"
python3 build.py
git add -A && git commit -qm "Update $(date '+%F %H:%M')" || true
git push -q origin main && echo "Live: https://webermanapps.github.io/portfolio-dashboard/"

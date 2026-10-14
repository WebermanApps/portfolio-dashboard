#!/usr/bin/env bash
# Refresh the Portfolio dashboard (main page + six private sub-dashboards). Used by the Morning Report routine (due by 5:00 AM ICT).
# Morning Report only: the Evening Report was retired Oct 14 2026 (no evening-report.sh, no Evening section, report.json is always Morning).
# Main page: edit data.json (no figures!). Sub-dashboards rebuild from the live data files.
# Ready To Swipe shelf: shelf.json (kit deck-shelf v2); build.py syncs unfinished decks into shelf.json pinned. Refill steps: SUBMIT.md.
# Encrypted pages publish only when PORTFOLIO_DASH_PASSWORD is set; plaintext stays in ../dashboard-private (never in this repo).
set -e; cd "$(dirname "$0")"
python3 build.py
# safety: refuse to commit anything that is not the public page, tokens, templates, scripts, shelf, or ciphertext pages
if git ls-files --others --modified --exclude-standard | grep -vE '^(index\.html|data\.json|template\.html|sub_template\.html|lock_template\.html|sub\.js|subdash\.py|build\.py|update\.sh|brand-tokens\.css|robots\.txt|ptr\.js|\.gitignore|s/[a-z]+\.html|screenshots/.*\.png|report\.json|routines\.json|shelf\.json|shelf-sources/[a-z0-9_-]+\.(json|py)|SUBMIT\.md|README\.md|morning-report-on-dashboard\.sh)$'; then echo "Unexpected file above; not publishing"; exit 1; fi
for f in s/*.html; do [ -e "$f" ] && ! grep -q 'const S="' "$f" && { echo "$f is not an encrypted wrapper; not publishing"; exit 1; }; done
git add -A && git commit -qm "Update $(date '+%F %H:%M')" || true
git push -q origin main && echo "Live: https://webermanapps.github.io/portfolio-dashboard/"

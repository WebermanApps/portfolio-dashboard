#!/usr/bin/env bash
# Evening Report publish (18:00 ICT). Edit data.json report.evening + title first, then run this.
# Writes public report.json (type + posted_at ICT, no figures) via build.py and publishes.
set -euo pipefail
cd "$(dirname "$0")"
export PORTFOLIO_REPORT_TYPE="Evening Report"
exec ./update.sh

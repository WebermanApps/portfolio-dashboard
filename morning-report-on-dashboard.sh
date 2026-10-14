#!/usr/bin/env bash
# Morning Report publish (by 5:00 ICT). Edit data.json report.morning + title first, then run this.
# Writes public report.json (type + posted_at ICT, no figures) via build.py and publishes.
set -euo pipefail
cd "$(dirname "$0")"
export PORTFOLIO_REPORT_TYPE="Morning Report"
exec ./update.sh

#!/bin/bash
# Runs the dashboard export once, standalone -- no Claude session required.
# Installed as a persistent launchd job (see scripts/README.md); this script
# is what the job actually invokes, kept here (version-controlled) rather
# than inlined in the plist so it can be run and edited like any other repo
# script, e.g. `bash scripts/refresh_dashboard.sh` for a manual one-off run.
set -euo pipefail

REPO_ROOT="/Users/imeish/quant trading"
LOG_DIR="$REPO_ROOT/scripts/logs"
mkdir -p "$LOG_DIR"

cd "$REPO_ROOT/backend"
source "$REPO_ROOT/.venv/bin/activate"

STAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
set +e
python -m dashboard.export >> "$LOG_DIR/refresh_$STAMP.log" 2>&1
EXIT_CODE=$?
set -e

# Keep the last 30 logs only -- this runs daily forever, don't let logs grow
# unbounded. `|| true`: an empty/short log directory makes `ls` exit non-zero
# (no glob match), which -- combined with `pipefail` -- would otherwise abort
# this cleanup step under `set -e` even though the actual export above
# already completed; cleanup failing is not itself a reason to report failure.
ls -t "$LOG_DIR"/refresh_*.log 2>/dev/null | tail -n +31 | xargs -r rm -- || true

exit $EXIT_CODE

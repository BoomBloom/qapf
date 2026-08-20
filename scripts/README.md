# scripts/

Standalone operational scripts — things that need to run reliably without a
Claude Code session attached, unlike the wayfinder scratch scripts under
`.scratch/wayfinder-real-capital/`, which are one-off validation exercises.

## refresh_dashboard.sh

Runs `python -m dashboard.export` (the full pipeline, ~60-90s) and logs to
`scripts/logs/`, keeping the last 30 log files.

**Installed as a persistent macOS `launchd` job** (2026-08-20), not a Claude
Code cron job — Claude Code's own cron tool is session-scoped (dies when the
session ends, auto-expires after 7 days regardless), which would silently
stop working the first time a terminal closes. `launchd` runs independent of
any session, through reboots, indefinitely.

- Job label: `com.qapf.dashboard-refresh`
- Plist: `~/Library/LaunchAgents/com.qapf.dashboard-refresh.plist`
- Schedule: daily at 06:15 local time
- Manual one-off run: `bash scripts/refresh_dashboard.sh`
- Check it's loaded: `launchctl list | grep qapf`
- Stop it: `launchctl unload ~/Library/LaunchAgents/com.qapf.dashboard-refresh.plist`
- Restart it (e.g. after editing the schedule): unload, then
  `launchctl load ~/Library/LaunchAgents/com.qapf.dashboard-refresh.plist`
- Logs: `scripts/logs/refresh_*.log` (script's own log) and
  `scripts/logs/launchd.{out,err}.log` (launchd's stdout/stderr capture,
  should stay empty if the script's own logging is working correctly)

Only refreshes the dashboard snapshot — does not run Agent 1 (orchestrator)
or Agent 8 (codegen), both of which make real LLM calls and are deliberately
excluded from the automatic export (see `backend/dashboard/export.py`'s
`orchestrator`/`codegen` sections) so a scheduled job can't silently rack up
API cost. Run those manually when you actually want a fresh CIO memo or want
to exercise codegen.

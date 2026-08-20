---
name: qapf-prime
description: Orients Claude in the QAPF (Quantitative Autonomous Prop Firm) codebase before planning or implementing ANY agent work, risk-module work, or Qlib/TradingAgents integration work. Loads the ground rules, identifies which of the 16 agents the task concerns and its build strategy (adapt/extend/build custom), checks what's already built vs. not, and surfaces known gotchas (Qlib expression-engine bug, CRO isolation, date-offset-not-shift, pip-vs-source Qlib version drift) before code gets written. Use this whenever a task touches backend/agents/, backend/risk/, backend/core/, reference/qlib/, reference/TradingAgents/, or mentions building/extending/fixing one of the numbered agents, the CRO, the orchestrator, the backtester, or the portfolio optimizer in QAPF. Trigger even if the user doesn't say "prime" explicitly — any substantive QAPF implementation or planning task should start here.
---

# QAPF Prime

Orientation pass for the QAPF repo. Run this **before** planning or writing any code for a task that
touches agent work, risk, or the Qlib/TradingAgents forks. Don't skip it because the task "seems simple"
— this project has already been bitten twice by skipping verification (see CLAUDE.md's working
principles), and most of the bugs on record here were silent, not loud.

Always read the live files — never rely on a cached summary of them from earlier in the conversation or
from this skill. CLAUDE.md and README.md are the source of truth and they get updated as agents get built.

## Step 1 — Load ground rules

Read `CLAUDE.md` at the repo root if it isn't already in context. Note in particular:
- The architecture map (what's built vs. not, as of the last update)
- Async-first, Pydantic v2, one-folder-per-agent, no-placeholder-data
- CRO isolation rule
- The date-offset-not-positional-shift rule for time series
- "Never commit without being asked"

## Step 2 — Identify the agent and its build strategy

If the task concerns one of the 16 agents (building a new one, extending an existing one, fixing a bug in
one), read the **Agent Roster → Build Strategy** table in `README.md` and pin down, explicitly:

- Which agent number and name this is
- Its **Call**: Adapt / Adapt Qlib / Adapt heavily / Extend Qlib / Build custom / Build custom (defer) /
  Build custom, isolated
- Its **Basis** — what existing code (TradingAgents or Qlib) it should build on, if any

Do not assume a build strategy that applies to one agent applies to another — the README is explicit that
this is per-agent, not uniform. If the task doesn't name an agent number, ask which one before proceeding
unless it's obvious from context (e.g. "add cointegration checks" is clearly Agent 4).

## Step 3 — Check what's already built

Cross-check the architecture map in CLAUDE.md (and the "Roadmap" section of README.md if more detail is
needed) for the current state of that agent and any adjacent code:

- Is this agent already built? If so, read its existing folder (`backend/agents/<name>/`) before
  proposing changes — don't re-architect something that's already been verified working.
- Does the task overlap with a piece of infrastructure that isn't built yet (`backend/core/`,
  `backend/api/`)? If so, flag that dependency explicitly rather than building around it silently.

## Step 4 — Surface relevant gotchas

Check whether the task touches any of the following, and if so, act accordingly:

- **Touches Qlib in any way** (imports `qlib`, uses its expression engine, backtest, or optimizer) → read
  `.claude/references/qlib-known-issues.md` in full before writing code. In particular: rolling-window
  expression operators (`Ref`, `Mean`, `Std`, `Corr`, `Rank`) silently return empty results — don't use
  them without checking the reference doc's current guidance. Any script that imports qlib and runs
  directly needs `if __name__ == "__main__":` guarding its entry point.
- **Touches `backend/risk/` (the CRO)** → restate the isolation rule out loud in your plan: this module
  must never import from `backend/core/` or any LangGraph module. It reads state; it doesn't join the
  debate. If `backend/risk/` exists by the time this runs, verify the import boundary holds (grep for
  forbidden imports) rather than assuming it does.
- **Computes a year-over-year / month-over-month / any time-based change** → use `pd.DateOffset` +
  `.asof()`, never a positional `.shift(n)`. Real series have gaps; a positional shift silently reports
  the wrong period.
- **Touches TradingAgents' orchestration graph** → read
  `reference/TradingAgents/tradingagents/graph/` first. `backend/core/state_graph.py` (Agent 1, built
  2026-08-19) already forks `GraphSetup`/`StateGraph` — read its module docstring before adding a node or
  assuming a second orchestration mechanism is needed. It deliberately has only ONE LLM node
  (`cio_synthesis`); every other node wraps an already-built deterministic agent, on purpose.
- **Runs any script under `reference/qlib/scripts/`** (data collectors, not `backend/`'s own agents) →
  the pip-installed `pyqlib` package and the local `reference/qlib` checkout can be different versions.
  `python -m agents.<name>` in `backend/` correctly uses the pip-installed package and is unaffected, but
  a standalone `reference/qlib/scripts/...` collector may need `reference/qlib` prepended to
  `PYTHONPATH` ahead of site-packages to resolve `import qlib` to the newer local checkout (hit this
  building the point-in-time universe collector, 2026-08-19 — `qlib.utils.pickle_utils` doesn't exist in
  the pip release). Isolated to that one script's subprocess; never change what `backend/` itself imports.
- **Scrapes a live web page for a one-time or periodic data build** → don't trust that the page still has
  the structure an older script assumed. Wikipedia's S&P 500 "Selected changes" table was removed from
  the live article entirely between when the PIT-universe research was written and when the collector was
  actually run (2026-08-19) — verify structure against the live page (or a specific historical revision)
  before debugging column-index math, don't assume the earlier research's description still holds.

## Step 5 — Verify, don't inherit

This project has already been corrected twice by reading actual source instead of trusting
README-generation or prior AI-written docs (see CLAUDE.md's "Working principles"). Before treating any
claim in README.md, CLAUDE.md, or an earlier planning doc as settled:
- If it's a claim about what a library does or doesn't support, check the actual source in `reference/`.
- If it's a claim about integration compatibility or performance that isn't marked "verified" in
  README.md's Phase 0 spike results, treat it as unverified and say so.
- Restating an existing idea with no new verification adds nothing — only add it to the plan if it's
  either independently confirmed or structurally necessary.

## Step 6 — Give a short session brief before implementing

Before writing any code, summarize back in a few lines:
- Agent/module in scope and its build strategy
- What already exists vs. what needs building
- Any gotchas from Step 4 that apply
- Anything from Step 5 that's an open question rather than settled fact

Then proceed to planning/implementation. Keep scope tight — per CLAUDE.md, a bug fix doesn't need
surrounding cleanup, and agents should be built one at a time per the phased roadmap, not several at once.

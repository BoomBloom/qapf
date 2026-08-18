# QAPF — Quantitative Autonomous Prop Firm

## What this is
A local-first autonomous quant trading platform: a prop-firm-style AI workforce (16 agents as of
2026-08-18, not capped at a round number) covering research, statistics,
strategy building, backtesting, risk enforcement, portfolio allocation, execution, and operations —
built on top of two forked upstreams (TradingAgents for orchestration/LLM judgment, Qlib for
data/backtest/execution math) plus custom agents for what neither provides. Full rationale, the
agent-by-agent build strategy, and the phased roadmap live in [README.md](README.md) — this file is the
lean, always-on summary; read the README for the "why."

**Stack:** Python 3.12 (FastAPI, Pydantic v2, LangGraph) + Next.js frontend (Phase 1+) + Postgres/Redis
(Phase 1+, not yet stood up).

## Architecture map

```
reference/TradingAgents/  Apache-2.0 fork basis — LangGraph orchestration graph + LLM analyst agents.
                          Read reference/TradingAgents/tradingagents/graph/ before touching orchestration.
reference/qlib/           MIT fork basis — data/backtest/execution/optimization engine.
                          Read .claude/references/qlib-known-issues.md BEFORE using its expression engine.
backend/core/             (not yet built) event_bus.py, state_graph.py (our fork of TradingAgents' graph), config.py
backend/api/              (not yet built) FastAPI app: main.py, routes/, websockets/
backend/models/           (not yet built) Pydantic v2 schemas — inter-agent events + API DTOs
backend/services/         DROPPED (2026-08-18) — Qlib usage lives inside each owning agent's own folder
                          instead (Agent 9's actual precedent). See "Where new code goes" below.
backend/agents/research/  BUILT & verified live (2026-08-18) — arXiv + GitHub ingestion (Agent 3).
                          See backend/agents/research/pipeline.py. Run: `python -m agents.research`.
backend/agents/stats/     BUILT & verified live (2026-08-18) — stationarity (ADF/KPSS), cointegration
                          (Engle-Granger + Johansen), Deflated Sharpe Ratio (Agent 4). Regime-switching/
                          EVT/copulas/Bayesian are in the original spec but deliberately deferred, not
                          built. See backend/agents/stats/toolkit.py. Run: `python -m agents.stats`.
backend/agents/macro/     BUILT & verified live (2026-08-18) — keyless FRED ingestion, deterministic
                          growth x inflation regime classification, yfinance fundamentals (Agent 6).
                          NLP/sentiment scoring from the original spec is NOT built (needs an LLM key
                          or a local transformer) — it's an explicit seam, not a stub.
                          Run: `python -m agents.macro`.
backend/agents/alpha/     BUILT & verified live (2026-08-18) — pandas factor computation (momentum 12-1,
                          5d reversal, low-vol, volume trend), cross-sectional rank normalization to
                          [-1,+1], regime-conditional weighting that CONSUMES Agent 6's output (Agent 7).
                          Deliberately avoids Qlib's broken expression engine. Run: `python -m agents.alpha`.
backend/agents/backtest/  BUILT & verified live (2026-08-18) — walk-forward backtest chaining Agent 6 ->
                          Agent 7 -> Qlib's verified backtest engine -> Agent 4's DSR (Agent 9). Runs
                          2018-2020 (spans COVID) on Qlib's own bundled price data for execution, NOT
                          live yfinance -- see backtest/walkforward.py's module docstring for why.
                          Run: `python -m agents.backtest`.
backend/risk/             BUILT & verified live (2026-08-18) — VaR/CVaR (historical + parametric),
                          drawdown tracking, hard kill-switch (Agent 10/CRO). Import-isolation enforced by
                          an AST-based test, not just convention. Run: `python -m risk`.
backend/agents/           other 10 agents not yet built (incl. Agents 13-16, added 2026-08-18 to cover
                          compliance, model risk, data reliability, and treasury) — see README's roster
.claude/references/       On-demand detail, e.g. qlib-known-issues.md. Add new ones here as they recur.
.venv/                    Python 3.12 (NOT system Python, which is 3.14 — see qlib-known-issues.md)
```

**Agents 3, 4, 6, 7, 9, and 10 exist so far** (research, stats, macro, alpha, backtest, risk/CRO — see
each row above for what's built vs. deferred within it). The rest of the architecture map is the target
layout — build
into it, don't invent a different one.

## Ground rules (specific decisions, not slogans)

- **Agent build strategy is per-agent, not uniform** — some agents adapt/extend the forked repos, some
  are fully custom. Check the "Agent Roster → Build Strategy" table in README.md before starting any
  agent's implementation; don't assume a pattern that applies to one agent applies to all twelve.
- **CRO isolation is architecturally enforced, not just a convention.** `backend/risk/` must never
  import from `backend/core/` (the LangGraph state graph) or any LangGraph module. It reads state; it
  does not join the debate. Verify this with an import-boundary check (e.g. a lint rule or a test that
  greps for forbidden imports) once `backend/risk/` exists — don't rely on remembering the rule.
- **Don't trust Qlib's expression engine (`Ref`, `Mean`, `Std`, `Corr`, `Rank`, ...) without reading
  `.claude/references/qlib-known-issues.md` first.** It has a verified silent-failure bug under the
  current numpy/pandas stack. Plain field access (`$close`, `$volume`) and the backtest/account/exchange
  engine are confirmed working and fast; rolling-window expression operators are not, until that
  reference doc says otherwise.
- **Any script that imports `qlib` and is run directly (not just imported) needs
  `if __name__ == "__main__":` around its entry point.** Qlib uses `multiprocessing` internally; without
  the guard, macOS's spawn start method re-imports and re-executes the whole script per worker, which
  looks exactly like a silent hang (verified — cost 15 minutes of wall-clock time once, see
  qlib-known-issues.md). This is a Python/macOS multiprocessing gotcha, not a Qlib defect.
- **Never compute a time-based change with a positional shift.** Use date offsets (`pd.DateOffset` +
  `.asof()`), not `.shift(n)`, for anything year-over-year / month-over-month. Real economic series have
  gaps — CPIAUCSL is missing `2025-10-01`, which made a `shift(12)` "YoY" silently report a 13-month
  change (3.54% vs the true 3.30%). This class of bug produces plausible-looking wrong numbers rather
  than errors, so it will not announce itself. There's a regression check for it in
  `backend/agents/macro/__main__.py`.
- **One folder per agent under `backend/agents/<name>/`.** Never combine two agents' logic in one file
  (this was already a stated intent across every prior planning doc for this project — keep it).
- **Async first.** All network/DB/Redis operations use `async`/`await`.
- **Pydantic v2 everywhere** for Python API/event contracts; strict TypeScript interfaces on the frontend.
- **No placeholder data.** Dashboard mocks use structurally realistic values (real-shaped OHLCV,
  plausible non-zero Sharpe) when live data is disconnected — never empty/zero stubs.
- **Respect upstream licenses.** Retain Apache-2.0 (TradingAgents) and MIT (Qlib) notices in any forked
  or vendored code.

## Working principles (how to operate in this repo)

- **Verify before building on a claim — including claims from other AI tools.** This project has
  accumulated multiple AI-generated architecture blueprints (see README's "Rejected/Deferred sources"
  and the note on the DeepSeek/Qwen/Gemini docs). Treat any such document as a hypothesis to check
  against the actual repo/source/running code, not as ground truth — this project was already corrected
  twice by actually reading Qlib's and TradingAgents' source instead of trusting their READMEs.
  Restated ideas with no new verification add no value; only fold in details that are structurally
  useful or independently confirmed. (Inferred from how this project has been run so far, not yet
  explicitly confirmed by the user — revisit if that's not the intended working style.)
- **Spike risky/uncertain integration points before committing architecture to them**, the same way
  Phase 0 was actually run (venv+Qlib install, real data load, real backtest attempt) rather than
  assumed from documentation. If a dependency's compatibility, performance, or correctness is unverified,
  say so explicitly rather than presenting a plan as settled.
- **Keep scope tight.** A bug fix doesn't need surrounding cleanup; don't build agents 2 through 12
  simultaneously when the roadmap says build one phase at a time.
- **Never commit without being asked.** Git is initialized; stage freely, but leave the commit itself
  for an explicit instruction.

## Commands

- Activate the environment: `source .venv/bin/activate` (must be the Python-3.12-based venv — see
  qlib-known-issues.md for why system Python 3.14 doesn't work for Qlib).
- Install backend deps (editable): `pip install -e ./backend`
- Run the research agent manually: `cd backend && python -m agents.research` (set `GITHUB_TOKEN` env
  var first to avoid GitHub's unauthenticated search rate limit — 10 req/min).
- Run the stats agent manually: `cd backend && python -m agents.stats` (downloads ~2y of KO/PEP/XOM
  daily data via yfinance; no API key needed).
- Run the macro agent manually: `cd backend && python -m agents.macro` (live FRED + yfinance; no API
  key needed — uses FRED's keyless CSV endpoint, not the keyed JSON API).
- Run the alpha agent manually: `cd backend && python -m agents.alpha` (pulls the live regime from
  Agent 6, then runs bounds / factor-direction / look-ahead / regime-sensitivity checks).
- Run the backtest agent manually: `cd backend && python -m agents.backtest` (walk-forward backtest,
  2018-2020, ~30-60s; needs `qlib.init()` against the bundled US dataset, already downloaded).
- Run the CRO manually: `cd backend && python -m risk` (~30-60s — reruns Agent 9's backtest as a real-data
  test fixture, not a risk-engine dependency). Reports the kill-switch illustration and stops there until
  `max_drawdown_pct`/`max_daily_loss_pct` are set in `__main__.py` — a risk-appetite decision, deliberately
  not defaulted by the agent.
- No test suite or lint config exists yet. Add real commands here the moment they do — don't leave this
  section aspirational.

## On-demand references
- **`/qapf-prime` skill** (`.claude/skills/qapf-prime/`) — the orientation pass to run before planning or
  implementing any agent / risk / Qlib-integration work. Loads ground rules, pins down the agent's build
  strategy, checks what's already built, and surfaces the known gotchas. Prefer invoking it over
  re-deriving this context by hand.
- `.claude/references/qlib-known-issues.md` — Qlib expression-engine bug, stale sample data, and the
  multiprocessing entry-point guard. Read before any Qlib-touching code.
- `README.md` — full architecture rationale, agent-by-agent build strategy, phased roadmap, rejected
  sources.

## Where new code goes (the seams)
- A new custom agent → `backend/agents/<name>/`, exposing a `run(state) -> state` entry point matching
  the LangGraph node signature used in `reference/TradingAgents/tradingagents/graph/setup.py`.
- A new graph node wiring an agent into the orchestrator → `backend/core/state_graph.py` (our fork of
  `GraphSetup`), following the existing node/edge pattern — don't invent a second orchestration
  mechanism alongside it.
- A new Qlib-backed capability (backtest variant, optimizer extension) → directly inside the owning
  agent's `backend/agents/<name>/` module, importing `reference/qlib/qlib/...` there rather than
  reimplementing it (unless `qlib-known-issues.md` says that part of Qlib is broken). `backend/services/`
  was the original plan but Agent 9 never used it — it imports `qlib` straight into `backend/agents/
  backtest/`, and that's the actual precedent now (decided 2026-08-18, see
  `docs/qapf-remaining-agents.spec.md`). Don't create `backend/services/` for this; Agents 2, 11, and 12
  follow the same rule.
- A new API/WebSocket surface → `backend/api/routes/` or `backend/api/websockets/`.

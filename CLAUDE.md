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
backend/core/             BUILT & verified live (2026-08-19) — state_graph.py (Agent 1, Lead Orchestrator),
                          config.py. LangGraph pipeline: macro -> alpha -> portfolio -> risk_gate ->
                          [execution -> compliance] -> cio_synthesis. Only ONE LLM node (cio_synthesis,
                          Anthropic claude-sonnet-5) — every other node wraps an already-built
                          deterministic agent; see state_graph.py's docstring for why 3/4/9/12/14/15 are
                          deliberately NOT graph nodes. risk_gate is also wayfinder ticket 12's
                          kill-switch enforcement: a halted state skips execution/compliance entirely
                          (zero orders constructed, not just zero sent), verified against Agent 9's real
                          2018-2020 COVID-crash backtest. event_bus.py not built — no consumer yet.
                          Run: `python -m core`.
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
backend/agents/portfolio/ BUILT & verified live (2026-08-19) — turns Agent 7's signals into position sizes
                          via Qlib's PortfolioOptimizer + Ledoit-Wolf shrinkage covariance, with
                          regime-conditional optimizer choice (Agent 2). LONG-ONLY by deliberate
                          decision (Qlib's optimizer hard-codes no-shorting; margin/borrow are
                          unmodeled) — see allocator.py's docstring. Run: `python -m agents.portfolio`.
backend/agents/backtest/  BUILT & verified live (2026-08-18) — walk-forward backtest chaining Agent 6 ->
                          Agent 7 -> Qlib's verified backtest engine -> Agent 4's DSR (Agent 9). Runs
                          2018-2020 (spans COVID) on Qlib's own bundled price data for execution, NOT
                          live yfinance -- see backtest/walkforward.py's module docstring for why.
                          Run: `python -m agents.backtest`.
backend/risk/             BUILT & verified live (2026-08-18) — VaR/CVaR (historical + parametric),
                          drawdown tracking, hard kill-switch (Agent 10/CRO). Import-isolation enforced by
                          an AST-based test, not just convention. Run: `python -m risk`.
backend/agents/execution/ BUILT (2026-08-19) — TWAP/VWAP scheduling + square-root market impact (Agent 11).
backend/agents/operations/ BUILT (2026-08-19) — target-vs-fill reconciliation, PnL attribution as an
                          identity that must close to zero (Agent 12).
backend/agents/compliance/ BUILT (2026-08-19) — restricted list, position/sector limits, wash-trading
                          patterns, audit trail. Separate from the CRO by design (Agent 13).
backend/agents/modelrisk/ BUILT (2026-08-19) — independently challenges Agent 9: decay, regime coverage,
                          return concentration (Agent 14).
backend/agents/datainfra/ BUILT (2026-08-19) — feed staleness/gap/schema-drift monitoring; its regression
                          suite re-detects all four data defects this project actually hit (Agent 15).
backend/dashboard/        BUILT (2026-08-19) — export.py runs the whole pipeline and writes
                          frontend/data/snapshot.json. All dashboard numbers come from here.
frontend/index.html       BUILT (2026-08-19) — single-page dashboard over the snapshot. Serve it:
                          `python3 -m http.server 8402 --directory frontend` (fetch() needs http, not file://).
backend/agents/codegen/   BUILT & verified live (2026-08-19) — Agent 8. Groq-tier code generation,
                          escalating to Anthropic only after 2 failed Groq attempts (cost discipline).
                          Never self-grades: every attempt runs in a subprocess against a caller-supplied
                          verification script, trusting only its exit code. Demo generates the symmetric
                          CUSUM filter (López de Prado, AFML), verified against an independently
                          hand-traced case, then landed for real in agents.stats.toolkit.cusum_filter().
                          Run: `python -m agents.codegen`.
backend/agents/           Agents 5 and 16 deferred by policy
.claude/references/       On-demand detail, e.g. qlib-known-issues.md. Add new ones here as they recur.
.venv/                    Python 3.12 (NOT system Python, which is 3.14 — see qlib-known-issues.md)
```

**14 of 16 agents are built** (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15). Only 5 and 16 remain,
both deferred by policy — see each row above. The rest of the architecture map is the target layout —
build into it, don't invent a different one.

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
- Run the portfolio agent manually: `cd backend && python -m agents.portfolio` (chains Agent 6 -> 7 -> 2
  on live data; runs bounds / position-cap / shrinkage-conditioning / regime / all-cash checks).
- Run any agent: `cd backend && python -m agents.<name>` — research, stats, macro, alpha, portfolio,
  execution, operations, compliance, modelrisk, datainfra, backtest (and `python -m risk` for the CRO).
- Run the orchestrator manually: `cd backend && python -m core` (Agent 1 — chains macro -> alpha ->
  portfolio -> risk_gate -> execution -> compliance -> a real Anthropic-backed CIO synthesis; makes one
  paid Claude call per invocation, ~10-15s, real cost — see backend/core/config.py's two-tier LLM note
  before running this often). Needs GROQ_API_KEY and ANTHROPIC_API_KEY in `.env`.
- Run the code-gen agent manually: `cd backend && python -m agents.codegen` (Agent 8 — generates and
  verifies the CUSUM filter from a natural-language spec; Groq-tier by default, ~5-10s, escalates to a
  paid Anthropic call only if 2 Groq attempts fail verification).
- Regenerate the dashboard data: `cd backend && python -m dashboard.export` (~60s, runs everything).
- Serve the dashboard: `python3 -m http.server 8402 --directory frontend` then open localhost:8402.
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

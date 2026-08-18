# Quantitative Autonomous Prop Firm (QAPF)

## Mission
A local-first, autonomous quant trading platform where an AI workforce covers
the full lifecycle of a prop trading firm — research, statistics, strategy
building, backtesting, risk enforcement, portfolio allocation, execution, and
operations. The org chart is modeled on a real prop firm's, not capped at a
round number: **16 agents** as of 2026-08-18 (started at 12; four more were
added because a real prop firm has functions the original 12 didn't cover —
see "Agents 13-16" below).

---

## Foundation: what we actually have (verified, not assumed)

Both reference repos were cloned into `reference/` and their **source code was
read** — not just their READMEs. Both are permissively licensed and safe to
fork or vendor.

| | `reference/TradingAgents` | `reference/qlib` |
|---|---|---|
| License | Apache-2.0 | MIT |
| Upstream | TauricResearch/TradingAgents | microsoft/qlib |
| Last commit (fork) | 2026-07-18 (v0.3.1, active) | mirrors upstream |
| Python | >= 3.10 | >= 3.8 (cython build) |
| Layer | **LLM judgment** | **Math / data / simulation** |

### The key structural finding

**These two repos do not overlap at all.** That's the most useful thing learned
from reading them, and it's good news — they compose instead of competing:

- **TradingAgents is a reasoning pipeline with no quant engine.** It produces a
  BUY/SELL/HOLD decision for one ticker on one date via LLM debate. It declares
  `backtrader` as a dependency but **never imports it** (verified by grep — zero
  usages). There is no backtest, no Sharpe calculation, no portfolio
  simulation anywhere in it. Its "prop firm" framing is org-chart mimicry, not
  quant rigor.
- **Qlib is a quant engine with no LLM layer.** Real event-driven backtesting
  (`qlib/backtest/` — account, position, exchange, executor, report), a
  data/factor expression engine (`qlib/data/`), and MLflow-based experiment
  tracking (`qlib/workflow/`). No agents, no LLM calls.

So the architecture is: **TradingAgents supplies the orchestration + judgment
layer; Qlib supplies the math + validation + execution-simulation layer.** Our
custom work is the connective tissue plus the pieces neither has.

### Two corrections from reading the source

1. **Qlib already has portfolio optimization.** `qlib/contrib/strategy/optimizer/optimizer.py`
   ships a `PortfolioOptimizer` implementing global minimum variance (`gmv`),
   mean-variance (`mvo`), risk parity (`rp`), and inverse volatility (`inv`).
   It also ships serious covariance estimation in `qlib/model/riskmodel/`
   (shrinkage, POET, structured estimators), and `cvxpy` is already a
   dependency. Agent 2 is therefore an **extend**, not a from-scratch build —
   only Black-Litterman, hierarchical risk parity, and Kelly sizing need adding.
2. **Neither repo has any econometrics/statistics layer.** Grepping both trees
   for `cointegration`, `adfuller`, `statsmodels`, and "deflated sharpe" hits
   exactly one incidental file. Agent 4 is confirmed a genuine from-scratch
   build on `statsmodels`/`arch`.

### Phase 0 spike results (verified against a running install, not just source-reading)

The Phase 0 integration spike (see Roadmap below) was actually run, not just planned. Findings:

- **Environment:** The host's only Python was 3.14, too new for `pyqlib` (wheels only go up to cp312 —
  it's an Alpha-status package with Cython extensions). Fixed by installing Python 3.12 via Homebrew
  into an isolated `.venv`, without touching system Python. `pyqlib==0.9.7` then installs cleanly.
- **Data layer works:** `qlib.init()` against the real downloaded US sample dataset correctly loads
  8,994 instruments with real prices (verified AAPL OHLCV against known values).
- **The expression engine has a real, silent bug.** `D.features(..., ["$close"])` works, but any
  expression using a rolling-window operator — `Ref($close, 1)`, and by extension the `Mean`/`Std`/
  `Corr`/`Rank` operators that Qlib's own Alpha158/Alpha360 factor libraries are built from — silently
  returns an **empty result with no exception**, under the numpy/pandas versions pip naturally installs
  alongside `pyqlib` today. Root-caused (see `.claude/references/qlib-known-issues.md`); this is not a
  local misconfiguration, it reproduces from a clean install. Since this operator underlies nearly all
  of Qlib's factor/alpha-mining value, **this downgrades confidence in "extend Qlib for Agent 7" and
  raises the odds we need Polars/hand-rolled code for the factor layer, keeping Qlib only for the parts
  confirmed to work (raw field access, backtest/account/exchange primitives, portfolio optimizer).**
- **Downgrading pandas to dodge the bug cascades into a worse conflict:** an older pandas forces pip to
  downgrade numpy below 2.0, which breaks scipy/cvxpy/qlib's own import chain. There is no clean pin;
  the real fix is a one-line patch to our fork (tracked in the reference doc) or replacing the affected
  operators with Polars/pandas equivalents in our own code.
- **The free sample dataset is stale:** its calendar stops at 2020-11-10 — any backtest window after
  that raises `IndexError` (not a bug, just old public sample data).
- **Backtest engine confirmed working and fast, once a test-harness bug was fixed.** A minimal
  `TopkDropoutStrategy` backtest (10 tickers, 108 trading days, `SimulatorExecutor`, $1M account,
  realistic commissions) initially appeared to hang for 15+ minutes with almost no CPU consumed. Root
  cause: Qlib uses `multiprocessing` internally, and our test script lacked Python's required
  `if __name__ == "__main__":` guard — on macOS's spawn-based multiprocessing, that causes every worker
  to re-import and re-execute the whole script, spawning more workers in an unbounded loop of
  `RuntimeError`s (visible in the process's own error output). This was **our test harness's bug, not
  Qlib's.** Fixed, the same backtest completed in **~7 seconds** (108 steps at ~925 it/s), producing a
  real equity curve: $1,000,000 → $1,103,140 (+10.31%) over the window against a random signal, vs.
  AAPL's own +35.54% (a random signal losing to a single outperforming stock is the expected result —
  this run was only proving the mechanics, not evaluating a real strategy).

**Net effect on the plan:** Qlib's backtest/account/exchange primitives and portfolio optimizer are
**confirmed working and performant** — a solid foundation for Agents 2, 9, 11. The expression engine
(central to Agent 7 in the original plan) still needs a fallback — most likely Polars or hand-rolled
pandas for factor computation, feeding pre-computed signals into Qlib's backtest layer rather than
relying on Qlib's own `Ref`/`Mean`/`Std` expression DSL. Any future script that touches Qlib and uses
multiprocessing (directly or via Qlib internals) must guard its entry point with
`if __name__ == "__main__":` — this generalizes beyond this one spike.

---

## Agent Roster → Build Strategy

| # | Agent | Call | Basis |
|---|-------|------|-------|
| 1 | Lead Orchestrator (CIO) | **Adapt** | Fork `TradingAgentsGraph` + `GraphSetup`; its LangGraph `StateGraph` wiring, typed `AgentState`, and SqliteSaver checkpoint/resume are directly reusable |
| 2 | Portfolio Manager & Allocation | **Extend Qlib** | `PortfolioOptimizer` (gmv/mvo/rp/inv) + `riskmodel/` covariance estimators + `cvxpy` already present; add Black-Litterman, HRP, Kelly |
| 3 | Academic & Open-Source Research | **Build custom** | arXiv + PyGithub ingestion pipeline (drafted in prior session, ready to drop in). Absent from both repos |
| 4 | Advanced Probability & Statistics | **Build custom** | Cointegration (Engle-Granger/Johansen), ADF/KPSS, HMM regime detection, Deflated Sharpe Ratio. Verified absent from both repos |
| 5 | Quantum & Optimization | **Build custom** (defer) | QUBO/QAOA via Qiskit/Pennylane. Lowest priority — see "Scope warning" below |
| 6 | Fundamental & Macro Intelligence | **Adapt heavily** | Near-direct port of TradingAgents' `fundamentals_analyst`, `news_analyst`, `sentiment_analyst`, `social_media_analyst` + its wired FRED / Alpha Vantage / Reddit / StockTwits / Polymarket tooling |
| 7 | Alpha Mining (Signal Generator) | **Build custom** on Qlib's model infra | TradingAgents' bull/bear researchers debate in prose, not standardized signals. Need `[-1,+1]` numeric output; Qlib's `qlib/model` + LightGBM give the training infra |
| 8 | Quantitative Software Engineering | **Build custom** | Code-gen agent (paper/pseudocode → tested Python). Absent from both |
| 9 | Backtesting & Strategy Validation | **Adapt Qlib** (sole source) | `qlib/backtest/` is the only real backtest engine available — TradingAgents has none. Extend with Monte Carlo, walk-forward, look-ahead/survivorship checks |
| 10 | Chief Risk Officer (CRO) | **Build custom, isolated** | Must be deterministic code with kill-switch authority, running **outside** any LLM path. TradingAgents' aggressive/conservative/neutral debators are advisory LLM opinion — they must never substitute for hard VaR/drawdown enforcement |
| 11 | Execution & Microstructure | **Adapt Qlib** | `exchange.py` / `executor.py` give order-simulation primitives; Qlib also has `examples/rl_order_execution` and `examples/orderbook_data`. Extend toward live APIs later |
| 12 | Operations & Settlement | **Extend Qlib** | `qlib/workflow/recorder.py` (MLflow-backed) is a head start for audit logging, PnL history, and experiment tracking |
| 13 | Compliance & Regulatory Surveillance | **Build custom** | Absent from both repos. Wash-trading/spoofing pattern detection, position-limit checks, restricted-list screening, and a regulatory-defensible audit trail. Structurally distinct from the CRO (Agent 10): CRO watches capital-at-risk, this watches conduct |
| 14 | Model Risk & Independent Validation | **Build custom, independent of Agent 9** | Absent from both repos. A real institution keeps this separate from the team that built the model, on purpose — the question isn't "does the backtest look good" (Agent 9's job) but "could this model be systematically wrong in ways backtesting can't reveal": regime-shift blindness, decay over time, out-of-distribution inputs |
| 15 | Data Infrastructure & Reliability | **Build custom** | Absent from both repos. Watches every upstream feed (FRED, yfinance, arXiv, GitHub, and Qlib's own data store) for staleness, schema drift, and outages. Motivated by this project's own history, not speculation — see "Why Agent 15 exists" below |
| 16 | Treasury & Funding | **Build custom** (defer) | Absent from both repos. Margin, collateral, funding costs, and currency hedging of firm capital — distinct from the Portfolio Manager, which allocates strategy capital, not manages the cash/broker relationship. Lower priority for a single-operator system without multiple prime broker relationships; named so it isn't silently forgotten |

**Net:** 4 adapt, 3 extend, 9 build custom (2 explicitly deferred: Agent 5,
Agent 16). Roughly half the system has a real foundation already —
considerably better than starting cold.

### Why Agent 15 (Data Infrastructure & Reliability) exists

This isn't a speculative role — it's a direct response to this project's own
track record. Every one of these was found only because a human-triggered live
test happened to catch it, not because anything was watching for it:

- PyGithub's `PaginatedList` throwing `IndexError` on a short result set (Agent 3).
- FRED's `CPIAUCSL` silently missing an observation, corrupting a YoY calc (Agent 6).
- Qlib's public sample dataset calendar being stale since 2020-11-10.
- Qlib's expression engine (`Ref`/`Mean`/`Std`) silently returning empty data
  under the current numpy/pandas stack.

A dedicated agent whose only job is "watch every upstream data source for
drift, gaps, and staleness, and say so before it corrupts a downstream
calculation" would have flagged several of these automatically. Not yet built —
named here so the gap is explicit rather than rediscovered a fifth time.

---

## Repository Layout

```
quant trading/
├── reference/              # cloned upstreams: study + extension base (gitignored, own history)
│   ├── TradingAgents/      # Apache-2.0 — orchestration graph + LLM analysts
│   └── qlib/               # MIT — data / backtest / execution / optimization
├── backend/
│   ├── core/               # event_bus.py, state_graph.py (our fork of TradingAgents' graph), config.py
│   ├── api/                # FastAPI app: main.py, routes/, websockets/
│   ├── models/             # Pydantic v2 schemas — inter-agent events + API DTOs
│   ├── services/           # business logic + Qlib integration wrappers (data, backtest, optimizer)
│   ├── agents/             # one folder per custom agent (3, 4, 5, 7, 8, 12 + extensions to 2, 6, 9, 11)
│   └── risk/               # isolated CRO — must NOT import backend/core or LangGraph
├── frontend/               # Next.js dashboard (Phase 1+)
├── docker-compose.yml      # Postgres + Redis + FastAPI, once containerization starts (Phase 1+)
├── CLAUDE.md               # always-on rules for AI coding agents (see: rules-create-global)
├── .claude/references/     # on-demand detail (e.g. qlib-known-issues.md)
└── README.md               # this file — architecture rationale & roadmap
```

This layout (`core/` · `api/` · `models/` · `services/` split) was refined from three independent
AI-generated blueprints the user collected (DeepSeek, Qwen, and a Gemini master-prompt doc) — all
restated the same 12-agent design with no new verified facts, but this particular split of concerns
was cleaner than the original flat `backend/agents + graph + risk` layout and is worth keeping.

---

## Roadmap

### Phase 0 — Integration spike (start here, before any agent code)
The single highest-value thing to do first, because it de-risks everything after it:

1. Run `reference/TradingAgents` end-to-end on one ticker with a real LLM key.
   Confirm the graph/state/tool pattern and measure **token cost per decision** —
   this sets the economics of the whole design.
2. Run a `reference/qlib` example backtest. **Expect friction here:** Qlib needs
   an explicit data download + `qlib.init()` step, is marked
   `Development Status :: 3 - Alpha`, and builds cython extensions — verify it
   compiles on this machine's Python before committing to it as the backtest
   engine.
3. Decide fork vs. dependency. **Recommendation: fork both.** We need a 12-node
   graph and an isolated CRO layer — those are architectural changes, not tools
   bolted onto the existing graph.

### Phase 1 — Core foundations
- **Agent 3 (Academic Research — arXiv + GitHub) is built and verified live**
  as of 2026-08-18: `backend/agents/research/`. Run with
  `cd backend && python -m agents.research`. Verified against real arXiv/GitHub
  APIs (found 3 real recent papers on LOB simulation/diffusion models; correctly
  pulled a linked GitHub repo straight out of an abstract). Two real bugs found
  and fixed during verification, documented in the code: PyGithub's
  `PaginatedList` raises `IndexError` when sliced past its actual result count
  (worked around with `itertools.islice`), and naive `$...$` regex extraction
  picks up bare numbers as false "math concepts" (filtered out).
- Extend the forked graph with nodes for Agents 2–12 (most as stubs initially),
  rather than building a LangGraph pipeline from scratch.
- Stand up the isolated CRO (`backend/risk/`) as its own process with a
  deterministic loop and kill-switch **from day one**, not retrofitted later.

### Phase 2 — Statistics, alpha, engineering
- **Agent 4 (Probability & Statistics) is built and verified live** as of
  2026-08-18: `backend/agents/stats/`. Run with `cd backend && python -m agents.stats`.
  Covers stationarity (ADF + KPSS), cointegration (Engle-Granger + Johansen),
  and the Deflated Sharpe Ratio (Bailey & López de Prado 2014) — the last of
  these directly feeds Agent 9's overfitting checks. Verified against real
  yfinance data (KO/PEP/XOM): price levels correctly test non-stationary,
  log returns correctly test stationary, ADF and KPSS agree on both, and
  Engle-Granger and Johansen independently agree on cointegration rank. A
  built-in sanity check confirms the DSR correctly decreases as the assumed
  number of trials increases (more multiple-testing should make the same
  result *less* convincing — this held on the first run). **Deliberately
  deferred, not built:** regime-switching (HMM/Markov-switching), extreme
  value theory, copulas, and Bayesian return modeling — all present in the
  original 12-agent spec, cut for MVP scope. Add them as separate, focused
  follow-ups rather than folding them in unverified.
- **Agent 7 (Alpha Mining) is built and verified live** as of 2026-08-18:
  `backend/agents/alpha/`. Run with `cd backend && python -m agents.alpha`.
  **This is the first agent that consumes another agent's output** — it pulls
  the live macro regime from Agent 6 and uses it to weight factors.
  - **Deviated from the original plan, for a verified reason.** The roster said
    "on Qlib's model infra"; factors are computed in **plain pandas** instead,
    because Phase 0 proved Qlib's expression engine (`Ref`/`Mean`/`Std`)
    silently returns empty data. Qlib is still the backtest engine (Agent 9) —
    that part is verified working.
  - Factors: 12-1 momentum (with the standard 1-month skip so short-term
    reversal doesn't contaminate it), 5-day reversal, low-volatility, volume
    trend. Normalized **cross-sectionally by rank** rather than z-score, so a
    single outlier can't distort the whole cross-section.
  - Regime weights are **hand-set priors, not fitted** — momentum-heavy in
    expansions, low-vol-heavy in contractions, with gross exposure scaled down
    in risk-off. Deliberately not optimized, so a backtest can't quietly tune
    them into overfitting. Agent 9 is where they get validated.
  - **Four correctness checks, all passing:** bounds (`[-1,+1]`/`[0,1]`);
    **factor-direction** (recomputes realized vol and 5-day returns
    independently and asserts each factor ranks them the intended way — a
    flipped sign here would produce confident backwards signals silently);
    **look-ahead bias** (corrupts every post-`as_of` bar with a 100x spike and
    asserts all 15 signals stay byte-identical — 119 future bars corrupted, zero
    drift); and **regime-sensitivity** (confirms switching regime actually moves
    and reorders signals, so the regime input isn't decorative).
  - Known characteristic, not a bug: combined signals compress toward zero
    (max ≈ ±0.37 on a 15-name universe) because averaging four partly
    uncorrelated rank factors is mean-reverting by construction, then scaled by
    risk exposure. Re-normalizing the composite would restore full range but
    would also cancel the risk-off exposure scaling — so position sizing is
    left to the Portfolio Manager (Agent 2).
- Agent 8 (Quant Software Engineering / code-gen).

**Agent 6 (Fundamental & Macro Intelligence) is built and verified live** as of
2026-08-18: `backend/agents/macro/`. Run with `cd backend && python -m agents.macro`.
(Listed here out of phase order because it was built early — it had the largest
head start from the TradingAgents fork.)

- **Improved on the upstream design:** TradingAgents' FRED vendor requires a
  `FRED_API_KEY`. This uses FRED's public keyless CSV endpoint instead, so
  Agent 6 runs with **zero API keys**. The curated alias→series-ID map *is*
  adapted from TradingAgents (Apache-2.0, attributed in `fred_client.py`) —
  that mapping is real domain knowledge worth reusing.
- **Deterministic, not LLM-driven.** The growth × inflation quadrant
  classifier (Inflationary Expansion / Stagflation / Disinflationary Growth /
  Deflationary Contraction) is rule-based, so the same inputs always yield the
  same regime and every call ships its own reasoning trace. Downstream agents
  need a stable regime flag; LLM non-determinism would be a liability here.
  Inflation direction is measured as *acceleration of the YoY rate*, not the
  sign of inflation itself (CPI YoY is nearly always positive, so the naive
  reading would be useless).
- **Found and fixed a genuine correctness bug during verification:** a
  positional `shift(12)` was being used for year-over-year change. CPIAUCSL is
  missing its `2025-10-01` observation, so that walked back 12 *rows* to
  2025-06-01 and reported a **13-month** change as "YoY" — 3.54% instead of the
  true 3.30%. Now date-offset based (`asof`), with a regression check in the
  runner. This is now a project-wide ground rule in `CLAUDE.md`, since it
  applies to every time series here, not just CPI.
- Also fixed a misleading output: rate series (unemployment, VIX, 10y-2y) now
  report percentage-**point** change alongside percent change — unemployment
  moving 4.3%→4.1% is `-0.20pp`, which reads very differently from `-4.65%`.
- **NOT built (explicit seam, not a stub):** NLP/financial-BERT sentiment
  scoring and news/SEC-filing ingestion from the original spec. Both need
  either an LLM API key or a local transformer download, so neither could be
  verified — and a fake sentiment score is worse than a missing one.

### Phase 3 — Validation & risk

**Agent 9 (Backtesting & Strategy Validation) is built and verified live** as
of 2026-08-18: `backend/agents/backtest/`. Run with `cd backend && python -m agents.backtest`.
**This is the first fully composed pipeline** — Agent 6 (regime) → Agent 7
(signal) → Qlib's backtest engine → Agent 4 (Deflated Sharpe Ratio), with every
rebalance using only data available as of that date.

- **A real gap had to be fixed first.** Agent 6 always fetched "as of now" —
  fine for live use, but a walk-forward backtest asks "what was the regime on
  this past date," and using today's regime to trade a historical date would
  be look-ahead bias baked into the tool itself. `MacroRegimeClassifier.assess()`
  now takes an `as_of` parameter (plus an optional pre-fetched `series_cache`
  so a 35-rebalance backtest doesn't make ~250 redundant live FRED calls) —
  verified against real historical dates: 2018-06 correctly reads
  inflationary expansion, 2019-06 disinflationary growth, 2020-06 deflationary
  contraction with the growth score pinned at its -1.0 floor during the COVID
  crash. That last one in particular is a strong real-world sanity check, not
  a designed-for-the-demo result.
- **Runs on a 2018-2020 window, not "through today" — for a specific, verified
  reason, not a shortcut.** Qlib's execution engine needs its own bundled
  price data (mixing in fresh yfinance prices for the same tickers via
  `Exchange(extra_quote=...)` risks duplicate-index conflicts in its internal
  quote store — investigated, not assumed). That dataset's calendar stops at
  2020-11-10. All 15 universe tickers were verified to have complete,
  gap-free coverage in it from 2017-01-03 onward, so the window was chosen
  to end there — and it happens to span the COVID crash, a genuinely useful
  stress period rather than a limitation to apologize for. Agent 6/7's
  signal generation uses real historical yfinance data for the same window;
  Qlib's own bundled data (also Yahoo-sourced) handles execution pricing —
  two real data sources for the same real market, not a mock standing in
  for one.
- **Composition-level look-ahead test, not just per-agent.** Agent 6 and 7
  were already individually verified point-in-time-safe, but the new glue
  code here (rebalance-date selection, forward-filling a signal between
  rebalances) could reintroduce the bug on its own. Corrupting all data after
  the backtest's midpoint left all 18 earlier rebalances' long/short lists
  byte-identical — verified, not assumed from the sub-agents' own tests.
- **The honest result:** over 2018-01-02 to 2020-10-30, the strategy returned
  **+27.54%** against a naive equal-weight buy-and-hold benchmark's **+50.98%**
  — it underperformed. Annualized Sharpe 0.495, max drawdown -36.68% (the
  COVID crash). Feeding the daily returns through Agent 4's Deflated Sharpe
  Ratio (assuming 4 trials, for Agent 7's 4 hand-set factors) gives **0.414 —
  not statistically significant.** This is the system working correctly, not
  failing: Agent 9's job is to give a trustworthy skeptical answer, not a
  flattering one, and a hand-set factor design underperforming a naive
  benchmark on its first real test is a normal, expected outcome, not a bug
  to chase. The regime classifier and signal engine are validated; the
  specific factor weights are not (yet) shown to add value.
- Deliberately deferred, not built: Monte Carlo simulation and parameter
  sensitivity sweeps (both named in the original spec). The walk-forward
  mechanics and the overfitting check (DSR) were the higher-priority half to
  get right first.

**Agent 10 (Chief Risk Officer) is built and verified live** as of 2026-08-18: `backend/risk/`. Run with
`cd backend && python -m risk`. Historical + parametric VaR/CVaR, drawdown tracking, and a hard kill-switch
on drawdown/daily-loss limits.

- **Isolation is enforced by a test, not a convention.** An AST-based scan (not a text grep, so a forbidden
  import can't hide behind a comment) confirms nothing under `backend/risk/` imports `backend.core` or
  LangGraph — the module's actual source (`metrics.py`, `monitor.py`) has zero dependency on either; only
  the verification runner separately reuses Agent 9's backtest as a real-data test fixture.
- **Cross-agent consistency, not just internal self-consistency:** `backend/risk/metrics.py`'s
  `max_drawdown()` is an independent implementation from Agent 9's own drawdown calculation in
  `walkforward.py`. Run against the same real 2018-2020 backtest, both agree exactly: -36.68%. (This
  required a small refactor: `WalkForwardBacktester.run()` previously returned only summary stats, not the
  daily-returns series other agents need — it now returns both, so Agent 14's Model Risk won't have to
  duplicate the same Qlib wiring to get the same series a third time.)
- **The fat-tail relationship was verified, not assumed.** Agent 4 had already measured KO's daily-return
  kurtosis at ~5.1 against the normal distribution's 3.0. The real portfolio-strategy return series here
  has kurtosis 11.36 — even fatter — and historical VaR (0.0272) correctly exceeds parametric/Gaussian VaR
  (0.0266) on the same data, confirming a Gaussian risk model understates real tail risk here, not just in
  theory.
- **The kill-switch illustration produced a genuine, unplanned validation:** scanning the real COVID-crash
  backtest at a 25% max-drawdown limit shows the kill switch would have triggered on **2020-02-27** — the
  actual historical date that crash began, not a number tuned to look right. At a 15% limit it triggers
  far earlier, 2018-11-19, during that year's real Q4 selloff.
- **The actual risk limits (`max_drawdown_pct`, `max_daily_loss_pct`) are deliberately left unset** in
  `backend/risk/__main__.py`, pending the user's own risk-appetite decision — informed by the illustration
  above, not invented as a default. This is a values decision, not a technical one.
- Deliberately deferred, not built: Kupiec-style VaR-model backtesting (counting VaR exceptions against the
  confidence level's implied rate) — a real refinement, but the hard drawdown/daily-loss limits were the
  higher-priority piece to get right first.

- Dashboard: equity curves, drawdown, Monte Carlo distributions, risk gauges.

### Phase 4 — Portfolio, execution, operations
- Extend Qlib's `PortfolioOptimizer` with Black-Litterman / HRP / Kelly.
- Extend Qlib's exchange/executor toward live broker APIs.
- Agent 12 (Operations) on Qlib's experiment tracking.

---

## Scope warning (worth deciding early)

Two parts of the 12-agent design are speculative relative to the rest and are
candidates to cut or defer:

- **Agent 5 (Quantum & Optimization).** QAOA/QUBO on today's simulators does
  not beat classical solvers for portfolio problems of realistic size, and
  `cvxpy` (already a Qlib dependency) will handle the actual optimization
  better. Keep it as a research curiosity, not a critical path item.
- **Per-decision LLM cost.** A 12-agent graph with multi-round debate makes
  many LLM calls per trading decision. Phase 0 step 1 exists specifically to
  measure this before the architecture is locked in. If cost is high, the fix
  is to make the numeric agents (4, 7, 9, 10, 11) pure deterministic code and
  reserve LLM calls for genuine judgment tasks (3, 6, 8).

---

## Rejected sources
- The [prop trading firm gist](https://gist.github.com/chrisaycock/8b7a37b1f97549517cb7789be5b06266)
  is a directory of ~200 firm names and websites — no code, no architecture.
  Useful only as a "who to benchmark against" list.
- The [GitHub `prop-firm` topic](https://github.com/topics/prop-firm) is mostly
  challenge-passing Expert Advisors and drawdown calculators for funded-account
  programs (FTMO/TopStep-style). Different problem domain; not relevant here.

---

## Rules for AI IDEs & coding agents
1. **Strict type safety.** Pydantic v2 for all Python contracts; strict
   TypeScript interfaces in the frontend.
2. **Modular agents.** One folder per agent under `backend/agents/<name>/`.
   Never combine two agents' logic in one file.
3. **Async first.** All network/API/DB/Redis operations use `async`/`await`.
4. **CRO isolation is non-negotiable.** `backend/risk/` must never import from
   `backend/graph/` or any LangGraph module. It reads state; it does not join
   the debate. An LLM must never be able to talk the risk limit out of firing.
5. **No placeholder data.** Dashboard mocks use structurally realistic values
   (real-shaped OHLCV, plausible non-zero Sharpe) when live data is off.
6. **Respect upstream licenses.** Retain Apache-2.0 (TradingAgents) and MIT
   (Qlib) notices in any forked or vendored code.

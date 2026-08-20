# QAPF — Quantitative Autonomous Prop Firm: summary for external review

## What this is
A local-first, single-operator autonomous quant trading system. A 16-agent "AI workforce" (research,
statistics, macro regime classification, alpha signal generation, portfolio construction, backtesting,
risk enforcement, execution simulation, compliance, model-risk challenge, data-infrastructure monitoring,
orchestration, code generation, quantum-optimization research, treasury) built on top of two forked
open-source projects: TradingAgents (LangGraph orchestration + LLM agent scaffolding, Apache-2.0) and
Qlib (Microsoft's quant data/backtest/optimization engine, MIT). All 16 agents are built and individually
verified against real data (yfinance, FRED, Qlib's bundled US equities dataset) — no synthetic/placeholder
data anywhere in the system by explicit project rule.

## Architecture
- **Agent 1 (Lead Orchestrator)**: LangGraph pipeline — macro → alpha → portfolio → risk_gate →
  [execution → compliance] → CIO synthesis. Only ONE node makes an LLM call (the final CIO memo,
  Anthropic); every other node wraps a deterministic, independently-verified agent. Kill-switch
  enforcement lives here: a risk breach routes straight to the memo, skipping execution entirely (zero
  orders constructed, not just zero sent).
- **Agent 2 (Portfolio Manager)**: Ledoit-Wolf shrinkage covariance + Qlib's optimizer, regime-conditional
  method choice. Long-only by deliberate decision (no margin/borrow modeled yet).
- **Agent 6 (Macro)**: keyless FRED ingestion, deterministic growth×inflation regime classification.
- **Agent 7 (Alpha)**: 4 cross-sectional factors (12-1 momentum, 5-day reversal, low-volatility, volume
  trend), rank-normalized to [-1,+1]. low_volatility now uses a real Yang-Zhang range-based estimator
  (added this session) when OHLC data is available, falling back to close-to-close std otherwise.
- **Agent 9 (Backtest)**: walk-forward validation on Qlib's real backtest engine, monthly rebalancing,
  point-in-time signal discipline (verified via an explicit look-ahead-bias test that corrupts future
  data and asserts the signal doesn't change).
- **Agent 10 (CRO/Risk)**: VaR/CVaR, drawdown-based kill switch. Architecturally isolated — enforced by
  an import-boundary test, not just convention — from the LangGraph orchestration layer; it reads state
  and rules on it, nothing can argue it out of a halt.
- **Agent 4 (Stats)**: Deflated Sharpe Ratio (Bailey & López de Prado) used as the primary overfitting
  guard on every strategy validation attempt.
- Agents 3, 5, 8, 11-16 round out research ingestion, execution-cost modeling, compliance surveillance,
  model-risk challenge (independent of the team that built the backtest), data-health monitoring,
  code-generation (self-verified against real tests, never self-graded), quantum-optimization research,
  and treasury/cash-yield calculators.

## Governance discipline (the actual selling point, arguably more than the strategy)
- Every non-trivial numeric claim in this project has been independently re-verified at least once —
  e.g. Agent 10's risk metrics are cross-checked against Agent 9's real backtest; Agent 5's quantum
  optimizer is checked against both brute-force enumeration and an exact classical eigensolver every run.
- A structured "wayfinder" process tracks open questions as tickets with an explicit decision log, a
  5-attempt budget for the core "does this strategy actually work" question (to keep the trial count
  honest for Deflated Sharpe purposes), and a running map of what's settled vs. still open.
- This project has been burned twice by trusting unverified claims (a Qlib expression-engine bug, a stale
  bundled dataset) and has an explicit standing rule: verify against real source/execution before
  building on any claim, including claims from other AI-generated planning docs.

## Current real finding: the strategy has not yet cleared its own validation bar
Ticket 02 set the bar: Deflated Sharpe Ratio > 0.95, beat an equal-weight buy-and-hold benchmark on BOTH
annualized Sharpe and return-per-unit-max-drawdown, and be profitable net of real IBKR-Lite execution
costs at a genuine $1,000 account size. Five attempts were budgeted (n_trials incremented honestly each
time, since every free parameter is itself a trial for DSR purposes). Trajectory on a 2008-2017,
14-name US large-cap universe:

| Attempt | Change | DSR | Sharpe (strat vs bench) | Return/maxDD (strat vs bench) | Verdict |
|---|---|---|---|---|---|
| 1 | flat regime weights, real $0-commission cost model | 0.9636 (pass) | 0.564 vs 0.849 (fail) | 1.536 vs 2.175 (fail) | FAIL |
| 2 | + volatility-managed exposure scaling (Moreira & Muir 2017) | 0.9615 (pass) | 0.726 vs 0.849 (fail) | 2.741 vs 2.175 (**pass**) | FAIL |
| 3 | + Yang-Zhang range volatility estimator | 0.9301 (**fail**) | 0.738 vs 0.849 (fail) | 4.182 vs 2.175 (pass) | FAIL |
| 4 | pure low-volatility tilt (naive risk parity) instead of the 4-factor blend | 0.8870 (fail) | 0.718 vs 0.849 (fail) | 4.060 vs 2.175 (pass) | FAIL |
| 5 | (in progress) absolute momentum with a 200-day market-trend cash overlay | — | — | — | — |

The pattern: drawdown control keeps improving materially (max drawdown went from -36.7% to -17.6%
across attempts 1-4), but raw Sharpe has plateaued around 0.72-0.74 across three different
volatility-related refinements, while the Deflated Sharpe Ratio's honest trial-count penalty has grown
faster than that plateaued Sharpe can compensate for. Attempt 5 (final) deliberately switches to a
structurally different mechanism — absolute momentum with a cash leg — rather than a fourth variation
on risk-scaling, specifically because the trial-count math has made further refinement in that direction
counterproductive.

## What I'd like an honest outside opinion on
1. Is the overall architecture (16 specialized agents, deterministic-by-default with LLM judgment
   reserved for narrow synthesis tasks, isolated risk enforcement) a sound design for a real-money
   system, or over-engineered for what is currently a $1,000 account?
2. Given the attempt trajectory above, is there a smarter diagnosis of why Sharpe has plateaued around
   0.72-0.74 that the project might be missing — a structural reason a 14-name long-only US large-cap
   book on daily bars can't realistically clear a >0.85 benchmark Sharpe, versus a fixable modeling gap?
3. Any glaring risks, blind spots, or over-claimed rigor you'd flag from this summary alone?

Be skeptical. This project's own standing rule is to treat any external AI's take as a hypothesis to
verify against real code/data, not as an answer to adopt — so a critical, even harsh, response is more
useful than a diplomatic one.

## Every external resource sent to this project, start to finish (for context on what's already been considered)

**Early architecture docs (pre-formal-process):** DeepSeek and Qwen AI-generated architecture blueprints,
and an "AI Agents for Prop Trading" doc — all restated a similar agent-based design with no new
verification; one structural detail was merged into the README, the rest were treated as unverified
hypotheses (this project was already corrected twice by trusting AI-generated docs over real source).

**Quant methodology books/papers sent:** Kakushadze & Serur "151 Estrategias de Trading" (arXiv
1912.04492) — full text read, drove the actual factor-family feasibility analysis below; Jansen
*Machine Learning for Algorithmic Trading*; Carver *Systematic Trading*; Kaufman *Trading Systems and
Methods*; López de Prado *Advances in Financial Machine Learning* (its CUSUM filter technique was
extracted and actually landed in production code); Vince *The Leverage Space Trading Model* and *The
Mathematics of Money Management*; Bernut *Algorithmic Short Selling with Python*; a differential-geometry
statistics PDF; an HFT eBook.

**Papers/courses/tools sent as links:** quantpad.ai (rejected, closed SaaS); TabPFN (rejected as a return
predictor — license and evidence gaps; narrow allowed use for regime classification only); a GMM
regime-switching paper (Lindemann, Dunis & Lisboa 2005); an ML course; ConvTimeNet (arXiv 2403.01493);
ml-quant.com archive; OpenBB-finance/OpenBB (rejected, AGPL-3.0 license conflict; but led to discovering
Qlib's own free point-in-time constituents builder); cantaro86/Financial-Models-Numerical-Methods;
several YouTube videos (cannot be watched, only acted on if the operator summarizes them);
paperswithbacktest/awesome-systematic-trading (a curated list, verified real but stale);
HKUDS/Vibe-Trading (verified real, 31k stars — has systematic look-ahead testing QAPF lacked, but also
lacks any deflated-Sharpe/overfitting-correction machinery QAPF has).

**Platform/infra candidates sent:** Fincept Terminal (rejected, AGPL-3.0); QuantConnect/LEAN (Apache-2.0,
legitimate, not adopted — would mean rebuilding on top of a second backtest engine with no demonstrated
need); nautilus_trader (LGPL-3.0, confirmed real Interactive Brokers integration — the most seriously
considered alternative, flagged for the broker-integration ticket); Supabase, Coolify, LocalAI (all
genuinely relevant to not-yet-built infrastructure, not actionable yet); CrewAI and AutoGen (both
rejected — this project deliberately forked one orchestration framework rather than run two);
Documenso/Cal.com/PostHog/Penpot/NocoDB/Excalidraw/n8n/Immich/Browser Use/Firecrawl/Mem0/Langflow/
Crawl4AI/RAGFlow/AnythingLLM (general tool lists, triaged by category relevance, none solve an open gap).

**Found later, not sent by the operator:** fja05680/sp500 (a better long-term point-in-time data source
than what got built); stocklake.dev (an MCP connector — verified by direct API call to have only 365
days of daily history and no delisted-security data, solves none of the two remaining open data
problems, and its differentiated features are unverifiable AI-generated trading signals, philosophically
opposed to this project's deterministic-by-default design); BoomBloom/pwb-alphaevolve (a real,
functional LLM-evolutionary strategy-discovery tool — not adopted: requires a specific paid LLM this
project's cost model avoids, uses a different backtest engine, and has no visible overfitting-correction
despite running exactly the kind of many-trials search that inflates a Deflated Sharpe Ratio); its data
source paperswithbacktest.com (verified by downloading and querying the actual dataset — its
"survivorship-adjusted" marketing claim doesn't hold up: three real 2008-era delisted names are absent
entirely, and a fourth ticker in the dataset turned out to be a different company that later reused the
same symbol, not the original delisted one).

## Broader ask

Beyond the three specific questions above: what's your overall opinion of this project? What would you
change or add if you were advising on it? Be specific and be willing to disagree with choices already
made — this project treats outside AI opinions as hypotheses to check, not verdicts to adopt, so a
critical response is more useful than an agreeable one.

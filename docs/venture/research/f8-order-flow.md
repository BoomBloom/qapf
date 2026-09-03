# F8 — Order flow and market microstructure
Researched: 2026-09-03 | Researcher: subagent

## Environment note (read before trusting any tag below)
This session's egress proxy blocks CONNECT to essentially every primary-source domain —
confirmed for arxiv.org, ssrn.com, semanticscholar.org, researchgate.net, sec.gov, finra.org,
nasdaq.com, and the major exchange/broker APIs — with 403 policy denials, not network errors.
Only WebSearch (result-summary access) worked. Per the standing instruction, no attempt was
made to route around this. **Every claim below is therefore `[reported]` at best** — a
search-engine summary of a primary or secondary source, never a document I read directly. A
few numbers (HFT industry revenue collapse, IBKR/IBKR-adjacent margin figures, Databento's
published list price) come from sources specific and stable enough to treat as reasonably
solid `[reported]` claims, but none carry `[verified]`. Anything used to size a real position
or commit real capital must be re-checked from a machine with open network access before
that decision is made — this is consistent with §0 of the shared research log.

## Bottom line — can a retail operator extract an order-flow edge? (direct answer required)

**Mostly no, with one narrow, capital-inappropriate exception.** The core academic finding on
order book imbalance — the most-studied order-flow signal — is that its predictive power is
concentrated in the next **1–2 order book events / next few seconds to tens of seconds**, and
decays toward zero beyond roughly a minute [reported, converging across multiple sources
below]. That horizon sits at or below the round-trip latency a retail operator on a home/VPS
internet connection actually gets (**10–100ms is achievable, but that's the *network* leg
only** — add strategy compute, exchange queueing, and the fact that by the time a retail
client sees a book update it is already stale relative to colocated participants who see it
in single-digit microseconds). The retail operator is not "a bit slower" than the competition
here; they are competing in a different physics regime — nanoseconds/microseconds (colocated
HFT, FPGA tick-to-trace ~100–500ns [reported]) vs. milliseconds (retail). At the horizon where
OBI is actually predictive, a retail operator's marginal edge has already been captured and
reversed by faster participants before the retail order can reach the matching engine. This
is the single strongest finding in this research and it should be taken at face value rather
than argued around.

The one place this verdict softens: **trade-sign / order-flow long-memory effects (the
Lillo-Mike-Farmer / Bouchaud persistence literature) operate on a slower, structural timescale**
— driven by large institutional metaorders being split and executed over minutes to hours,
not by microsecond queue dynamics. This is a genuinely different mechanism from raw OBI and
is not obviously latency-gated in the same way. It is also the least "retail-friendly" to
verify (it requires trade-classification and long historical trade tapes) and the underlying
edge (fading/following persistent institutional flow) is closer to what serious quant funds
already harvest as part of market-impact and execution-cost modeling than to a standalone
retail alpha source. **Verdict: worth a scoped kill test, not worth building a business plan
around at $1,000.**

**Everything downstream of "trade signals derived from OBI/CVD/footprint reasoning at
sub-minute retail latency" should be treated as dead** for this operator, not marginal. The
honest use of order-flow tooling at this capital level is **not as an alpha source but as an
execution-quality tool** — reading absorption/liquidity at the point of entry to reduce
slippage on trades whose actual edge comes from elsewhere (a macro/factor signal on the
platform this operator already has). That is consistent with what F2 (crypto microstructure)
already flagged in passing: microstructure facts are useful for execution timing, not as a
standalone alpha source (see `f2-crypto-microstructure.md` line ~257).

**If forced to name a horizon, venue, and cost where something is still live:** the
Lillo-Mike-Farmer trade-sign persistence effect, tested on CME Micro E-mini futures (ES/NQ
family) using free-to-cheap trade-tape data (not full MBO), at a multi-minute-to-hourly
horizon, is the only candidate that survives the latency argument. It should be treated as a
research curiosity to falsify cheaply, not a strategy to size capital into before falsification.

## The decay-horizon question (the crux)

Multiple independent strands of literature converge on the same shape: **order-flow-derived
short-horizon return predictability is real, statistically robust, and decays fast.**

- The foundational Cont–Kukanov–Stoikov (2014, *Journal of Financial Econometrics*) result:
  over short intervals, price changes are driven by order flow imbalance at the best bid/ask,
  with a **linear** relationship between OFI and price change, slope inversely proportional to
  market depth. This holds across NYSE TAQ data for 50 US stocks and is described as "stable
  across time scales and across stocks" [reported] — but stability of the *relationship* is
  not the same as a long *predictive* horizon; it describes contemporaneous/very-short-lag
  price formation, which is the mechanism, not a tradeable lead time.
- A 2022 arXiv paper directly on this question ("The Short-Term Predictability of Returns in
  Order Book Markets," arXiv:2211.13777) and related emergent-mind summaries converge on:
  **imbalance has strong predictive power over exactly the next 1–2 mid-price changes, then
  decays to near zero.** Results are described as "robust out of sample for horizons measured
  in seconds and tens of seconds," with informal characterizations of "a few seconds to about
  a minute" as the usable window [reported].
- DeepLOB (Zhang, Zohren, Roberts 2018) shows deep-learning models can extract *some*
  generalizable structure from raw LOB data across previously-unseen stocks over a
  multi-month test window [reported] — but this is evidence the *signal exists and is
  learnable*, not evidence it survives retail execution latency; DeepLOB's own robustness
  checks show accuracy degrading meaningfully (double-digit percentage points) under input
  perturbation, i.e., it is fragile exactly where retail execution noise would live
  [reported].
- The trade-sign long-memory literature (Lillo–Mike–Farmer 2005; Bouchaud et al.) is the
  outlier: sign autocorrelation decays as a **power law** (Hurst exponents ~0.65–0.9 reported
  across LSE and Euronext studies), meaning persistence measured in **many trades / longer
  wall-clock windows**, attributed to institutional order-splitting (metaorders), not to
  queue-level microstructure. This is mechanistically distinct from OBI decay and is the one
  effect whose horizon is not obviously sub-second [reported].

**Retail latency reality, stated concretely:**
- Colocated HFT: single-digit-microsecond wire latency inside the datacenter; FPGA-based
  tick-to-trade of **100–500 nanoseconds** [reported]. CME's own Aurora, IL colocation costs
  **$12,000/month for a 10G handoff plus a $2,000 setup fee** [reported] — a real, checkable
  number, not the whole institutional cost stack (racks, cross-connects, hardware, licenses
  add materially more).
- Retail (home broadband or a generic cloud VPS, not a purpose-built trading VPS in the
  exchange's metro): **10–100ms round trip** is the commonly cited achievable range
  [reported]. Even a well-tuned "trading VPS" product marketed at retail targets ~1ms
  [reported] — three to four orders of magnitude slower than colocated HFT, and still slower
  than the multi-hundred-microsecond tier occupied by serious non-colocated proprietary shops.
- **Conclusion, stated plainly:** at the horizon where OBI/CVD-type signals are shown to have
  predictive power (next 1–2 book events, seconds to tens of seconds), a retail participant's
  order does not reach the matching engine before that information is stale relative to
  faster participants. This is not a "you'll do worse" edge case — it is a structural
  disqualification for pure short-horizon order-flow signals at retail infrastructure. The
  slower, metaorder-driven persistence effect is the only one not obviously disqualified by
  this argument, because its timescale (many trades, minutes-to-hours) does not require
  competing on wire speed — it requires correctly inferring *that a large order is being
  worked*, which is an inference problem, not a speed problem.

## Data costs — what it actually takes to research and trade this

| Source | Coverage | Historical cost | Live cost | Confidence |
|---|---|---|---|---|
| Databento (CME GLBX.MDP3, full MBO) | CME futures (ES/NQ/MES/MNQ etc.), full order-by-order book | Pay-as-you-go, metered by bytes delivered; no flat historical fee found | Standard live subscription plan reported at **$179/month** (12-month intro rate), renewing to **$199/month**; this is Databento's current CME Standard tier, not necessarily full-depth MBO at that price — plan tiers and included datasets need direct confirmation on Databento's own pricing page before budgeting | reported |
| Polygon.io | US equities, options, forex, crypto — quote/trade level; DOM/full order-book depth not confirmed in this research | N/A | "Stocks Advanced" flat-rate real-time reported around **$199/month**; no confirmed order-book-depth tier found | reported |
| IBKR API market data | Depth-of-market (Level 1 + Level 2 via `reqMktDepth`, `isSmartDepth`) is API-accessible to IBKR account holders | Bundled with account/market-data subscriptions, not separately priced in what I could find | Exchange-dependent market data fees (typically low single-digit to double-digit dollars/month per exchange for a retail/non-professional account), specific current schedule not verified | unverified — needs IBKR's own current market-data fee page, which is on the proxy's blocked list |
| dxFeed | Institutional-grade consolidated feed incl. depth data | Not found in this research pass | Not found in this research pass | unverified |
| Nasdaq TotalView-ITCH | Full-depth Nasdaq order book, direct-from-exchange | Enterprise/vendor licensing, materially expensive; one adjacent Nasdaq options depth-feed price point found: **$1,527/month (internal distributor) to $2,035/month (external distributor)**, effective Jan 2026 — this is a *different* Nasdaq depth product, not TotalView-ITCH itself, but indicates the order of magnitude for exchange-direct full-depth feeds | reported |
| Binance / Coinbase / OKX (crypto) | Full L2 depth, sub-100ms update streams | **Free**, via public WebSocket (`<symbol>@depth`, etc.) | **Free**, real-time streaming, subject to rate/connection limits | reported |
| Crypto historical L2/L3 flat files (e.g., Coinbase-style vendor archives referenced in search results) | Full historical order-book reconstruction data | Some vendors offer downloadable daily archives (.csv.gz, microsecond timestamps) at cost; exact current pricing not verified in this pass | N/A | unverified |

**The crypto-for-research point is real and should be used.** Free full-depth L2 (and in some
cases L3-reconstructable) data from Binance/Coinbase/OKX websockets means an operator can test
every OBI/CVD/VPIN/queue-position hypothesis in this document **at zero data cost**, using
crypto purely as a laboratory, before spending a cent on CME MBO data — consistent with the
charter's decision that crypto is shelved for trading but not for research. Given the venue
filter already excludes crypto for live trading (single-venue counterparty risk, no central
clearing), this is squarely a "build the kill test on crypto data, only pay for CME data if
the crypto kill test survives" workflow.

**Bottom line on cost:** testing this hypothesis family is cheap (free, on crypto data);
*trading* it live on CME with real depth data is a real recurring cost in the $150–250/month
range for the vendor feed alone (Databento CME Standard, unverified exact contents),
before accounting for exchange-direct market data fees, which is a material fraction of a
$1,000 account's annual return potential and should be treated as a go/no-go gate, not a
rounding error.

## Venue analysis: CME futures vs listed equities vs crypto (research-only)

- **CME futures (ES/NQ/MES/MNQ):** Passes the venue filter — centrally cleared, no
  counterparty-profits-from-your-loss structure, no pattern-day-trader rule (that's an
  equities/FINRA constraint, not a futures one) [reported — PDT is a well-known FINRA equities
  rule; its inapplicability to futures is standard industry knowledge, not independently
  re-verified this pass]. Micro E-minis (MES, MNQ) are the capital-appropriate instrument at
  $1,000: **intraday/day-trading margin commonly cited at roughly $50–$300 per contract**
  depending on broker (NinjaTrader/Tradovate/AMP-style day-trading discounts vs. IBKR's
  risk-based margining, which is generally less generous on intraday discounts), against a
  CME-set **overnight margin around $1,200** as of 2026 [reported, both figures]. This is the
  most-referenced retail order-flow venue by a wide margin — footprint-chart and
  delta-divergence communities are heavily concentrated in ES/NQ discussion.
- **Listed equities:** Passes the venue filter structurally (centrally cleared, lit
  exchanges), but PDT rules bind a $1,000 account hard (under $25k equity, at most 3 day
  trades per rolling 5 business days on margin accounts) — a genuine structural obstacle to
  testing any short-horizon signal with real frequency at this capital level, independent of
  whether the signal itself works.
- **Crypto (research-only, per charter):** Fails the venue filter for live trading (shelved
  by prior decision) but is the cheapest and richest environment to *falsify* every
  hypothesis in this document before spending real money or real data budget on CME. Crypto
  L2/L3 microstructure was explicitly excluded from this file's scope (covered by the F2
  researcher under venue/carry/arb) — this file's crypto usage is strictly "borrow the free
  data to kill hypotheses cheaply," not a trading recommendation.

**Net:** CME Micro E-minis are the correct live venue if any order-flow thesis survives
falsification; crypto is the correct *test bench*; equities are structurally disadvantaged for
this specific hypothesis family at this capital level, independent of the PDT question, because
their book depth and per-name volume are far more fragmented across venues (equities trade
across ~13+ lit venues plus dark pools) than a single centralized futures book, making
book-based signals harder to reconstruct correctly without a consolidated, paid feed.

## The education-industry problem — what has evidence, what is being sold

This is a blunt but load-bearing section. Searching directly for academic validation of the
retail order-flow canon — footprint charts, delta divergence, absorption reversals — returned
**zero peer-reviewed or backtested sources**, only vendor blogs, indicator marketplaces
(TradingView scripts, Sierra Chart add-ons, "OrderFlowLabs"-style product pages), and course
content. The search summary itself states this plainly: these are "practitioner-focused"
concepts with "no backtested performance data, academic peer-reviewed studies, [or] rigorous
evidence of predictive value" found [reported — search-summary characterization, but the
absence itself, across a targeted query, is the finding].

Separately, and consistent with what a prior researcher on this project found for FX (see
`f7-forex.md`), the retail trading-education and prop-firm-challenge industries have a
structural conflict of interest: **evaluation-fee-funded prop firms profit from traders
failing challenges**, independent of whether their taught methodology (frequently
footprint/order-flow-branded) works [reported]. The charter's own venue filter already
excludes prop-firm challenges on exactly this basis — the operator running this account is
not the natural customer for that content regardless of whether footprint reading has any
edge.

**What does have real, citable evidence behind it**, and should not be confused with the
above:
- Order flow imbalance and its short-horizon relationship to price changes (Cont-Kukanov-Stoikov
  and follow-on work) — genuinely published, peer-reviewed, replicated across markets.
- Trade-sign long memory (Lillo-Mike-Farmer, Bouchaud et al.) — genuinely published,
  peer-reviewed, and has a coherent causal mechanism (order splitting).
- VPIN — published (Easley/López de Prado/O'Hara, *Review of Financial Studies* 2012), but
  **actively disputed in the literature itself**: Andersen and Bondarenko report that once you
  control for contemporaneous volume and volatility, VPIN shows **no incremental predictive
  power** for future volatility, and separately dispute the trade-classification methodology
  (bulk-volume classification vs. transaction-based) underlying the original VPIN construction
  [reported]. This is a case where the "evidence" is a live, unresolved academic dispute, not
  settled science — treat any VPIN-based product or claim with the same skepticism the dispute
  itself implies.
- Iceberg/hidden-liquidity detection — a real, if narrow, academic literature exists
  (active/pinging, model-based, and frequentist detection approaches; at least one CME-specific
  arXiv paper and one *Journal of Financial Research* 2025 paper found) [reported]. This is
  closer to legitimate market-structure research than to the retail "absorption" narrative,
  though the retail narrative borrows its vocabulary.

**Verdict on the education-industry question:** the popular retail order-flow canon
(footprint/delta-divergence/absorption as taught by course vendors) is, on the evidence
gathered here, **almost entirely unvalidated folklore wearing the vocabulary of a real
academic field.** The underlying academic concepts (OFI, trade-sign persistence, VPIN,
iceberg detection) are real research areas with real papers — but the specific chart-pattern
trading rules sold to retail (divergence = reversal, absorption = highest-quality reversal
signal) have no discovered evidentiary backing independent of the people selling them. This
is close to F7's finding on retail FX education and should be read the same way.

## Tooling: what can actually backtest order flow

| Framework | L2/MBO support | Queue modelling | Verdict |
|---|---|---|---|
| **nautilus_trader** | Yes — explicit `L3_MBO` (per-order, keyed by order ID, full book reconstruction) and `L2_MBP` (aggregated by price level) types; native Databento integration | Yes — MBO data explicitly supports queue-position modeling; nanosecond-resolution, event-driven simulation with configurable fill/latency/order-book models; Rust core for performance | **Best-fit tool for this hypothesis family.** Purpose-built for exactly the granularity this research needs, open source, actively maintained, has a direct Databento integration matching the CME data source identified above. |
| **hftbacktest** (nkaz001) | Yes — explicit full order-book reconstruction from **both** L2 (market-by-price) and L3 (market-by-order) feeds | Yes — this is the framework's headline feature: backtests explicitly account for feed/order latency **and** order queue position for realistic fill simulation; Python (Numba JIT) + Rust | **Strong second candidate, arguably more purpose-built for the latency/queue question specifically** than nautilus_trader — worth evaluating alongside it, especially for a first kill test given its narrower, HFT-specific focus. |
| **QuantConnect / Lean** | Partial — no native turnkey L2/order-book type; users must define a custom `BaseData` subclass and hand-roll book reconstruction from tick data; official docs and forum threads confirm this is a DIY path, not a first-class feature | No — fill timing is tied to subscription resolution (e.g., minute bars only receive minute-sliced data); no built-in queue-position simulation found | **Cannot do this out of the box.** Usable only with substantial custom engineering, and even then lacks native queue modeling — a real limitation for anything claiming a queue-position or fill-probability edge. |
| **StockSharp** | Claims order-book/Level 2 support ("ticks, order books, candles" across 80+ sources), C#-based | Marketing copy claims "realistic testing," specifics on queue-position modeling not found in this research pass | **Unverified depth of support** — plausible for basic L2 backtesting, but no evidence found of MBO-level queue modeling comparable to nautilus_trader/hftbacktest. Treat as a maybe pending direct evaluation. |
| **Standard OHLCV backtesters (vectorbt, backtrader, Qlib's own backtest engine as currently used in this project)** | No | No | **Cannot backtest order-flow hypotheses at all**, full stop — this needs to be said plainly for this project specifically: QAPF's existing Qlib-based walk-forward harness (Agent 9, `backend/agents/backtest/`) operates on OHLCV/bar data and **cannot evaluate any thesis in this document** without a fundamentally different, order-book-aware backtesting engine bolted on alongside it. This is not a Qlib expression-engine bug (see `qlib-known-issues.md`) — it's a category mismatch between bar-based and event-based backtesting that no amount of Qlib configuration fixes. |

**Practical implication for this operator specifically:** if any thesis below survives its
kill test, it requires standing up a **second, separate backtesting stack** (nautilus_trader
or hftbacktest) — the existing Qlib/walk-forward/DSR harness this project has built cannot be
extended to cover order-flow hypotheses; it would need to be run alongside, not modified.

## Candidate theses

### T8.1 — Order book imbalance predicts the next 1–2 mid-price moves, but not further, and retail latency exceeds that horizon
- Evidence for: Cont-Kukanov-Stoikov (2014) linear OFI-to-price-change relationship, robust
  across 50 US stocks and multiple time scales [reported]; 2022 arXiv work confirming OBI
  predictive power concentrated in the next 1-2 order-book events, decaying to ~0 beyond
  seconds-to-tens-of-seconds [reported].
- Evidence against: retail round-trip latency (10-100ms typical, ~1ms best-case with a
  dedicated trading VPS) is not obviously "too slow" in absolute terms for a tens-of-seconds
  horizon — the real disqualifier is that colocated participants act on the *same* imbalance
  in microseconds and have already moved the price by the time a retail order lands, so the
  retail operator is trading a signal that is stale relative to faster capital, not merely
  slow in isolation. This is the single strongest counter-argument in this research and it
  wins.
- Horizon the edge lives at: seconds to tens of seconds (order-book-event scale), i.e.
  faster than retail infrastructure can reliably act on with an edge intact.
- Infrastructure and data cost required: full MBO/L2 feed with sub-millisecond internal
  processing and ideally colocated or near-colocated execution to have any chance; CME MBO via
  Databento (~$179-199/month, unverified exact tier) at minimum, likely insufficient without
  materially faster execution infrastructure than a retail operator has access to.
- Capital range where it works: not this operator's, at any capital level, without a
  fundamentally different infrastructure investment (colocation) that is economically
  irrational below a much larger account size.
- Kill test (runnable in under 1 day with free or cheap data): pull free Binance/Coinbase L2
  websocket depth for a liquid pair, compute OBI at each snapshot, regress forward returns at
  multiple horizons (100ms, 1s, 5s, 30s, 60s, 5min) against current OBI, and plot the decay
  curve of the OBI-return correlation as a function of horizon. If (as expected) predictive
  power collapses by ~30-60 seconds, that alone falsifies this thesis for retail use without
  spending a cent — the decay curve *is* the kill test.
- Verdict: **dead** for standalone alpha extraction at retail infrastructure. Not dead as a
  research confirmation exercise — worth running the decay-curve kill test once, cheaply, to
  have first-party confirmation rather than relying solely on literature review, and because
  the resulting decay curve is directly useful evidence for T8.3/T8.5 below.

### T8.2 — Trade-sign long memory / metaorder persistence is exploitable by following (or fading) large orders being worked over minutes-to-hours
- Evidence for: Lillo-Mike-Farmer (2005) and Bouchaud et al. establish power-law-decaying
  trade-sign autocorrelation (Hurst ~0.65-0.9 across LSE/Euronext studies), attributed to
  institutional order-splitting; this is a slower, structurally different mechanism from raw
  OBI, plausibly not gated by colocation-scale latency [reported].
- Evidence against: the persistence being real and detectable is not the same as it being
  *profitably tradeable net of costs* — the same order-splitting behavior that creates the
  persistence is also *why* markets have square-root price-impact laws, meaning anyone
  trying to trade in front of or alongside a detected metaorder faces the same impact costs
  that make the original order worth splitting in the first place. This is a genuinely harder
  thesis to falsify than T8.1 and deserves real skepticism rather than optimism just because
  the literature is more favorable.
- Horizon the edge lives at: minutes to hours (many-trades scale), not latency-gated in the
  same way as T8.1 — the binding constraint is correctly *identifying* persistent flow, not
  reacting to it in microseconds.
- Infrastructure and data cost required: a reasonably long, clean trade tape with reliable
  trade-sign classification (Lee-Ready or similar) — does not require full MBO depth, making
  it meaningfully cheaper than T8.1/T8.3; CME trade data or even free crypto trade tapes
  suffice for the initial test.
- Capital range where it works: unclear — this is closer to an execution-cost/impact-modeling
  insight used by funds sizing their own metaorders than a standalone retail directional
  signal; plausible only as a small-size, low-frequency overlay, not a primary strategy.
- Kill test (runnable in under 1 day with free or cheap data): using free crypto trade-tape
  data (Binance historical trades, which are free and include aggressor side), compute
  trade-sign autocorrelation out to a few hundred trades and fit a power-law decay; then test
  a simple "follow persistent sign for N trades" rule net of realistic taker fees and slippage
  over a walk-forward window, checking whether the *net-of-cost* Sharpe survives Agent 4's
  Deflated Sharpe Ratio correction (this project already has that tool built —
  `backend/agents/stats/toolkit.py`).
- Verdict: **marginal** — the only thesis in this document not disqualified by the latency
  argument, but unproven net of costs and requiring its own falsification before any
  capital commitment. Worth the one-day kill test; not worth building infrastructure around
  before that test runs.

### T8.3 — VPIN flags elevated crash/volatility risk usable for a defensive risk-gate signal
- Evidence for: original Easley/López de Prado/O'Hara (2012, *Review of Financial Studies*)
  finding that VPIN reached historically high levels over an hour before the May 2010 Flash
  Crash [reported].
- Evidence against: Andersen and Bondarenko's direct rebuttal — controlling for
  contemporaneous volume and volatility, VPIN shows **no incremental predictive power** for
  future volatility, and the bulk-volume trade classification underlying VPIN is disputed
  versus transaction-based classification, with "diametrically opposite results" reported
  under the alternative method [reported]. This is a live, unresolved academic dispute
  between the metric's own authors and named critics — not a settled positive result.
- Horizon the edge lives at: contested — proponents claim intraday (pre-crash) warning value;
  critics say it adds nothing once standard volume/volatility are controlled for.
- Infrastructure and data cost required: trade-volume-bucketed tape (does not require full
  MBO depth); moderate.
- Capital range where it works: irrelevant pending resolution of the underlying dispute — this
  is not yet a "does it work at small size" question, it's a "does it work at all,
  independent of size" question.
- Kill test (runnable in under 1 day with free or cheap data): replicate Andersen-Bondarenko's
  core test cheaply — compute VPIN on free crypto trade data around a known high-volatility
  event, then regress forward realized volatility on VPIN **with and without** contemporaneous
  volume/volatility controls; if VPIN's coefficient loses significance once those controls are
  added, that is a direct, first-party replication of the critique on this operator's own data
  and should be treated as decisive.
- Verdict: **marginal-to-dead** — even the most favorable published claim (crash early-warning)
  is disputed by name in the literature; not worth building a live risk-gate signal on without
  running the replication kill test first, and the prior should lean toward the critics given
  the specificity of their methodological objection.

### T8.4 — Iceberg / hidden-liquidity detection identifies absorption zones usable for entry/exit timing
- Evidence for: a real, if narrow, academic literature (active/pinging, model-based, and
  frequentist detection methods; CME-specific work exists) [reported]; conceptually distinct
  from and more rigorous than the retail "absorption" narrative that borrows its vocabulary.
- Evidence against: no evidence found in this research pass of net-of-cost, out-of-sample
  profitability from iceberg detection as a standalone signal — the literature located is
  about *detecting* hidden orders, not about a validated trading rule built on that detection;
  this is a meaningful gap between "detectable" and "profitably actionable."
  Additionally, genuine iceberg detection at the necessary precision generally requires MBO
  depth (to see partial refills at a price level, the tell-tale iceberg signature), which
  brings back the same real-time data-cost and latency requirements as T8.1.
- Horizon the edge lives at: unclear from available evidence — plausibly execution-timing
  scale (seconds to a few minutes) rather than a standalone directional signal.
- Infrastructure and data cost required: full MBO depth (same tier as T8.1); a purpose-built
  event-driven backtester (nautilus_trader or hftbacktest) to reconstruct queue refills.
- Capital range where it works: most plausible as an execution-quality tool (reduce slippage
  on trades whose edge comes from elsewhere) rather than an alpha source at any capital level.
- Kill test (runnable in under 1 day with free or cheap data): on free crypto L2 depth data,
  flag price levels showing repeated partial-size refills at the same price (a simple iceberg
  heuristic) and test whether price is more likely to reverse or stall at flagged levels than
  at random comparable levels, over a walk-forward sample.
- Verdict: **marginal as a standalone thesis, more promising as an execution-quality overlay**
  — reframe as reducing slippage on an existing signal rather than as a new alpha source
  before investing further.

### T8.5 — CVD / footprint-chart delta divergence as a discretionary or systematic reversal signal
- Evidence for: none found. Direct, targeted searches for academic or backtested validation
  of CVD divergence / footprint absorption returned only vendor blogs, indicator marketplace
  listings, and course content — zero peer-reviewed or rigorously backtested sources
  [reported — an absence, not a citation].
- Evidence against: the entire commercial ecosystem around this signal (indicator vendors,
  course sellers, prop-firm-adjacent education) has a direct financial interest in the
  narrative being believed regardless of whether it works, structurally identical to the
  FX-education conflict of interest documented in `f7-forex.md`.
- Horizon the edge lives at: not established by any evidence found.
- Infrastructure and data cost required: N/A pending evidence the signal exists.
- Capital range where it works: N/A.
- Kill test (runnable in under 1 day with free or cheap data): using free crypto trade data,
  construct CVD exactly as commonly defined (cumulative signed volume) and mechanically test
  the specific claimed rule ("price new high + CVD lower high = reversal warning") against
  forward returns over a walk-forward sample; this is cheap and mechanical enough that "we
  never tested the actual claimed rule" is not an acceptable reason to skip it, but going in,
  the prior should be strongly skeptical given the total absence of independent evidence.
- Verdict: **dead pending a mechanical kill test**, and even if the kill test surprises to the
  upside, treat any positive result on a single mechanical backtest of an untested folk rule
  with extreme suspicion (overfitting to a discretionary-origin rule is the most likely
  explanation for any apparent edge) before acting on it.

## Sources
- https://arxiv.org/pdf/2211.13777 — "The Short-Term Predictability of Returns in Order Book
  Markets" — OBI predictive power concentrated in next 1-2 mid-price changes, decaying to ~0
  beyond that; robust out-of-sample at seconds/tens-of-seconds horizons. [reported, via search summary]
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1712822 — Cont, Kukanov, Stoikov, "The
  Price Impact of Order Book Events" — foundational OFI-to-price-change linear relationship,
  Journal of Financial Econometrics 2014. [reported]
- https://arxiv.org/pdf/2112.02947 — "The Price Impact of Generalized Order Flow Imbalance" —
  follow-on/extension work. [reported]
- https://www.emergentmind.com/topics/order-book-imbalance-obi — OBI summary and horizon
  characterization. [reported]
- https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.131.197401 — Lillo-Mike-Farmer
  model quantitative test, trade-sign long memory tied to metaorder splitting. [reported]
- https://arxiv.org/pdf/1504.04354 — "The Long Memory of Order Flow in the Foreign Exchange
  Spot Market" — cross-asset confirmation of persistence mechanism. [reported]
- https://www.sciencedirect.com/science/article/abs/pii/S1386418113000475 — "Reflecting on the
  VPIN dispute" — the Easley/López de Prado/O'Hara vs. Andersen/Bondarenko controversy.
  [reported]
- https://academic.oup.com/rfs/article-abstract/25/5/1457/1569929 — Easley, López de Prado,
  O'Hara, "Flow Toxicity and Liquidity in a High-Frequency World," Review of Financial
  Studies 2012 — original VPIN paper, Flash Crash finding. [reported]
- https://arxiv.org/pdf/1909.09495 — "CME Iceberg Order Detection and Prediction," Zotikov
  (Devexperts) — CME-specific iceberg detection literature. [reported]
- https://onlinelibrary.wiley.com/doi/full/10.1111/jfir.12414 — "Who can see the iceberg's
  peak?", Journal of Financial Research 2025 — iceberg/information-trader literature. [reported]
- https://www.quantvps.com/blog/low-latency-trading — colocation and HFT latency figures
  (nanosecond-scale wire distance, FPGA 100-500ns tick-to-trade). [reported]
- https://electronictradinghub.com/venue-specific-latency-why-deterministic-trading-infrastructure-must-be-calibrated-per-exchange/
  — £10,000+/month/rack colocation cost context. [reported]
- CME Aurora, IL colocation cost ($12,000/month, 10G handoff, $2,000 setup) — found via search
  summary of quantvps.com low-latency-trading blog content; underlying CME facility page not
  directly reached. [reported]
- https://databento.com/blog/introducing-new-cme-pricing-plans — Databento CME Standard plan
  pricing ($179/month intro, $199/month renewal). [reported]
- https://databento.com/datasets/GLBX.MDP3 — CME Globex MDP 3.0 dataset description, confirms
  full MBO granularity is part of the feed. [reported]
- https://apicostcalc.com/polygon.html — Polygon.io Stocks Advanced pricing (~$199/month).
  [reported]
- https://www.interactivebrokers.com/campus/ibkr-quant-news/ibkr-api-depth-mark/ — IBKR API
  depth-of-market parameter documentation (`reqMktDepth`, `isSmartDepth`). [reported]
- https://www.sec.gov/files/rules/sro/mrx/2025/34-104071-ex5.pdf — Nasdaq options Depth of
  Market Feed pricing ($1,527-$2,035/month), adjacent data point for full-depth feed cost
  order-of-magnitude. [reported]
- https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams — free Binance
  depth WebSocket streams (`<symbol>@depth`). [reported]
- https://waylandz.com/quant-book-en/Tick-and-L2-Order-Book-Data-Sources/ — survey of free vs.
  paid L2 data sources across crypto and traditional venues. [reported]
- https://nautilustrader.io/docs/latest/concepts/order_book/ — nautilus_trader L3_MBO/L2_MBP
  order book types, queue-position-capable MBO support. [reported]
- https://nautilustrader.io/docs/latest/integrations/databento/ — nautilus_trader's native
  Databento integration. [reported]
- https://github.com/nkaz001/hftbacktest — hftbacktest: Python/Rust HFT backtester with
  explicit feed/order latency and queue-position fill modeling from L2/L3 data. [reported]
- https://www.quantconnect.com/forum/discussion/826/how-to-backtest-with-historical-limit-order-book-data/
  — confirms Lean/QuantConnect requires custom `BaseData` subclassing for any LOB backtesting;
  no native support. [reported]
- https://stocksharp.com/en/ — StockSharp order-book/Level-2 support claims (unverified depth).
  [reported]
- https://www.sciencedirect.com/science/article/abs/pii/S027553191530026X — "The fall of
  high-frequency trading: A survey of competition and profits" — HFT industry revenue
  collapse from ~$7.2B peak to <$1B by 2017, used as context for how competitive/thin the
  microsecond tier has become even for professional participants. [reported]
- https://www.cis.upenn.edu/~mkearns/papers/rlexec.pdf — Kearns & Nevmyvaka, "Reinforcement
  Learning for Optimized Trade Execution" — early large-scale empirical RL-on-microstructure
  work, five-minute execution-optimization horizon, context for what horizons this research
  area actually operates at in practice. [reported]
- `f2-crypto-microstructure.md` (this project, prior researcher) — confirms crypto
  order-flow/microstructure signal work was out of scope there, and independently notes
  microstructure facts are useful for execution timing rather than standalone alpha.
  [verified — internal document, read directly]
- `f7-forex.md` (this project, prior researcher) — structural template for the
  education-industry conflict-of-interest finding, reused here for the order-flow retail
  education ecosystem. [verified — internal document, read directly]

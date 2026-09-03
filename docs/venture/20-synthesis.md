# Phase 1 Synthesis — the ranked shortlist

Compiled 2026-08-27 from the six research files in `research/`.

**Update 2026-08-27:** F7 (foreign exchange) has landed and is folded in below. It was
commissioned after the first six families, at the user's prompting — FX was a genuine gap in
the original split. It produced **no promising thesis**, so the ranked shortlist is unchanged;
what it did produce is the cross-cutting finding in §4 below, which is arguably the most
useful single output of the whole study.

**Confidence warning:** no primary source was readable from this session (see
`10-research-log.md` §0). Everything below is `[reported]`. Nothing here is settled — it is a
prioritized list of what to *test*, ranked by how cheaply it can be falsified.

---

## What the six families actually returned

| Family | Promising | Marginal | Dead |
|---|---|---|---|
| F1 Equity factors | 2 | 2 | 1 + "factor zoo harvesting" |
| F2 Crypto | 0 | 3 | 2 + 1 unverified |
| F3 Options / vol | 0 | 2 | 4 |
| F4 LLM-native | 2 | 3 | 0 |
| F5 Portfolio construction | 0 | 0 | the whole premise |
| F6 Small-operator structural | 2 | 4 | 0 |
| F7 Foreign exchange | 0 | 1 | 4 |
| F8 Order flow / microstructure | 0 | 2 | 3 |

Six promising theses out of roughly thirty-five examined. That ratio is the honest base rate and
should be expected to fall further once kill tests run.

---

## The three findings that matter more than any single thesis

### 1. The cost prior kills most of the search space
Chen & Velikov (JFQA 2023): across 204 anomalies, net of realistic trading costs, the
**average nets ~4bps/month and the best nets ~10bps/month**. Harvey/Liu/Zhu's multiple-testing
correction leaves **9 of 313** factors significant at |t|>3. McLean & Pontiff: ~26% of returns
gone out-of-sample, ~58% post-publication. [all reported]

**Consequence:** any thesis sourced from a paper starts from a prior of "probably nets a few
basis points." Transaction costs are not a detail to model later — they are the first test.

### 2. Three families converged on the same place, independently
F1 (factor-decay literature), F4 (LLM/capacity reasoning) and F6 (structural-friction
literature) each arrived at **capacity-constrained small/microcap situations** without being
pointed there. The convergence is the strongest signal in the study.

**But F6 supplies the counter-argument the other two missed:** the same illiquidity that keeps
institutions out makes *retail* execution expensive too. Most classic small-cap anomalies
(January effect, index-reconstitution reversal, the small-cap premium itself) shrink or die
once realistic bid-ask spreads are applied. So the convergence points at a *region*, not a
proven edge — and the region's entry fee is a transaction-cost test.

### 3. The quantum branch is closed
F5's direct answer: sophisticated combinatorial portfolio construction does **not** add
out-of-sample Sharpe at this scale, and the case gets *weaker* at $1k–$100k, not stronger.
The defensible lever is regularization against estimation error, which the existing long-only
+ Ledoit-Wolf allocator already captures. Consistent with QAPF's own verified Agent 5 result.

### 4. Counterparty structure has been a bigger threat than strategy selection
Three of seven families independently produced the same warning, from unrelated evidence:

- **F7 (FX):** regulator-mandated disclosures show **74–89% of retail CFD accounts lose money**
  (ESMA 2018 review); individual FCA-regulated broker disclosures range ~46% to ~76%. The
  proximate cause is the dealing-desk "B-book" model, where the broker is often the client's
  direct counterparty and profits when the client loses.
- **F6 (prop firms):** 5–14% challenge pass rates, ~1–2% of challenge buyers ever paid. The
  business model is selling challenges, not funding traders.
- **F2 (crypto):** the 2025-10-10 cascade, where correctly-hedged delta-neutral accounts were
  auto-deleveraged out of their hedges because one venue priced collateral off its own
  internal order book.

**The transferable rule:** before evaluating any strategy, ask *who is on the other side, and
do they profit when I lose?* Central clearing (CME futures, listed equities) removes this
question. Dealing-desk brokers, prop-firm challenges, and single-venue crypto margin do not.
On this evidence, venue structure deserves a hard filter *before* strategy selection — not a
footnote after it.

---

## Ranked shortlist — test in this order

Ranked by **(strength of evidence that an edge exists) x (cheapness of falsification)**, not
by expected return.

### Rank 1 — T6.2 Odd-lot tender arbitrage
The only thesis where institutional exclusion is *mechanical rather than economic*: odd-lot
provisions apply to holders of fewer than 100 shares, so a large holder cannot qualify no
matter how much it wants to. Nothing else on this list has that property.
- **Limit:** caps at hundreds-to-low-thousands of dollars per event, regardless of capital.
  At $1,000 that ceiling does not yet bind. At $100k it would.
- **Kill test:** reconstruct 12 months of completed tender offers with odd-lot provisions;
  compute realized net-of-cost return per event and events-per-year. If annualized net
  return on deployable capital < 10%, or fewer than ~10 qualifying events/year, it dies.

### Rank 2 — T1.3 Volatility-scaled momentum
Daniel-Moskowitz risk-managed momentum reportedly roughly doubles static momentum's Sharpe by
scaling exposure inversely to recent realized volatility (momentum's crashes are concentrated
in high-vol rebounds).
- **Why rank 2:** cheapest possible test. QAPF already has the momentum factor, a
  COVID-spanning walk-forward window, and Deflated Sharpe Ratio. Near-zero new code.
- **Kill test:** add vol-scaling to the existing 12-1 momentum factor; run the existing
  walk-forward; compare DSR scaled vs unscaled. If DSR doesn't improve materially, it dies.

### Rank 3 — T6.1 Closed-end fund discount convergence
Reported 18.2% / 14.9% annualized in academic backtests. Mechanism is real and old.
- **Weakness:** the net-of-spread number was never verified, and CEF spreads are wide.
- **Kill test:** take the reported strategy, apply actual quoted spreads on the specific CEFs
  it would have traded, and see what survives. This is a spread-arithmetic test, not a
  signal test.

### Rank 4 — T1.5 / T4.4 Microcap capacity niche (the convergent thesis)
The region three families pointed at. Treated as a *meta-thesis* other signals run inside,
not a standalone strategy.
- **Gate 1 (data):** yfinance has known survivorship and delisting bias in exactly this
  segment. Run `backend/agents/datainfra` against a microcap universe before believing any
  return number computed from it. A backtest on survivor-only microcaps is worthless.
- **Gate 2 (cost):** measure real quoted spreads on the actual candidate universe. If the
  round-trip cost exceeds the signal, the region is closed and ranks 1–3 are the whole game.

### Rank 5 — T4.3 Earnings-call evasiveness
Most promising LLM-native thesis: semantic distance between analyst questions and management
answers in Q&A. Nobody has run a contamination check on it.
- **Prerequisite:** design the test so the model cannot have memorized the outcome — point-in-
  time text, and a model whose training cutoff precedes the test window. Without that the
  result is worthless (see below).
- **Second prerequisite:** it must beat a cheap lexical baseline. If bag-of-words does as
  well, the LLM is decoration.

### Rank 6 — T2.1 Delta-neutral funding carry — **shelved, not dead**
Real edge, wrong size (~$5–10k minimum per position) and partly wrong jurisdiction (deepest
venues restrict US persons). Revisit at ≥$10k capital.
- **Carry this forward regardless:** on 2025-10-10, ~$19B liquidated in hours and accounts
  running textbook long-spot/short-perp hedges were auto-deleveraged out of those hedges
  because one venue priced collateral off its own internal order book (USDe to $0.65). The
  hedge was correct and it did not matter. **No backtest of funding rates would ever show
  this.** It is the cleanest available example of why paper edge and live edge differ.

---

## Foreign exchange — closed, with one useful residue

F7 found no thesis worth testing at this account size:
- **Carry** — dead here. The one real documented FX risk premium, but it is compensation for
  rare fast crashes: 2008 drawdowns reported -7% to -32%; the 2015 CHF de-peg moved ~30% in a
  single session and bankrupted brokers; the Aug 2024 yen unwind produced the worst Nikkei day
  since 1987. Disqualifying negative skew at $1,000.
- **Trend/momentum** — marginal-to-dead. Reported Sharpe ~1.9 in the 2000s decaying to ~0.2
  since, so it no longer reliably offsets carry's tail as the classic pairing assumed.
- **PPP mean-reversion** — real (2.5-5yr half-life, well triangulated) but structurally
  unusable at that horizon for an operator trying to compound capital.
- **Central-bank divergence** — discretionary macro narrative; no formalized backtestable rule
  was found.

**The residue worth keeping:** FX's only genuine structural advantage over equities was
exemption from the PDT rule — and that advantage is available via **CME Micro FX futures**,
which are centrally cleared and therefore avoid the B-book conflict entirely. If the PDT
elimination above holds, the advantage disappears on both sides. FX's real draw for a small
account is high leverage plus near-zero minimums, which is precisely the combination that
destroys small accounts fastest.

---

## Order flow — closed except one slower-horizon thesis (F8, 2026-09-03)

Commissioned at the user's prompting; the original seven families had no
order-flow coverage. **Direct answer: no, a retail operator cannot systematically
extract an order-flow edge** — with one narrow exception.

- **Order book imbalance (OBI)** — the most-studied signal, and unreachable.
  Predictive power is concentrated in the next 1-2 order-book events and decays
  to near-zero within seconds to tens of seconds (Cont-Kukanov-Stoikov 2014).
  Colocated HFT runs 100-500ns tick-to-trade; a retail round trip is 10-100ms,
  ~1ms on a dedicated trading VPS. That is not "somewhat slower" — it is a
  different physics regime, and the retail operator is trading a stale signal.
  [reported]
- **Trade-sign long memory / metaorder persistence** (Lillo-Mike-Farmer,
  Bouchaud) — **the one exception.** Driven by institutional order-splitting, so
  it lives on a structural timescale of minutes to hours and is NOT latency-gated.
  Unproven net of costs: the same order-splitting that creates the persistence
  also creates the impact costs that would eat any edge from anticipating it.
  Worth a real kill test. [reported]
- **VPIN** — marginal-to-dead; disputed by Andersen & Bondarenko, who find no
  incremental predictive power once volume and volatility are controlled for.
- **Iceberg detection** — real academic literature, but no evidence of profitable
  trading rules built on it. Better used as an execution-quality overlay than as
  alpha.
- **CVD / footprint charts / delta divergence** — the popular retail canon.
  Targeted searches returned **zero peer-reviewed evidence**; only vendor blogs
  and course material. Same education-industry conflict pattern as retail FX
  (see §4) — the people teaching it profit from volume or from selling courses.

**Cheapest kill test, and it costs nothing:** crypto exchanges give away
full-depth L2 order books, unlike CME MBO via Databento (~$179-199/month). Pull
free Binance/Coinbase L2, compute OBI, regress forward returns across horizons
from 100ms to 5min, and plot the decay curve. Expect collapse by 30-60 seconds.
Crypto is shelved for *trading* (D6) but is the cheapest venue on earth for this
*research*.

**If anything survives:** CME Micro E-minis (MES/MNQ, ~$50-300 intraday margin)
are the correct live venue — centrally cleared, so they pass the D9 venue filter.
**But the existing Qlib/OHLCV harness cannot evaluate any order-flow thesis** —
order-book reconstruction and queue-position modelling are missing data
structures, not a resolution setting. That needs `nautilus_trader` or
`hftbacktest` (both open-source, both with genuine queue modelling). Lean cannot
do it natively. Note: `nautilus_trader` is one of the nine stale untouched forks
in the fork audit — if this thesis survives, it becomes the first fork with a job.

---

## Declared dead — do not revisit without new evidence

- Everything in options/volatility at this account size. Every thesis is either a sold risk
  premium with a documented account-ending tail (Feb 2018, Mar 2020, Aug 2024) or a retail
  structural loser after costs. A Chicago Fed 2025 paper reportedly finds the equity variance
  risk premium has shrunk toward statistical zero over 15 years.
- Short-vol ETPs (this is literally the XIV liquidation), 0DTE long/directional, dispersion
  (needs capital not available), put-call parity arb (latency).
- Crypto basis at $1k (CME Micro BTC margin ~$2,800), solo MEV, cross-exchange latency arb.
- Naive standalone size effect; unconditional low-volatility (crowded, trades expensive).
- Quantum and quantum-inspired combinatorial optimization as a source of edge.
- **All of foreign exchange at this account size** — carry, trend, PPP, policy divergence.
  Retail FX through a dealing-desk broker is disqualified on venue structure alone.
- **Order book imbalance and the retail order-flow canon** (CVD, footprint,
  delta divergence) — OBI is real but decays inside the retail latency floor;
  the canon has no peer-reviewed support at all.
- **Prop-firm funded accounts as a capital strategy.** Reported 5–14% challenge pass rates,
  ~1–2% of challenge buyers ever paid. Legitimate only as leverage for someone already
  independently profitable — never as a route to becoming profitable.

---

## Two corrections to earlier assumptions in this project

### The PDT rule — likely obsolete
F3 and F6 independently reported that the SEC approved FINRA's **elimination of the pattern-
day-trader framework and the $25,000 minimum**, approved 2026-04-14, effective 2026-06-04,
with broker implementation running to Oct 2027. Real-time intraday margin replaces it.

**Status: `[reported]`, NOT verified.** Both agents used the same blocked-egress search tool,
so this is correlated evidence, not independent confirmation. `sec.gov` and FINRA were both
blocked. **Verify from a machine with open network before this changes any decision** — it
would materially widen what is viable at small account size, and it is currently stated in
`00-charter.md` as a constraint.

### LLM alpha is contaminated
Gao, Jiang & Yan (2025) built a direct memorization test ("Lookahead Propensity") and
attributed roughly **37% of the headline ChatGPT-predicts-returns effect to training-data
contamination**, concentrated exactly where the naive result looks strongest — small caps and
famous names. The effect is real but materially overstated. Anything in this literature
published before ~2025 without an explicit memorization test should be discounted by default.

---

## Recommended next step

Run kill tests in rank order, one at a time, cheapest first. Rank 2 (vol-scaled momentum) is
the natural first move because it needs almost no new code and exercises infrastructure that
already exists.

**Do not build anything else yet.** The base rate says most of these die. Six promising
theses will probably become one or two. Infrastructure built before that point is
infrastructure built for theses that turn out not to exist — which is the specific failure
this project is designed to avoid.

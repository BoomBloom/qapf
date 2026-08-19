# Viable Alpha Families for a 15-Name, Long-Only, Daily-OHLCV Book

**Question:** For a long-only book of ~15 US large caps, ~10 years of daily OHLCV, no alternative
data, and $1,000 of capital — which families of trading strategy are realistically viable, and which
are ruled out by the data, the universe size, the rebalance frequency, or the long-only constraint?

**Scope of sources.** The operator-supplied primary source (Kakushadze & Serur, *151 Estrategias de
Trading*, arXiv 1912.04492, Spanish edition) read directly from the PDF via `pdftotext`; peer-reviewed
journal articles (JF, JFE, JoB) read from author-hosted or publisher PDFs; López de Prado's own
whitepaper text; and the QAPF repository's own source code and backtest output. Where I could only
reach an abstract or a publisher's description rather than full text, that is stated inline and in the
source table.

**This is an engineering feasibility analysis of strategy families against hard technical constraints.
It is not investment advice, and nothing here is a recommendation to trade any security.**

---

## 0. Two corrections to the brief's premises, before anything else

Both of these change the answer, so they go first.

### 0.1 The system does not rebalance daily. It rebalances monthly.

The brief specifies "daily rebalance". The built system does not do that.
`backend/agents/backtest/walkforward.py:114` sets `rebalance_freq: str = "MS"` — pandas' *month start*
frequency. The signal is recomputed monthly and held constant in between; only the *execution* engine
runs on a daily clock (`EXCHANGE_KWARGS = {"freq": "day", ...}`, line 36). The backtest report
confirms it: `n_rebalances = 35` over 2018-01-01 → 2020-10-30, which is 35 months, and the equity
curve in `frontend/data/snapshot.json` has 148 points at a median spacing of 7 days.

The module docstring says as much: the signal is held "constant until the next rebalance -- exactly
what 'monthly' means" (`walkforward.py:71`).

This matters because most of what follows is a turnover-and-cost argument, and monthly is roughly
21× cheaper than daily. **Several families that are ruled out at daily frequency are ruled back in at
monthly.** I analyse both frequencies below and label which is which. If the roadmap genuinely intends
to move to daily rebalancing, that is a decision that needs its own justification — at $1,000 it is
mechanically impossible (§1.1).

### 0.2 The Deflated Sharpe of 0.414 is not the honest number. It is an upper bound.

The reported DSR is 0.414 with `dsr_trials = 4` (`snapshot.json`). Four is not a defensible trial
count. Reconstructing the DSR from the published equity curve using the repository's own
implementation (`agents/stats/toolkit.py:89`) reproduces the reported figure closely at `n_trials=4`
and shows how fast it decays:

| `n_trials` | E[max SR] under H₀ | DSR |
|---|---|---|
| 1 | 0.000 | 0.791 |
| 2 | 0.043 | 0.626 |
| **4 (as reported)** | **0.087** | **0.429** |
| 8 | 0.120 | 0.288 |
| 16 | 0.149 | 0.189 |
| 32 | 0.173 | 0.123 |
| 128 | 0.216 | 0.050 |

*(Reconstructed from the 148-point weekly equity curve; the repo computes it on its internal return
series, hence 0.429 here vs. 0.414 reported. Per-period Sharpe 0.0712, skewness −1.58, kurtosis 12.49,
n = 147.)*

The strategy as built has four hand-set factor weights across four macro regimes — sixteen numbers —
plus six lookback windows (`MOMENTUM_LONG=252`, `MOMENTUM_SKIP=21`, `REVERSAL_WINDOW=5`,
`VOL_WINDOW=60`, `VOLUME_SHORT=20`, `VOLUME_LONG=60` in `agents/alpha/factors.py`), plus `topk=5` and
`n_drop=2`. The `REGIME_FACTOR_WEIGHTS` docstring in `agents/alpha/combiner.py` argues these are
"priors, not fitted parameters… deliberately hand-set and auditable rather than optimized". That is an
honest and unusually disciplined stance, and it genuinely reduces overfitting relative to a grid
search. But it does not reduce the *trial count* to four, because the priors were still chosen by a
process that could have chosen otherwise, and the lookbacks are conventional choices each of which had
alternatives.

López de Prado is explicit about why this is the pivotal quantity. In "The 10 Reasons Most Machine
Learning Funds Fail" (GARP whitepaper, Pitfall #10), he gives the expected maximum Sharpe of `I`
trials on a martingale — i.e. an instrument with *no* true edge:

> E[max{xᵢ}] ≈ (1−γ)Z⁻¹[1−1/I] + γZ⁻¹[1−e⁻¹/I] ≤ √(2·log[I])

and states that without the trial count "it is not possible to determine the Family-Wise Error Rate
(FWER), False Discovery Rate (FDR), Probability of Backtest Overfitting (PBO) or similar." The DSR's
rejection threshold SR* is defined in terms of `N` independent trials and `V[{SR_n}]`, the variance
*across trials*. The repo's implementation substitutes `1/√n_observations` for `√V[{SR_n}]`
(`toolkit.py:104`) — a standard and defensible simplification — which makes `n_trials` the *only*
lever controlling honesty.

**Practical consequence:** the strategy did not merely fail its bar at 0.414. Under any trial count
above ~30 it fails at DSR < 0.13. Whatever replaces it must be validated with an honest `N`, and that
requirement shapes the shortlist in §4 — I have preferred families with *few free parameters*
specifically because every parameter is a trial.

---

## 1. The constraints, restated as binding arithmetic

The universe is fixed at 15 names (`backend/dashboard/export.py:22`): AAPL, MSFT, GOOGL, AMZN, NVDA,
JPM, V, WMT, KO, PEP, XOM, CVX, JNJ, PG, HD — 5 tech, 2 financials, 4 staples, 2 energy, 1 healthcare,
1 discretionary.

### 1.1 Capital is the hardest constraint, and it is harder than it looks

Live closing prices for the 15 names (yfinance, 2026-08-19):

```
AAPL 210.02   AMZN 259.45   CVX  205.74   GOOGL 344.20   HD   337.49
JNJ  271.11   JPM  363.25   KO    88.82   MSFT  481.63   NVDA 219.74
PEP  140.13   PG   143.45   V    364.25   WMT   115.20   XOM  165.56
```

**One share of each name costs $3,810 — 3.8× the entire account.**

Equal-weighting $1,000 across 15 names is $66.67 per position, which buys a *fraction* of a share of
every single name in the universe (0.14 shares of MSFT, 0.75 of KO — the cheapest). Even the current
`topk=5` construction at $200 per position buys less than one whole share for 9 of the 15 names.

Two consequences, and they are structural rather than inconvenient:

1. **Without fractional-share support the book is not implementable at all.** Not "expensive" —
   arithmetically impossible. The rounding step in Kakushadze & Serur §3.1, `Qi = I × wi / Pi(0)`,
   yields Qi < 1 for every name.
2. **With fractional shares, any per-trade fixed cost is fatal.** The backtest's own configuration
   sets `"min_cost": 5` — a $5 minimum commission per trade (`walkforward.py:36-43`). On a $66.67
   position that is a **7.5% round-trip haircut on entry alone**. The backtest was run against a
   $1,000,000 notional (`PORTFOLIO_VALUE = 1_000_000` in `dashboard/export.py:31`), where $5 is
   negligible. At $1,000 it is not. **The reported backtest results do not transfer to the stated
   capital base**, and re-running the existing strategy at $1,000 notional with the same cost model
   would be the single cheapest falsification test available.

At *daily* rebalancing with `n_drop=2` (up to 4 trades/day), a $5 minimum cost is $20/day against
$1,000 — 2% per day, or complete ruin inside a quarter. This is why §0.1 matters: **daily rebalancing
of this book at this capital level is ruled out on cost arithmetic alone, independent of any alpha.**

### 1.2 Universe size: 15 names cuts both ways

Kakushadze & Serur are unusually direct about why cross-sectional statistical arbitrage needs breadth.
Their §3.21 ("Comentarios adicionales") draws the distinction explicitly: single-stock technical
strategies have no *a priori* reason to predict, whereas mean-reversion strategies "se espera que
funcionen porque se espera que las acciones estén correlacionadas si pertenecen a la misma industria" —
and the key difference between technical analysis and statistical arbitrage is that the latter rests on
"un gran número de acciones cuyas propiedades están 'estratificadas'". The statistical element *is* the
cross-section. With 15 names you do not have one.

Their §3.20 (alpha combos) puts a number on the intended scale: the worked example assumes "el mismo
universo de (digamos, 2,500) las acciones más líquidas de los Estados Unidos", combining alphas whose
count "puede ser muy grande (cientos de miles e incluso millones)". They are candid that individual
mined alphas are "débiles, efímeros y no se pueden operar por sí solos, ya que cualquier ganancia se
erosionaría por los costos transaccionales."

But the same footnote that damns the cross-section *blesses* the covariance matrix. Footnote 61 warns
that a sample covariance matrix is singular when T ≤ N+1, and that off-diagonal elements are unstable
out-of-sample "a no ser que T ≫ N, lo que es muy raro". Here N = 15 and T ≈ 2,500 daily observations —
so T/N ≈ 167. **This project is in the rare regime the footnote describes as almost never happening.**
The 15-name covariance matrix is genuinely well-conditioned, and Ledoit-Wolf shrinkage (already wired
in via `ShrinkCovEstimator` in `agents/portfolio/allocator.py`) is close to unnecessary at this ratio.
Risk-based allocation is the one thing this universe size makes *easier*, not harder.

### 1.3 Long-only is a hard architectural constraint, verified in source

Confirmed directly in the vendored upstream: `reference/qlib/qlib/contrib/strategy/optimizer/optimizer.py:230`
reads `bounds = so.Bounds(0.0, 1.0)`. The allocator docstring
(`agents/portfolio/allocator.py`) records the decision and its reasoning — negative-signal names get
zero weight and their capital stays in cash, because "shorting needs borrow availability, margin, and
its own risk treatment — none of which exist in this system yet".

Every family marked "requires shorting" below is therefore blocked on an architecture change, not a
parameter change.

### 1.4 Data: daily OHLCV only — and three of the four columns are currently unused

The existing factor set (`agents/alpha/factors.py`) uses **close and volume only**. `momentum_12_1`,
`reversal_5d`, and `low_volatility` all take a `prices` series; `volume_trend` takes `volumes`. Open,
high, and low are never touched.

This is a genuine, free, already-paid-for information source being left on the floor, and it is the
basis for two of the shortlist entries in §4.

---

## 2. The ruled-in / ruled-out table

Families are drawn from the Kakushadze–Serur taxonomy (chapters 2–19), restricted to those that could
conceivably touch a long-only equity book, plus the families raised in the brief.

| # | Family | K&S § | Verdict | Binding reason |
|---|---|---|---|---|
| 1 | **Volatility targeting / vol-managed exposure** | 6.5 | **RULED IN — top pick** | Per-name and per-portfolio; needs only close-to-close returns; long-only native (the complement is cash); ~1 free parameter. Peer-reviewed alpha 4.9% on the market factor. |
| 2 | **OHLC-based volatility estimation** (Garman-Klass, Parkinson, Yang-Zhang) | — | **RULED IN — enabler** | Uses the O/H/L columns already downloaded and currently discarded. Not a strategy; a strictly better input to #1, #3 and the risk engine. |
| 3 | **Absolute / time-series momentum + dual momentum** | 3.11, 4.1.2, 10.4 | **RULED IN** | Explicitly per-name with "sin interacción transversal" (§3.11); long-only *by construction* with a T-bill/defensive leg (Antonacci); no cross-section required. |
| 4 | **Single-name mean reversion vs. own level** (OU / channel / IBS) | 3.15, 4.4 | **RULED IN, cautiously** | IBS (§4.4) needs only prior-day H/L/C. Long-or-flat variant needs no shorting. But K&S §3.21 warns the statistical justification is much weaker without a cross-section. |
| 5 | **Risk-based allocation** (min-variance, risk parity, HRP) | 3.18 | **RULED IN — but it is not alpha** | Footnote 61's T ≫ N condition is satisfied (T/N ≈ 167). Already available via Qlib's `PortfolioOptimizer`. Changes the risk profile, not the expected return. |
| 6 | **Meta-labelling over an existing primary signal** | — (López de Prado) | **RULED IN, as a filter** | Operates on signals you already have; converts a direction call into a size call. Needs no new data. Does not create edge where none exists. |
| 7 | **Cross-sectional multifactor ranking** (the current approach) | 3.1–3.7, 3.20 | **RULED OUT at this universe size** | §3.21: the edge *is* the cross-section. Deciles of 15 names are groups of 1–2. Already empirically failed here: DSR 0.414 (honestly ≤0.13), Sharpe 0.495, underperformed buy-and-hold 27.5% vs 50.98%. |
| 8 | **Pairs trading** | 3.8 | **RULED OUT — requires shorting** | K&S define it as "Esta estrategia dólar-neutral", with the constraint Σ Pi Qi = 0 (eq. 291) requiring Qi < 0. Structurally impossible long-only. |
| 9 | **Statistical arbitrage / mean reversion, multi-group** | 3.9, 3.9.1, 3.10 | **RULED OUT — requires shorting AND breadth** | Dollar-neutrality constraint eq. (296); Di = −γ·R̃i (eq. 297) is negative for half the book by construction. Also needs the "estratificación" of §3.21. |
| 10 | **Market-neutral / dollar-neutral optimization** | 3.18.1 | **RULED OUT — requires shorting** | The Lagrange construction (eq. 354–358) exists solely to impose Σwi = 0. Meaningless under `Bounds(0.0, 1.0)`. |
| 11 | **Alpha combo / 101-alphas mining** | 3.20 | **RULED OUT — needs ~2,500 names** | K&S's own worked scale. Mined alphas are "débiles, efímeros y no se pueden operar por sí solos". 15 names cannot support it. |
| 12 | **Market making** | 3.19 | **RULED OUT — needs order book + HFT infra** | K&S: success depends on queue position, "básicamente, se trata de la velocidad con la que se inician, cancelan y reemplazan las órdenes. La infraestructura y la tecnología son claves." No book data, no colocation, daily bars. |
| 13 | **Earnings momentum (SUE)** | 3.2 | **RULED OUT — needs fundamentals** | Requires quarterly EPS and 8 quarters of surprise history (eq. 274). Not in daily OHLCV; yfinance fundamentals are not point-in-time and carry survivorship/restatement bias. |
| 14 | **Value (B/P)** | 3.3 | **RULED OUT — needs fundamentals + breadth** | Book value not in OHLCV. Also a decile strategy on 15 names. |
| 15 | **Residual momentum** | 3.7 | **RULED OUT — needs factor returns + breadth** | Requires MKT/SMB/HML series (eq. 278) over a 36-month regression, then deciles. External data plus a cross-section. |
| 16 | **Implied-volatility signals** | 3.5 | **RULED OUT — needs options data** | Requires call/put IV changes. Not available. |
| 17 | **All option strategies** | 2.2–2.57 | **RULED OUT — no options data, no capital** | 56 strategies, all requiring an options chain. A single ATM contract on most of these names exceeds the account. |
| 18 | **Merger arbitrage** | 3.16 | **RULED OUT — needs deal data + event flow** | Requires M&A announcements and terms; 15 mega-caps generate almost no target-side events. |
| 19 | **Sector/ETF rotation** | 4.1–4.2 | **RULED OUT of the stated universe** | Would require trading ETFs, not these 15 stocks. Viable as a *different* project; noted because §4.1.2 (dual momentum) is the source of shortlist item #3. |
| 20 | **KNN / ML on a single stock** | 3.17 | **RULED OUT on sample size** | K&S themselves flag that tuned weights "pueden ser (y muchas veces son) inestables fuera de muestra". ~2,500 daily observations per name with overlapping T-day labels is far too little for reliable OOS fitting; every hyperparameter is another DSR trial (§0.2). |
| 21 | **Leveraged-ETF decay harvesting** | 4.5 | **RULED OUT — requires shorting** | K&S: the trade is to *sell* both the leveraged and inverse ETF. |
| 22 | **VIX futures basis / variance risk premium** | 7.2–7.6 | **RULED OUT — needs futures + shorting** | Different asset class, margin account, and typically short volatility. |
| 23 | **FX carry, commodities, fixed income, CDO/convertible/tax arb, distressed, real estate** | 5, 8–17 | **RULED OUT — wrong asset class** | Out of scope for a US large-cap equity book. |

---

## 3. Reasoning on the contested calls

Three verdicts deserve more than a table row, because a reasonable person could argue them.

### 3.1 Why cross-sectional multifactor is ruled out rather than "tune it"

The temptation is to keep the current architecture and fix the weights. The evidence says the problem
is structural, not parametric.

- **The mechanism requires breadth.** K&S §3.21 is unambiguous that stratification across many names
  is what converts a technical indicator into a statistical claim. A "top decile" of 15 names is 1.5
  names. The `topk=5` construction is effectively "hold a third of the universe", which is a
  concentrated bet, not a factor portfolio.
- **The empirical result is already in.** Total return 27.54% vs. benchmark 50.98% over 2018-01-01 →
  2020-10-30; Sharpe 0.495; max drawdown −36.7%. The strategy underperformed equal-weight buy-and-hold
  by 23 percentage points while taking a 37% drawdown.
- **The return distribution is the wrong shape.** Skewness −1.58, kurtosis 12.49. The DSR formula
  penalises exactly this: PSR "decreases with fatter tails (γ̂₄)" per the GARP whitepaper. A negatively
  skewed, fat-tailed equity curve is the signature Daniel & Moskowitz (2016) describe for momentum
  crashes — and the sibling research note in this repo
  ([`regime-factor-evidence.md`](regime-factor-evidence.md)) already established that the *regime*
  conditioning layer is conditioning on the wrong variable (macro growth × inflation quadrants rather
  than market state × volatility).

Taken together: the factor layer lacks the breadth its mechanism requires, and the regime layer
conditions on a variable the literature does not support. Tuning the weights addresses neither.

### 3.2 Why single-name mean reversion is "cautiously" ruled in rather than ruled out

This is the call I am least confident in, and I want to be explicit about why.

The case *for*: IBS (K&S §4.4, eq. 370) — `IBS = (P_C − P_MI) / (P_MA − P_MI)` — needs only the
previous day's high, low, and close. It is one line of pandas, has zero fitted parameters, and uses
data already downloaded. A long-or-flat version (buy when IBS is low, hold cash otherwise) needs no
shorting. Donchian channels (§3.15, eq. 329–330) are similarly parameter-light.

The case *against*: K&S §3.21 explicitly groups single-stock technical strategies among those
"consideradas 'no científicas' por muchos profesionales y académicos", noting there is no fundamental
reason a moving-average crossover should predict. They soften this — trend-following *is* built on
moving averages — but the softening is that momentum provides the economic story, not that the
technicals do. For mean reversion specifically, their stated mechanism is *correlation between related
stocks*, which is the cross-sectional case that is ruled out here.

So: ruled in as cheap to test and honest about parameters, but with no strong prior that it works, and
it should be held to the same DSR bar as everything else. K&S also describe IBS cross-sectionally as a
dollar-neutral decile trade — the long-only single-name adaptation is *mine, not theirs*, and inherits
none of their evidence.

### 3.3 Why "long-only" is doing more damage than the universe size

Of the 23 families above, **five are ruled out specifically and solely because shorting is
unavailable** (#8, #9, #10, #21, #22) — and #9/#10 are the two that the Kakushadze–Serur equities
chapter treats as its main event. The mean-reversion and statistical-arbitrage machinery of §3.9–3.18
is the intellectual core of that chapter, and every construction in it is built around Σ Pi Qi = 0.

This is worth stating plainly for the roadmap: **the long-only constraint, not the 15-name universe,
is what removes the largest and best-evidenced block of the catalogue.** Lifting it means adding a
margin model, borrow availability, and short-specific risk treatment (the deferred Agent 16), and
changing one line in Qlib's optimizer. Laurent Bernut's *Algorithmic Short Selling with Python*
(Packt, 2021) is the operator's cited reference for that work; per the publisher's description it
covers regime definition, position sizing, and a chapter on the pitfalls — short squeezes and borrow
fees. **I was not able to access the book's full text**, so I am citing it only as a pointer to the
intended methodology, not as evidence for any claim here.

That said — lifting the constraint does *not* rescue pairs/stat-arb at this universe size, because
those also need breadth (§1.2). It would open them at a larger universe. Both constraints bind.

---

## 4. Ranked shortlist: 3–5 families worth trying next

Ranked by expected-value-per-unit-of-effort, with a bias toward **few free parameters**, because §0.2
established that every parameter is a DSR trial.

---

### #1 — Volatility-managed exposure (scale the whole book by inverse realized variance)

**What it is.** Hold the existing long book, but scale gross exposure by the inverse of recent
realized variance, parking the remainder in cash. Moreira & Muir's construction (JF 2017, eq. 1):

> f^σ_{t+1} = (c / σ̂²_t(f)) · f_{t+1}

where σ̂²_t(f) is the previous month's realized variance computed from daily returns (their eq. 2 uses
22 daily observations), and `c` is a constant chosen so the managed portfolio has the same
unconditional standard deviation as buy-and-hold. They note `c` "has no effect on our strategy's Sharpe
ratio".

**What it needs.** Daily closes only — already available. One parameter (the variance lookback). No
shorting: the complement of a scaled long position is cash, which is exactly what
`agents/portfolio/allocator.py` already does with negative-signal names. K&S §6.5 gives the same idea
in the simpler `w = σ*/σ` form with a rebalance-threshold κ to suppress turnover.

**Why it might work where the current approach didn't.** It is not a cross-sectional bet, so §1.2's
breadth problem does not apply. Moreira & Muir report, for the market portfolio, "an alpha of 4.9%, an
appraisal ratio of 0.33, and an overall 25% increase in the buy-and-hold Sharpe ratio", across "the
market, value, momentum, profitability, return on equity, investment, and betting-against-beta factors
in equities as well as for the currency carry trade." The mechanism is that "there is little relation
between lagged volatility and average returns but there is a strong relationship between lagged
volatility and current volatility" — volatility is forecastable, returns are not, so the risk-return
trade-off is predictably worse in high-volatility months.

Critically for this project, they address the two objections that would otherwise kill it here: the
strategies survive "realistic transaction costs and tight leverage constraints", and §III.B tests
variants that cap leverage at 1 and 1.5 explicitly to reduce trading. **A leverage-capped variant is
long-only-and-cash compatible with no modification.**

It also directly targets the current strategy's worst property: a −36.7% max drawdown with −1.58
skewness. Moreira & Muir's Table III shows betas are "relatively lower in recessions" (β₁ < 0 for every
factor tested; MktRF ×1rec = −0.51).

**What falsifies it early and cheaply.** Apply the scaling to the *existing* backtest's return series
as a post-processing step — no re-run of the pipeline required, ~20 lines. If the Sharpe does not
improve and the max drawdown does not shrink on 2018–2020 data (which spans COVID, the ideal stress
case), abandon it. Cost: under an hour. This is the highest-information, lowest-cost test available.

**Caveat I want on record:** Moreira & Muir's result is for *factor* portfolios over long samples, not
for a 15-name concentrated book over 35 months. The mechanism (volatility is persistent, returns are
not) should carry, but the magnitudes should not be expected to.

---

### #2 — OHLC-range volatility estimators (an enabler, not a strategy)

**What it is.** Replace close-to-close standard deviation with an estimator that uses the open, high,
and low — Yang & Zhang (2000), or its simpler predecessors Parkinson and Garman-Klass.

**What it needs.** The O/H/L columns already being downloaded and discarded by
`agents/alpha/factors.py`. Zero new data. Zero new parameters.

**Why it matters here.** Yang & Zhang's estimator is, per the published abstract, (a) unbiased in the
continuous limit, (b) independent of the drift, (c) consistent in handling opening jumps, and has "the
smallest variance among all estimators with similar properties", with accuracy improvement over the
classical close-to-close estimator described as "dramatic for real-life time series". (*Journal of
Business* 73(3), 477–492.) **I read the abstract and the estimator's stated properties, not the full
paper** — the specific efficiency multiple is behind JSTOR/SSRN paywalls and I am not quoting one.

The point is leverage: a better volatility estimate improves shortlist item #1 (whose entire signal
*is* a variance estimate), improves the `low_volatility` factor, improves the CRO's VaR/CVaR in
`backend/risk/`, and improves the covariance input to `agents/portfolio/allocator.py`. One change,
four consumers. It creates no alpha by itself, which is why it is an enabler rather than a strategy —
but it is the cheapest quality improvement in this document.

**What falsifies it.** It essentially cannot fail on its own terms — a lower-variance estimator of the
same quantity is not a bet. The falsifiable claim is downstream: if swapping the estimator does not
change #1's results at all, then #1's signal was not variance-limited and the effort stops there.

---

### #3 — Absolute (time-series) momentum with a cash/defensive leg

**What it is.** Per name, go long only if its own trailing 12-month return exceeds a hurdle; otherwise
hold cash. Optionally combine with relative ranking across the 15 (dual momentum).

**What it needs.** Daily closes and a T-bill proxy. Two parameters (lookback, hurdle). No shorting.

**Why it might work where the current approach didn't.** Three independent reasons:

1. **It is explicitly not cross-sectional.** K&S §3.11 on moving-average signals: "Se puede aplicar
   fácilmente a múltiples acciones (siguiendo la lógica de acciones individuales, **sin interacción
   transversal entre las señales para acciones individuales**)." The 15-name breadth problem does not
   bind.
2. **The long-only case is the case the literature actually makes.** Antonacci (2012/2017) defines
   absolute momentum as whether an asset "has outperformed Treasury bills over the past year", with
   T-bills serving "as both a hurdle rate before we can invest in other momentum assets, as well as a
   safe, alternative investment". His conclusion #2: "Long side momentum works best when used with a
   hurdle rate and safe alternative asset." His composite reports annual return 14.90%, standard
   deviation 7.99%, Sharpe 1.07 vs. 0.50 for the equal-weight benchmark, and max drawdown −10.92% vs.
   −26.77%. **This is the one family in the catalogue whose published evidence is specifically for a
   long-only construction with a cash leg.**
3. **It attacks the drawdown directly.** The current book's −36.7% drawdown comes from being fully
   invested through the COVID crash. An absolute-momentum filter is precisely a rule for not being.

K&S §4.1.2 gives the same construction: buy only if the market index is above its 100–200 day moving
average, otherwise hold an uncorrelated asset (eq. 363).

**What falsifies it early and cheaply.** Backtest the simplest possible version — long the 15 names
equal-weighted only when each is above its own 200-day moving average, cash otherwise — over
2018–2020, and compare against equal-weight buy-and-hold on *drawdown*, not return. Absolute momentum
is expected to *cost* return in a bull market and *save* drawdown in a crash; if it does not reduce the
−36.7% materially, the premise is wrong. Two free parameters means the DSR trial count stays honest at
N ≈ 10–20, where a Sharpe of ~0.8 would be needed to clear DSR 0.95.

**Caveat I want on record, and it is a real one:** Moskowitz, Ooi & Pedersen's "Time Series Momentum"
(*JFE* 104(2), 228–250, 2012) — the canonical reference — documents the effect on **58 liquid futures
contracts, not individual stocks**. Their paper says so directly: "Focusing on liquid futures instead
of individual stocks". Their diversified portfolio yields "a Sharpe ratio greater than one on an annual
basis, or roughly 2.5 times the Sharpe ratio for the equity market", but that is a *diversified,
cross-asset-class* portfolio, and the sizing rule is "40%/σ_{t−1}" — an ex-ante volatility target that
**generally requires leverage** and is therefore not directly available to this book. Antonacci's
modules are likewise asset-class *pairs* (foreign/US equities, high-yield/credit, equity/mortgage
REITs, gold/Treasuries), not single stocks. **Neither evidence base is 15 US large caps.** Expect the
effect to be weaker and noisier here than either paper reports.

---

### #4 — Risk-based allocation (minimum-variance / risk parity) as the default book

**What it is.** Stop trying to forecast returns. Allocate the 15 names by risk contribution alone.

**What it needs.** A covariance matrix — which, per §1.2, is the one estimation problem this universe
size makes *easy* (T/N ≈ 167, comfortably inside K&S footnote 61's T ≫ N requirement). Qlib's
`PortfolioOptimizer` already exposes `gmv`, `mvo`, `rp`, and `inv`, and
`agents/portfolio/allocator.py` already imports it. Zero new dependencies. Zero return forecasts, hence
**zero alpha parameters and a near-honest DSR trial count of ~1–4.**

**Why it might work where the current approach didn't.** It is not an alpha strategy and should not be
sold as one — it will not beat buy-and-hold on return. What it does is remove the layer that
demonstrably failed. The current pipeline's return forecast (rank-normalized factor scores) is
acknowledged in the allocator's own docstring not to be a return forecast at all: "A rank-normalized
signal in [−1, +1] is not a return forecast, and mean-variance optimization formally wants the latter."
Minimum-variance sidesteps that mismatch entirely by not requiring expected returns.

**Its real role is as the benchmark that any future alpha must beat.** Right now the comparison is
against equal-weight buy-and-hold, which the strategy lost to. A risk-based book is a *harder* and
more honest bar, and having it in place makes every subsequent experiment interpretable.

**What falsifies it.** Nothing — it is a baseline, not a hypothesis. The useful test is the inverse: if
minimum-variance on these 15 names beats the full 12-agent pipeline on risk-adjusted return, that is a
strong signal that the alpha layer is subtracting value, and it should be reported as such.

---

### #5 — Meta-labelling as a sizing filter over whichever primary signal survives

**What it is.** López de Prado's construction: keep the primary model's *direction* call, and train a
secondary binary classifier on whether to *act* on it and at what size.

**What it needs.** An existing primary signal (any of #1, #3, or even the current factor combo) plus
labels. No new data.

**Why it might work.** It separates two decisions that the current pipeline conflates. Per the GARP
whitepaper, meta-labelling limits overfitting effects and is "particularly useful to 'quantamental'
firms". The natural labelling scheme is the triple-barrier method — profit-take, stop-loss, and a
time-out, with the label set by whichever barrier is hit first — which is a better fit for a book that
must control drawdown than a fixed-horizon return label.

**Why it is ranked last, and honestly.** It is the highest-effort item here and it **cannot create edge
where none exists** — it only improves the precision/sizing of a signal that already has some. It also
reintroduces every ML hazard §0.2 warns about: it needs purged, embargoed cross-validation (standard
k-fold "fails in finance because observations cannot be assumed to be drawn [IID]"), and each
hyperparameter is another DSR trial. **Do not start here.** Start at #1 or #4, establish that something
has genuine edge, and only then consider #5.

Note also that López de Prado's Pitfall #9 argues walk-forward backtesting — which is exactly what
`agents/backtest/walkforward.py` implements — is itself prone to overfitting, and recommends
Combinatorial Purged Cross-Validation instead, which "allows us to derive a distribution of Sharpe
ratios, as opposed to a single (likely overfit) Sharpe ratio estimate". Agent 14 already computes a
`sharpe_dispersion` of 0.383; CPCV would put that number on a principled footing.

---

## 5. What this project does not have, stated bluntly

Consolidating the ruled-out reasoning into the honest list:

- **No breadth.** 15 names cannot support cross-sectional ranking, decile portfolios, stat-arb
  stratification, or alpha mining. K&S's own worked scale is 2,500 names. This is not close.
- **No shorting.** Removes the entire mean-reversion/stat-arb core of the equities chapter — the
  best-developed material in the primary source.
- **No fundamentals.** Kills value, earnings momentum, quality, and residual momentum. yfinance
  fundamentals are not point-in-time and would introduce look-ahead bias that the existing
  `test_no_lookahead_bias` check would not catch, since it only guards the price path.
- **No options data.** Kills all 56 option strategies, implied-volatility signals, and the variance
  risk premium.
- **No microstructure.** Kills market making and all execution alpha. K&S are explicit that this is an
  infrastructure-and-speed game.
- **No capital.** $1,000 against a $3,810 single-share basket. Requires fractional shares to exist at
  all, and cannot absorb per-trade minimum commissions at any meaningful rebalance frequency. **This
  is the constraint most likely to be underestimated**, because the backtest was validated at
  $1,000,000 notional.

The honest summary: **the surviving families are all variations on "size the same long book better",
not "find a better cross-section".** That is a real but narrow space. It contains genuine, published,
peer-reviewed effects (#1 and #3 especially) — but nothing in it is likely to produce a high Sharpe
from 15 large-cap names on daily bars, and the roadmap should not be built on the expectation that it
will.

---

## 6. Source list and access honesty

| Source | Type | What I actually read |
|---|---|---|
| Kakushadze & Serur, *151 Estrategias de Trading*, [arXiv 1912.04492](https://arxiv.org/abs/1912.04492) (Spanish ed.) | Primary, operator-supplied | **Full text** of ch. 3 (equities), ch. 4 (ETFs), §6.5, plus complete TOC — extracted via `pdftotext -layout` from the operator's local PDF |
| Moreira & Muir, "Volatility-Managed Portfolios," *Journal of Finance* 72(4), 1611–1644 (2017) | Peer-reviewed | **Full text**, [author-hosted PDF](https://amoreira2.github.io/alan-moreira.github.io/VolPortfolios_published.pdf) — construction eq. 1–2, headline alphas, Table III, §III.B transaction costs |
| Moskowitz, Ooi & Pedersen, "Time Series Momentum," *JFE* 104(2), 228–250 (2012) | Peer-reviewed | **Full text**, [NYU Stern author copy](https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf) — 58-futures scope, 40%/σ sizing, Sharpe claims |
| Antonacci, "Risk Premia Harvesting Through Dual Momentum," NAAIM Founders Award 2012 / *J. Mgmt & Entrepreneurship* 2(1) 27–55 (2017) | Practitioner, peer-reviewed version exists | **Full text**, [SSRN 2042750 mirror](https://www.trendfollowing.com/whitepaper/SSRN-id2042750.pdf) — absolute-momentum definition, Table 11 composite, conclusions |
| López de Prado, "The 10 Reasons Most Machine Learning Funds Fail" | Primary author whitepaper | **Full text**, [GARP PDF](https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf) — Pitfalls #3, #4, #9, #10; DSR and PSR formulas |
| Bailey, Borwein, López de Prado & Zhu, "Pseudo-Mathematics and Financial Charlatanism," *Notices of the AMS* 61(5), 458–471 (2014) | Peer-reviewed | **Abstract only — ams.org returned HTTP 403.** Cited via the GARP whitepaper's restatement of its expected-maximum-Sharpe proof, not from the paper itself |
| Yang & Zhang, "Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices," *Journal of Business* 73(3), 477–492 (2000) | Peer-reviewed | **Published abstract and stated estimator properties only** — full text paywalled (JSTOR/SSRN). No efficiency multiple quoted |
| Bernut, *Algorithmic Short Selling with Python* (Packt, 2021) | Practitioner book | **Publisher description / TOC only — full text not accessed.** Cited as a methodology pointer, not as evidence |
| Jansen, *Machine Learning for Algorithmic Trading* — [companion repo](https://github.com/stefan-jansen/machine-learning-for-trading) | Practitioner book + code | **Repo chapter listing** — used only to map which chapters need alternative data vs. daily OHLCV |
| cantaro86, [Financial-Models-Numerical-Methods](https://github.com/cantaro86/Financial-Models-Numerical-Methods) | Code repository | **Repo TOC.** Assessed and largely *not* applicable: it is an option-pricing/SDE library (Heston, Lévy, PIDE). Its relevant pieces are §5.1–5.3 (Kalman filtering, volatility tracking), §6.1 (Ornstein-Uhlenbeck) and §7.1 (classical MVO). It contains no equity strategy backtesting and no regime-switching models |
| QAPF repository | Primary — this project | `agents/alpha/factors.py`, `agents/alpha/combiner.py`, `agents/backtest/walkforward.py`, `agents/portfolio/allocator.py`, `agents/stats/toolkit.py`, `dashboard/export.py`, `frontend/data/snapshot.json`, `reference/qlib/.../optimizer.py` |
| Daniel & Moskowitz (2016); Cooper, Gutierrez & Hameed (2004); and the regime-timing literature | Peer-reviewed | Not re-derived here — see the sibling note [`regime-factor-evidence.md`](regime-factor-evidence.md), which covers them in depth |

**Explicitly excluded:** trading blogs, strategy-marketing sites, and the several secondary summaries of
López de Prado's work that surfaced in search. Where a practitioner source is cited (Antonacci, Bernut),
it is flagged as such.

---

## 7. Recommended next action

The single cheapest decisive experiment is **not** building any of the five. It is re-running the
*existing* backtest at $1,000 notional with the existing `min_cost: 5` cost model (§1.1). If the
current strategy's 27.5% return becomes deeply negative purely from transaction costs — which the
arithmetic says it will — then the binding constraint on this project is capital, not alpha, and the
entire shortlist above is premature. That test costs one config change and one backtest run.

After that, in order: #2 (enabler, ~1 hour), #1 applied as post-processing to the existing return
series (~1 hour), #4 as the new benchmark, then #3. Leave #5 until something has demonstrated edge.

---

*Written 2026-08-19. Verdicts in §2 are judgements against the constraints as stated, not empirical
results — every "RULED IN" is a hypothesis to be tested at an honest DSR trial count (§0.2), not a
finding. The two premise corrections in §0 should be confirmed with the operator before this document
is used to steer the roadmap.*

# Data and Modelling Tooling: OpenBB, TabPFN, QuantPad

**Question set.** Three tools have been proposed against three open decisions in QAPF:

1. **OpenBB** — can it fix the stale-data ticket (Qlib's bundled calendar stops at 2020-11-10) and the
   survivorship-bias ticket (the 15-ticker universe was hand-picked in 2026 knowing who won)?
2. **TabPFN** — is a pre-trained tabular transformer a credible model for financial return prediction
   here, given that small-sample overfitting is exactly what is killing the strategy (DSR 0.414)?
3. **QuantPad** — is it relevant at all?

**Scope of sources.** Source code in the upstream repositories (read from `raw.githubusercontent.com`
at the `develop`/`main` HEAD on 2026-08-19), first-party documentation, vendor pricing pages, arXiv
and journal listings, and one live empirical test run in this repo's own venv. No blog posts, no
tutorial sites, no vendor comparison articles. Where a claim could only be sourced from a search-engine
summary rather than a document I could open, it is labelled **unverified**.

---

## Verdicts up front

| Tool | Verdict | One-line reason |
|---|---|---|
| **OpenBB** | **Reject** for the survivorship ticket; **reject** for the stale-data ticket | It has no delisted-securities data anywhere in the codebase, no date-parameterised constituents API, it sells no data of its own, and it is AGPL-3.0 — which would infect this repo's currently Apache-2.0/MIT licence position. |
| **TabPFN** | **Reject** (as a return predictor). Narrow **trial** allowed only for a non-return classification task. | The one peer-reviewed financial-return evaluation I found reports vanilla TabPFN at **negative** information ratio, and the default weights are **non-commercial-use-only** — fatal for something called a prop firm. |
| **QuantPad** | **Reject** | Hosted SaaS AI-IDE for retail/prop-challenge strategy coding, in DSLs this project does not use. It replaces the part of QAPF that already works and does not touch the part that is broken. |

**The finding that matters most:** the survivorship problem is solvable, cheaply, but **not by OpenBB**.
Qlib — already forked into this repo — ships a working point-in-time S&P 500 constituents collector
(`reference/qlib/scripts/data_collector/us_index/collector.py`), and Sharadar sells survivorship-free
delisted price history for **$9/month**. See §1.5.

---

## 1. OpenBB

### 1.1 What OpenBB actually is

OpenBB Platform is an **aggregation layer**, not a data vendor. Its own pricing page states the platform
includes only "a limited sandbox powered by Financial Modeling Prep" and that organisations must connect
their own datasets and bring their own provider API keys
([openbb.co/pricing](https://openbb.co/pricing)). The README describes it as a "connect once, consume
everywhere" infrastructure layer
([github.com/OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB)).

The repository at `develop` contains **33 provider extensions**
(`openbb_platform/providers/*`, enumerated from the GitHub tree API on 2026-08-19):

```
alpha_vantage, benzinga, biztoc, bls, cboe, cftc, congress_gov, deribit, ecb, econdb,
eia, famafrench, federal_reserve, finra, finviz, fmp, fred, government_us, imf, intrinio,
multpl, nasdaq, oecd, sec, seeking_alpha, stockgrid, tiingo, tmx, tradier,
tradingeconomics, wsj, yfinance
```

Keyed vs keyless, read from each provider's `__init__.py` `credentials=` field:

| Needs an API key | Keyless (`credentials=None` or absent) |
|---|---|
| `fmp`, `fred`, `nasdaq`, `intrinio`, `tiingo` (token), `alpha_vantage`, `econdb` (optional temp token) | `cboe`, `sec`, `yfinance`, `tmx`, `famafrench`, `finviz`, `stockgrid`, `wsj`, `federal_reserve` |

Note there is **no Polygon provider** and **no Sharadar provider** in the tree — so OpenBB is not even a
route to the two vendors that would actually help (§1.5).

### 1.2 Historical index constituents — partial, and only behind a paid key

There is exactly one constituents endpoint,
[`openbb_platform/extensions/index/openbb_index/index_router.py`](https://github.com/OpenBB-finance/OpenBB/blob/develop/openbb_platform/extensions/index/openbb_index/index_router.py),
`index.constituents`. The **standard query model takes only `symbol`** — no `date`, no `as_of`:

```python
class IndexConstituentsQueryParams(QueryParams):
    """Index Constituents Query."""
    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
```
(`openbb_platform/core/openbb_core/provider/standard_models/index_constituents.py`)

Only three providers implement it:

- **`cboe`** — free, but the symbol enum is European indices only (`BAT20P`, `BDE40P`, `BEP50P`,
  `BUK100P` …). Current snapshot, no history.
  (`openbb_platform/providers/cboe/openbb_cboe/models/index_constituents.py`)
- **`tmx`** — Canadian indices.
- **`fmp`** — the only US route, and it needs `fmp_api_key`.

The FMP model is the only one with anything historical:

```python
symbol: Literal["dowjones", "sp500", "nasdaq"] = Field(default="dowjones")
historical: bool = Field(default=False,
    description="Flag to retrieve historical removals and additions.")
...
url = f"{base_url}/{'historical-' if query.historical else ''}{query.symbol}-constituent/?apikey={api_key}"
```
(`openbb_platform/providers/fmp/openbb_fmp/models/index_constituents.py`)

So what you get is a **change log** — `date`, `added_security`, `removed_symbol`, `removed_name`,
`reason` — not a point-in-time membership snapshot. You would still have to write the reconstruction
logic yourself (roll the current list backwards through the change log). That is real raw material, but
OpenBB is contributing an HTTP wrapper around one FMP endpoint, nothing more.

### 1.3 Delisted securities — **OpenBB has none. Anywhere.**

I pulled the full recursive git tree of `OpenBB-finance/OpenBB@develop` (2,710 paths, untruncated) and
searched every path for `delist`, `survivor`, `point_in_time`. **Zero matches.** The only related hits
are `index_constituents` (3 providers, above) and `historical_market_cap` (fmp/intrinio). The
`equity_router.py` surface is `EquitySearch`, `EquityScreener`, `EquityInfo`, `MarketSnapshots`,
`HistoricalMarketCap` — all current-universe.

**Blunt statement, since it is the single most useful thing here: OpenBB does not solve the
survivorship-bias problem.** It cannot give you a price series for a company that no longer trades.
Even with a paid FMP key, the best it offers is the list of names that left the index — and a list of
names you cannot get prices for does not let you backtest them.

I confirmed the price side of that empirically. Run in this repo's own `.venv` on 2026-08-19, using the
`yfinance` the project already depends on:

```
TWTR 0 rows | ATVI 0 rows | FRC 0 rows | SIVBQ 0 rows | CERN 0 rows | ENRNQ 0 rows
("possibly delisted; no timezone found" / "no price data found")
```

Six delisted names, 2015–2023 window, **zero rows each**. This is the actual bottleneck, and no free
source in or out of OpenBB fixes it.

### 1.4 The licence problem

`OpenBB-finance/OpenBB/LICENSE` reads: *"All files in this repository are licensed under the GNU Affero
General Public License v3.0."* (Copyright 2021-2025 OpenBB Inc.)

QAPF currently sits on Apache-2.0 (TradingAgents) and MIT (Qlib), and CLAUDE.md carries an explicit
"respect upstream licenses" ground rule. AGPL-3.0 has a **network-use clause**: §13 obliges you to offer
corresponding source to users interacting with the software over a network. QAPF's roadmap has a
FastAPI + Next.js surface. Importing `openbb` into `backend/` is therefore not a neutral dependency
decision — it is a licence-posture decision that should not be made incidentally to solving a data bug.
(I am reporting the licence text, not giving legal advice.)

### 1.5 What would actually solve the two tickets

**Ticket A — data stops at 2020-11-10.** This is a *Qlib bundle* problem, not a *data source* problem.
The project already pulls live yfinance data in six agents. The fix is to build a fresh Qlib bin bundle
from data you already have access to, using tooling already in the fork:

- `reference/qlib/scripts/dump_bin.py` — CSV/parquet → Qlib `.bin` bundle.
- `reference/qlib/scripts/data_collector/yahoo/` — a Yahoo collector.
- `reference/qlib/scripts/check_data_health.py` — bundle sanity check.

Cost: **$0**, roughly a day of work. OpenBB adds nothing here.

**Ticket B — survivorship bias.** Two halves, and they need different fixes.

*Half one — the membership list.* Qlib **already ships a point-in-time S&P 500 constituents builder**.
`reference/qlib/scripts/data_collector/us_index/collector.py` defines `SP500Index(WIKIIndex)`, which
scrapes the Wikipedia S&P 500 changes table and, via `IndexBase.parse_instruments()`
(`reference/qlib/scripts/data_collector/index.py`), emits a Qlib instruments file with columns
`[symbol, start_date, end_date]` — literally the PIT membership file Qlib's backtester consumes.
`bench_start_date` is `1999-01-01`.

Two gotchas worth flagging under this repo's verify-before-trusting rule:
- `get_changes()` does `pd.read_html(...)[-1]` — it takes the **last** table on the Wikipedia page and
  then `iloc[:, [0, 1, 3]]`. Both are positional assumptions about a page anyone can edit. Verify the
  parsed frame before trusting the output.
- It reconstructs history by rolling the *current* list backwards, so its accuracy is bounded by
  Wikipedia's completeness for removals.

A free, MIT-licensed cross-check exists: [`fja05680/sp500`](https://github.com/fja05680/sp500) —
"Current and Historical Lists of S&P 500 components since 1996", last pushed 2026-07-13, ships
`S&P 500 Historical Components & Changes (Updated).csv` and `sp500_ticker_start_end.csv`. Use it to
validate whatever the Qlib collector produces. Cost: **$0**.

*Half two — prices for the delisted names.* This is the part that costs money, and the cheapest verified
option by a wide margin is **Sharadar**:

- SEP (equity prices) covers "21,000 tickers" of active **and delisted** US stocks back to **January
  1998** ([sharadar.com/prices](https://sharadar.com/prices)). Sharadar's site claims coverage is
  "point-in-time ready, and nearly completely free of survivorship bias" ([sharadar.com](https://sharadar.com/)).
- An `sp500` constituents table and a `tickers` metadata table are separate tables in the same Prices
  bundle ([sharadar.com/prices](https://sharadar.com/prices)).
- Pricing ([sharadar.com/subscribe](https://sharadar.com/subscribe)): **Prices $9/mo**,
  Fundamentals $19/mo, Investors $19/mo, **all-tables Bundle $29/mo**. There is a free tier covering the
  30 DJIA companies — enough to write and test the ingestion path before paying anything.

Comparison of the alternatives I checked:

| Option | Delisted prices | Historical constituents | Cost | Blocker |
|---|---|---|---|---|
| **Sharadar Prices** | Yes, from 1998 | Yes (`sp500` table) | **$9/mo** | None found. Free DJIA-30 tier to trial. |
| **Norgate Data Platinum** | Yes | Yes | $630/yr (12mo) or $346.50/6mo ([stockmarketpackages.php](https://norgatedata.com/stockmarketpackages.php)) | **Windows-only.** The `norgatedata` PyPI package lists "Microsoft Windows 10/11 or … Server" as a hard requirement and states "The 'Norgate Data Updater' application (NDU) is a Windows-only application" ([PyPI norgatedata 1.0.77](https://pypi.org/project/norgatedata/)). This project runs on macOS. |
| **Massive (ex-Polygon)** | Not stated on the pricing page | No | Free (2y, 5 calls/min) / $29 / $79 / $199 per month ([massive.com/pricing](https://massive.com/pricing)) | Delisted coverage not documented on the pricing page — would need verification before purchase. |
| **FMP via OpenBB** | **No** | Change log only | Free tier 250 req/day, 500MB/30d bandwidth ([FMP pricing](https://site.financialmodelingprep.com/pricing-plans)) — historical constituent depth on paid tiers, exact tier **unverified** (pricing page returns 403 to automated fetch) | Solves nothing on its own; see §1.3. |
| **OpenBB itself** | **No** | Wrapper over the above | Platform free (AGPL-3.0); Workspace Lite $1,200/yr, Snowflake $500/seat/yr ([openbb.co/pricing](https://openbb.co/pricing)) | Sells no data; adds AGPL. |

### 1.6 OpenBB verdict — **Reject**

Not because it is a bad project — it is a competent aggregation layer with a clean provider abstraction.
Reject because, against *these two tickets specifically*:

1. It has zero delisted-securities coverage, so it cannot fix survivorship bias (§1.3, verified against
   the full repo tree).
2. Its only historical-constituents path is a paid FMP key returning a change log you must reconstruct
   yourself — and Qlib, already in this repo, does that reconstruction for free (§1.5).
3. It supplies no data of its own, so it cannot fix the stale-2020 bundle either; that is a `dump_bin.py`
   job.
4. It is AGPL-3.0, which is a licence-posture change this project has not decided to make.

Cost of adopting it anyway: roughly a day of integration, plus an FMP subscription of unverified tier,
plus an AGPL dependency, in exchange for a change log. Cost of the alternative in §1.5: $0 for the
membership half (Qlib collector, already present) and $9/month for the delisted-price half.

---

## 2. TabPFN

### 2.1 What it is, current as of 2026-08-19

TabPFN is a transformer pre-trained on synthetic tabular datasets that performs supervised learning as
in-context learning in a single forward pass — no gradient training, no hyperparameter tuning. Interface
is scikit-learn-shaped: `TabPFNClassifier` / `TabPFNRegressor`, `fit()` then `predict()`
([PriorLabs/TabPFN README](https://github.com/PriorLabs/TabPFN)).

**Both classification and regression are supported**, in every current checkpoint.

The project has moved well past the Nature 2025 paper. Current lineage
([docs.priorlabs.ai/models](https://docs.priorlabs.ai/models)):

| Model | Licence | Max rows | Max features | Max classes | Regression |
|---|---|---|---|---|---|
| TabPFN-3-Plus | TABPFN-3 License v1.0 | 1M | 200 | 160 | Yes |
| **TabPFN-3** (OSS default) | TABPFN-3 License v1.0 | 1M | 200 | 160 | Yes |
| TabPFN-2.6 | TABPFN-2.6 License v1.0 | 100K | 2K | 10 | Yes |
| TabPFNv2 | Prior Labs License (Apache-2.0 + attribution) | 10K | 500 | 10 | Yes |

TabPFN-3 trades rows against features: **1M×200, 100K×2K, or 1K×20K** (README, "Mind the dataset size").
`ignore_pretraining_limits=True` pushes past the guardrail.

Papers: [Hollmann et al., *Nature* 2025](https://www.nature.com/articles/s41586-024-08328-6)
(doi:10.1038/s41586-024-08328-6) for v2; [TabPFN-2.5 report, arXiv:2511.08667](https://arxiv.org/abs/2511.08667);
[TabPFN-3 Technical Report, arXiv:2605.13986](https://arxiv.org/abs/2605.13986).

### 2.2 The licence kills it before the statistics do

**The default weights are non-commercial-use-only.** From the README: "The TabPFN-2.5, TabPFN-2.6, and
TabPFN-3 model weights are released under non-commercial licenses … TabPFN-3 is used by default."

The [TABPFN-3 licence on Hugging Face](https://huggingface.co/Prior-Labs/tabpfn_3/blob/main/LICENSE)
permits use only for "testing, evaluation, or research not tied to commercial gain, production
deployment, or revenue generation." It explicitly prohibits commercial or production deployment, hosted
/ SaaS provision (paid **or free**), and restricts **outputs** to non-commercial purposes. It terminates
automatically on breach.

For a project whose stated purpose is an autonomous prop firm trading real capital, "outputs may only be
used for non-commercial purposes" is disqualifying on its face. Trading signals produced by the model
would be outputs used for revenue generation.

Only **TabPFNv2** (Prior Labs License = Apache-2.0 + attribution) is commercially usable — and that is
the **10K rows × 500 features × 10 classes** checkpoint, i.e. the weakest one. You must opt in explicitly:

```python
TabPFNRegressor.create_default_for_version(ModelVersion.V2)
```

Also note: first use of the 2.5/2.6/3 checkpoints **opens a browser for licence acceptance** and caches a
`TABPFN_TOKEN`. That is a network-dependent, interactive step inside what is meant to be a local-first
automated pipeline.

### 2.3 Published evidence on financial returns — thin, and what exists is negative

Prior Labs maintains its own curated evidence list,
[`PriorLabs/awesome-tabpfn`](https://github.com/PriorLabs/awesome-tabpfn). Its "Financial Services,
Banking, and Insurance" section has **9 entries**. Reading them as the vendor's own best case:

| # | What it actually is |
|---|---|
| 1, 2 | Transaction analytics / **churn prediction** (arXiv:2603.15459, arXiv:2501.10677v2) |
| 3 | Crypto **rug-pull detection** (arXiv:2603.11324) |
| 4 | A **GitHub hobby repo**, `zx20030501/sp500-market-prediction-tabpfn` — not peer-reviewed |
| 5 | **FinPFN** — a *fine-tuned* variant, see below |
| 6 | AutoML benchmark on financial **classification** (ACIS 2025) |
| 7, 8 | Insurance premiums, health-insurance cross-sell |
| 9 | Corporate bond **recovery rate** (a GitHub repo) |

**Not one of these nine is a peer-reviewed demonstration of vanilla TabPFN predicting equity returns.**
Eight are cross-sectional classification problems on genuinely i.i.d.-ish customer/transaction data —
exactly the regime TabPFN was built for. The ninth is FinPFN, and FinPFN is the damning one.

**Entry 5 — Wang & Lera, "Meta-learning for return prediction in shifting market regimes,"
*Journal of Financial Markets*, 2026**
([ScienceDirect S1386418125000825](https://www.sciencedirect.com/science/article/abs/pii/S1386418125000825) ·
[RePEc listing](https://ideas.repec.org/a/eee/finmar/v79y2026ics1386418125000825.html)). The abstract I
could open confirms: the authors found it necessary to build a **domain-specific, fine-tuned** PFN
(FinPFN) precisely because market data is non-stationary and feature–return relationships evolve. The
existence of this paper is itself the finding: a research group that wanted to use a PFN on returns did
not use TabPFN off the shelf — they retrained the prior.

> ⚠️ **Unverified — do not cite this number without checking the paywalled full text.** A search-engine
> summary attributed to this paper an information ratio of **0.85 for FinPFN vs −0.44 for TabPFN** on
> CSI 500, and an annualised long-short Sharpe of 9.8 *before transaction costs*. I could not open the
> full text (ScienceDirect returns 403 to automated fetch) and the RePEc abstract does not mention
> TabPFN at all. If the −0.44 figure holds, vanilla TabPFN is *worse than nothing* on cross-sectional
> equity returns. And a pre-cost Sharpe of 9.8 is itself a red flag about the evaluation, not a
> selling point.

There is also a GitHub repo, `wangy8989/FinPFN` ("Financial Prior-Data Fitted Network (regression)"),
but it has **no README** (raw fetch returns 404), so I could not verify its contents.

### 2.4 Does the i.i.d. assumption survive contact with returns? No, and it is architectural

TabPFN's architecture applies attention across rows of the training set — that is what makes in-context
learning work, and it is why the model is (approximately) **permutation-invariant over rows**. Rows are
treated as exchangeable draws from one data-generating process. Financial returns violate this in three
independent ways:

- **Temporal ordering carries information** that a row-exchangeable model discards by construction.
- **Non-stationarity** — the mapping from features to returns changes across regimes. TabPFN has one
  in-context "training set"; it has no mechanism for weighting recent rows more heavily. (This is
  precisely the gap FinPFN was built to fill.)
- **Signal-to-noise** — TabPFN's synthetic prior is built around structured causal relationships. The
  monthly cross-sectional R² of realistic equity return prediction is order 0.5–1%. Nothing in the
  prior anticipates that regime.

Prior Labs does not address this. The [docs FAQ](https://docs.priorlabs.ai/faq) documents dataset size,
hardware, and reproducibility caveats, and says **nothing** about time series, distribution shift, or
i.i.d. assumptions. The [TabPFN-3 abstract](https://arxiv.org/abs/2605.13986) states no failure modes at
all — it is an achievement announcement.

The one place limitations *are* stated honestly is the time-series extension paper,
[TabPFN-TS (arXiv:2501.02945)](https://arxiv.org/abs/2501.02945), and the limitation it names is
directly relevant:

> TabPFN-TS "struggles in extrapolating trends, where the future target values lie outside the range
> observed in the conditioning set" — a consequence of TabPFN-v2's pretraining favouring interpolation
> over extrapolation. It is also ~30× slower at inference than comparable foundation models.

And note *how* TabPFN-TS handles time: it does **not** learn temporal dynamics. It featurises the
timestamp — a running index, eight sine/cosine calendar features, and FFT-derived seasonal features —
and then runs plain tabular regression. That works for seasonal demand and load forecasting. Daily
equity returns have no calendar seasonality worth the name. GIFT-Eval, where TabPFN-TS tops the
leaderboard, includes M4 economics/finance series, but the paper aggregates across all 97 tasks and
does not break out a finance domain — so **there is no published per-domain finance result to point at**.

### 2.5 What TabPFN would and would not fix here

The appeal is understandable: DSR 0.414 is a small-sample overfitting failure, and TabPFN promises good
small-data performance without tuning. But look at what is actually broken.

The DSR haircut in this project is driven by **trials** — 0.414 comes from deflating for 4 hand-set
factors (README:336). TabPFN does not reduce the trial count. It does not reduce the effective number of
strategy configurations searched. And it is not a small-*rows* problem in the sense TabPFN addresses:
15 tickers × ~750 days is ~11K rows, comfortably inside even TabPFNv2's 10K-ish range, but the
constraint is **independent observations of the regime**, and TabPFN has no notion of that.

Worse, TabPFN would make the current diagnosis harder. Agent 7's factors are four transparent, signed,
economically-motivated transforms. Replacing them with an opaque 11M-parameter forward pass, on a
strategy that already fails validation on a survivorship-biased 15-ticker universe with data ending in
2020, adds a second unexplained thing on top of the first. **The model is not the binding constraint —
the data is.** §1.5 costs $9/month and fixes the binding constraint.

### 2.6 TabPFN verdict — **Reject** as a return predictor

Reasoning, in priority order:

1. **Licence.** Default weights forbid commercial use *of the outputs*. A prop firm cannot ship this.
   The only commercially-licensed checkpoint (v2) is the weakest.
2. **No supporting evidence.** The vendor's own curated evidence list contains zero peer-reviewed
   demonstrations of vanilla TabPFN on equity returns; the one return-prediction paper it does cite
   found it necessary to retrain the prior.
3. **Architectural mismatch.** Row exchangeability, interpolation-biased prior, no recency weighting —
   each independently at odds with autocorrelated, non-stationary, low-SNR returns.
4. **Wrong target.** It does not address the trials-based DSR haircut, the survivorship bias, or the
   2020 data cliff — i.e. none of the three things actually failing.

Cost if adopted anyway: $0 in money (GPU optional; the README warns CPU/MPS is only feasible to ~5,000
samples for TabPFN-3), roughly 2–4 days of integration, plus an unresolved commercial-licence exposure
and a less interpretable pipeline.

**The one narrow trial I would allow.** If someone wants to spend half a day, the *defensible*
experiment is not return prediction. It is a **regime-classification** task — take Agent 6's macro
features, target the realised regime label, and compare `TabPFNClassifier` (v2 weights, for licence
safety) against the current deterministic growth×inflation rule under walk-forward evaluation. That is a
genuinely low-dimensional, low-row, quasi-i.i.d. classification problem — TabPFN's actual home turf —
and it does not put model output on the trading path. Ship it only if it beats the deterministic rule
out of sample, and log it as a trial in the DSR count.

---

## 3. QuantPad

Short section, as requested.

**What it is.** A **hosted SaaS** product marketed as "The AI IDE for quantitative trading" — an AI agent
that writes and backtests strategies alongside you, with cloud compute and market data bundled
([quantpad.ai](https://quantpad.ai/)). Not open source; the site mentions an open-source Pine script
runner on GitHub as a side project.

**What it offers.** Multi-DSL support (PineScript, NinjaScript, PowerLanguage, EasyLanguage), linting
and iterative code fixing, trade-log analysis, Monte Carlo simulation aimed explicitly at **prop firm
evaluation**, and community project sharing. Bundled data: 40+ futures markets, 8,000+ US equities,
options chains, FRED and SEC data. Coverage depth is uneven — futures OHLCV ~16 years, US equity tick
trades only 12 months.

**Pricing: unverified.** Subscription with refreshing usage allowances and "zero markup" pass-through
overages, but no dollar figures are published on the homepage, and `/pricing` returns only a sign-in
prompt to an automated fetch. I could not verify any price.

**Relevance.** Effectively none.

- It is a *strategy-authoring* tool in DSLs QAPF does not use (PineScript/NinjaScript/EasyLanguage are
  retail charting-platform languages; QAPF is Python + Qlib + LangGraph).
- Its Monte Carlo feature targets **prop firm challenge evaluation** — and this repo already closed
  wayfinder ticket 04 concluding prop funding is industry-wide incompatible with this strategy
  (commit `49bd5ac`).
- It duplicates what QAPF *already has working* — an agentic pipeline and a backtester — and duplicates
  it as a closed, hosted service, which conflicts with the local-first premise in CLAUDE.md.
- It does nothing for delisted securities, point-in-time universes, or the 2020 data cliff. Its equity
  history (12 months of tick, unspecified daily depth) is shallower than what yfinance already gives
  this project for free.

**Verdict: Reject.** Cost of evaluating: an unknown subscription plus a day. Expected gain against the
three open tickets: zero.

---

## 4. Recommended next actions (none of which involve the three tools)

Ordered by value per unit of effort:

1. **Build a fresh Qlib bundle** with `reference/qlib/scripts/dump_bin.py` from live data, and verify it
   with `check_data_health.py`. Kills the 2020-11-10 cliff. **$0, ~1 day.**
2. **Generate a point-in-time S&P 500 instruments file** with
   `reference/qlib/scripts/data_collector/us_index/collector.py` (`parse_instruments`), cross-checking
   the output against [`fja05680/sp500`](https://github.com/fja05680/sp500). Verify the
   `pd.read_html(...)[-1]` / `iloc[:, [0,1,3]]` parsing before trusting it. **$0, ~1 day.** Gives you an
   honest universe *list*.
3. **Trial Sharadar's free DJIA-30 tier** to write and test the delisted-price ingestion path, then
   decide whether $9/month for full SEP coverage back to 1998 is worth it. It is the only verified
   option that is both survivorship-free and macOS-compatible. **$0 to trial, $9/mo to adopt.**
4. Only after 1–3: re-run Agent 9's walk-forward on a real point-in-time universe covering 2021–2024,
   and see what the DSR actually is. Any modelling change made before that is being tuned against a
   known-biased sample.

---

## Source table

| Source | Type | What I could read |
|---|---|---|
| [OpenBB-finance/OpenBB @ develop](https://github.com/OpenBB-finance/OpenBB) | Primary source code | Full recursive tree (2,710 paths), `index_router.py`, `equity_router.py`, standard + fmp + cboe constituents models, all provider `__init__.py` credentials, `LICENSE` |
| [openbb.co/pricing](https://openbb.co/pricing) | First-party pricing | Full page |
| [site.financialmodelingprep.com/pricing-plans](https://site.financialmodelingprep.com/pricing-plans) | Vendor pricing | **Search summary only — 403 to direct fetch.** Free tier 250 req/day, 500MB/30d; historical-constituent tier requirement **unverified** |
| [PriorLabs/TabPFN README](https://github.com/PriorLabs/TabPFN) | Primary source | Full |
| [docs.priorlabs.ai/models](https://docs.priorlabs.ai/models) | First-party docs | Full model/limit/licence table |
| [docs.priorlabs.ai/faq](https://docs.priorlabs.ai/faq) | First-party docs | Full |
| [TABPFN-3 licence (Hugging Face)](https://huggingface.co/Prior-Labs/tabpfn_3/blob/main/LICENSE) | Primary licence text | Full |
| [PriorLabs/awesome-tabpfn](https://github.com/PriorLabs/awesome-tabpfn) | Vendor evidence list | Full finance section (9 entries) |
| [Hollmann et al., *Nature* 2025, doi:10.1038/s41586-024-08328-6](https://www.nature.com/articles/s41586-024-08328-6) | Peer-reviewed | **Paywalled — could not open.** Cited from the README's own BibTeX only |
| [TabPFN-3 Technical Report, arXiv:2605.13986](https://arxiv.org/abs/2605.13986) | Preprint | Abstract |
| [TabPFN-TS, arXiv:2501.02945](https://arxiv.org/abs/2501.02945) (v4 HTML) | Preprint | Abstract + limitations + featurisation |
| [Wang & Lera, *J. Financial Markets* 2026](https://www.sciencedirect.com/science/article/abs/pii/S1386418125000825) | Peer-reviewed | **Paywalled.** RePEc abstract only; TabPFN baseline numbers **unverified** |
| [quantpad.ai](https://quantpad.ai/) | First-party marketing | Homepage; **pricing page not accessible** |
| [sharadar.com/prices](https://sharadar.com/prices), [/subscribe](https://sharadar.com/subscribe), [sharadar.com](https://sharadar.com/) | Vendor first-party | Coverage, tables, prices |
| [norgatedata.com/stockmarketpackages.php](https://norgatedata.com/stockmarketpackages.php) + [PyPI norgatedata](https://pypi.org/project/norgatedata/) | Vendor first-party | Package tiers/prices; Windows-only requirement |
| [massive.com/pricing](https://massive.com/pricing) (ex-polygon.io) | Vendor first-party | Tiers/prices; delisted coverage not stated |
| [fja05680/sp500](https://github.com/fja05680/sp500) | Primary repo (MIT) | Metadata + file listing |
| `reference/qlib/scripts/` (this repo) | Primary source code | `dump_bin.py`, `data_collector/index.py`, `data_collector/us_index/collector.py` |
| Local `yfinance` delisted-ticker test | Empirical, run in this repo's `.venv` | 6/6 delisted tickers returned 0 rows |

**Explicitly excluded:** blog posts, tutorial sites, vendor comparison articles, Medium/Substack
write-ups, and YouTube. Where only a search-engine summary was available (FMP tier requirements, the
FinPFN-vs-TabPFN IR figures), it is labelled unverified inline and must be re-checked before any
decision rests on it.

---

*Written 2026-08-19. The three verdicts (reject / reject / reject) rest on facts read from source code,
licence text, and vendor pricing pages, not on judgement calls — with the single exception of the
narrow TabPFN regime-classification trial in §2.6, which is a judgement call and is flagged as one.*

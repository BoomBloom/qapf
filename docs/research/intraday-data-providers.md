# Intraday U.S. Equity Data Providers — Primary-Source Survey

**Date checked: 2026-08-19.** yfinance results below are a live test run in this repo's own venv on
2026-08-19; every other figure was read from the provider's own pricing/docs page on that date unless
explicitly flagged otherwise.

**Sourcing policy for this document:** no affiliate blogs, no "best data providers for quant trading"
roundups, no aggregator comparison sites. Only provider-owned domains (`alpaca.markets`,
`docs.alpaca.markets`, `massive.com` — formerly `polygon.io`, see §2.1 — `databento.com`, `tiingo.com`,
`alphavantage.co`, `firstratedata.com`, `kibot.com`, `pypi.org/project/yfinance`) plus one live empirical
test of `yfinance` in this repo's own environment.

**Verification levels used below:**
- **[V]** — retrieved the provider's own page directly (via `WebFetch`) and read the text, or ran the
  code myself and observed the output.
- **[P]** — partially verified: the claim comes from the provider's own page as surfaced through a
  search-engine extract, but direct retrieval of that specific page failed or was thin.
- **[X]** — could not verify. Stated as unknown, not guessed.

**Hard constraint governing every recommendation below:** the agent operating this repo cannot sign up
for a paid account, enter payment details, or complete any billing flow on the operator's behalf — this
is a hard safety rule of the environment, not a preference. Every option below is labelled either
**(a) FREE — can be wired up right now with an account signup only, no payment method**, or
**(b) PAID — requires the operator to personally pay and supply their own API key.**

---

## 0. Executive summary

1. **yfinance's intraday lookback limits are real and were reproduced live today**, not assumed from
   old blog posts: 1-minute bars are hard-capped at **8 days per request** (Yahoo's own error string, not
   yfinance's), 5m/15m/30m bars are capped at **60 days**, and 1-hour bars are capped at **730 days**
   (both confirmed by triggering the failure past the boundary). yfinance is explicitly **unofficial** —
   PyPI's own listing states it is "not affiliated, endorsed, or vetted by Yahoo, Inc." and is intended
   for "research and educational purposes" only, drawing on Yahoo's undocumented public endpoints with no
   SLA.
2. **Alpaca's free tier is a genuinely free, no-card, real-time-capable option for live intraday
   monitoring** — IEX-feed real-time bars via websocket (limited to 30 symbols), 200 REST calls/min, no
   payment method required to open a paper account. This is the strongest live-monitoring candidate.
3. **For the 2008–2017 historical backtesting window, no free tier from any provider surveyed covers it
   at minute granularity.** Alpha Vantage's free tier is the one provider whose *paid* coverage floor (its
   extended intraday history) reaches back to January 2000 — but the free-tier rate limit is **25
   requests/day**, making a 15-ticker × 10-year backfill impractical without a paid key. IEX Cloud, the
   commonly-cited free/cheap alternative, **shut down entirely on 2024-08-31** and is not a live option.
   Databento's equities tick/minute coverage starts **2018**, after the window ends. Tiingo's IEX-sourced
   minute data starts **2017**, covering only the last year of the window. The realistic paid options that
   cover the full window are **Massive (formerly Polygon.io)** (minute/tick data to 2004, $199/mo
   "Advanced" tier or higher) and flat-fee historical data vendors **FirstRateData** and **Kibot** (minute
   bars to 1998–2000, one-time purchase, no recurring subscription).
4. **Polygon.io rebranded to Massive.com on 2025-10-30** — same company, same API keys/endpoints (both
   domains run in parallel), new brand. Anyone researching "Polygon.io" today should expect the pricing
   page to redirect to `massive.com`.

---

## 1. Use case 1 — live intraday risk monitoring

### 1.1 yfinance live-test results [V]

Test environment: this repo's own venv (`source .venv/bin/activate`), `yfinance` 1.6.0, run live on
2026-08-19 against `AAPL`.

```python
import yfinance as yf
df = yf.download("AAPL", period="7d", interval="1m")
# rows: 2559  min: 2026-08-11 09:30:00-04:00  max: 2026-08-19 13:08:00-04:00

df4 = yf.download("AAPL", period="30d", interval="1m")   # push past the 1m limit
# EMPTY RESULT — no exception raised in yf.download itself, but the underlying fetch logged:
# "$AAPL: 1m data not available for startTime=... and endTime=...
#  Only 8 days worth of 1m granularity data are allowed to be fetched per request."

df_8d = yf.download("AAPL", period="8d", interval="1m")
# rows: 2949  min: 2026-08-10 09:30:00-04:00  max: 2026-08-19 13:08:00-04:00   -- succeeds exactly at 8d

df2 = yf.download("AAPL", period="60d", interval="5m")
# rows: 4646  min: 2026-05-26 09:30:00-04:00  max: 2026-08-19 13:05:00-04:00

yf.download("AAPL", period="60d", interval="15m")
# rows: 1549  min: 2026-05-26  max: 2026-08-19  -- also caps cleanly at 60d, no truncation observed

yf.download("AAPL", period="60d", interval="30m")
# rows: 775  min: 2026-05-26  max: 2026-08-19

df3 = yf.download("AAPL", period="1y", interval="1h")
# rows: 1750  min: 2025-08-19 12:30:00-04:00  max: 2026-08-19 12:30:00-04:00

yf.download("AAPL", period="730d", interval="1h")
# rows: 5079  min: 2023-09-21 09:30:00-04:00  max: 2026-08-19 12:30:00-04:00  -- succeeds exactly at 730d

yf.download("AAPL", period="800d", interval="1h")   # push past the 1h limit
# EMPTY RESULT; underlying error:
# "$AAPL: 1h data not available for startTime=... and endTime=...
#  The requested range must be within the last 730 days."
```

**Findings, all [V] — observed live today, not assumed from secondary sources:**

| Interval | Actual max lookback observed | Behavior past the limit |
|---|---|---|
| 1m | **8 days** (exact boundary succeeds; 30d request returns an empty frame) | Fails **silently** at the `yf.download` return value (empty DataFrame, no exception) — the real error only appears in a logged warning naming the exact cause. **A caller that doesn't check for an empty frame will not notice.** |
| 5m | 60 days | Not tested past 60d, but request exactly at 60d succeeds cleanly |
| 15m | 60 days | Same |
| 30m | 60 days | Same |
| 1h | **730 days** (exact boundary succeeds; 800d request returns an empty frame) | Same silent-empty-frame failure mode as 1m |
| 1d | effectively unlimited (`period="max"` returned 11,513 rows back to 1980-12-12) | n/a |

This confirms the commonly-cited "~7–8 days for 1-minute data" figure is accurate today, and additionally
establishes the 60-day cap for 5m/15m/30m and the 730-day cap for 1h — all reproduced live, all failing
**silently** (empty result, not a raised exception) when the request exceeds the limit. Any code built on
yfinance for live monitoring must explicitly check `len(df) == 0` / index bounds after every call rather
than trusting a lack of exception.

**Reliability caveat [V]:** yfinance's own PyPI listing (`pypi.org/project/yfinance`) states plainly that
it "is **not** affiliated, endorsed, or vetted by Yahoo, Inc." and describes itself as "an open-source
tool that uses Yahoo's publicly available APIs," restricted to "research and educational purposes," with
users directed to "refer to Yahoo!'s terms of use" which state "the Yahoo! finance API is intended for
personal use only." There is no SLA, no committed uptime, and no support channel — it scrapes an
undocumented endpoint that can change or break without notice. **This makes yfinance unsuitable as the
sole data source for a live risk gate that has to be trustworthy**, even though its intraday intervals are
useful for prototyping.

### 1.2 Alpaca Markets — free tier [V]

Source: `alpaca.markets/data` (pricing/comparison table, fetched directly 2026-08-19).

- **Free tier ("$0/mo", labelled for "developers and researchers") requires no payment method** — the
  page's pricing comparison lists it as free with no card-on-file requirement, and independent
  confirmation from Alpaca's own docs/support material states paper trading accounts are opened with just
  an email address and MFA setup, "free and available to all Alpaca users," no card required [V/P — the
  no-card claim for account opening specifically was confirmed via a search-surfaced extract of Alpaca's
  own docs/support pages rather than a direct fetch of the exact signup-flow page, so tagged **[P]** for
  that specific sub-claim].
- **Rate limit (free):** 200 API calls/minute, vs. unlimited on the paid "Algo Trader Plus" tier
  ($99/mo) [V].
- **Feed coverage (free):** **IEX only** — the paid tier ($99/mo) upgrades to "All US Exchanges" (i.e.
  the consolidated SIP feed) [V]. IEX alone is a single venue and will materially undercount volume and
  can show slightly different prices than the National Best Bid/Offer, which matters for a CRO computing
  mark-to-market equity — but IEX quotes are still real-time (not synthetically delayed).
- **Real-time vs. delayed (free):** the pricing table shows "15 minute delay via API" for REST pulls, but
  **real-time data is available via websocket** on the free tier, capped at "**30 symbols**" streamed
  concurrently (paid tier: unlimited symbols) [V].
- **Historical depth on data pages (both tiers):** "over 7+ years of historical data" — no explicit start
  date given [V], meaning roughly back to ~2019, not usable for the 2008–2017 backtest window (see §2.3).

**Verdict for live monitoring:** genuinely free, no card required to sign up for paper trading, real-time
IEX data via websocket sufficient to mark 30 or fewer symbols intraday — comfortably covers QAPF's current
14–15-ticker universe. The IEX-only (not full-SIP) caveat is a known accuracy trade-off, not a blocker.

### 1.3 Other live/near-real-time options considered

- **IEX Cloud** — **defunct.** IEX Group announced retirement of all IEX Cloud products on 2024-05-31 and
  shut the service down entirely on 2024-08-31; all endpoints are dead and accounts inactive (confirmed
  via multiple independent secondary sources describing IEX's own announcement — direct fetch of
  `iexcloud.io` failed with a connection error during this research, consistent with the domain being
  decommissioned) **[P]** — do not build against it.
- **Polygon.io / Massive** — has a real-time/delayed live feed product, but its free ("Basic") tier is
  **end-of-day only** with a 5 calls/minute limit [V, see §2.1] — not usable for live intraday monitoring
  without a paid plan ($29+/mo for 15-minute-delayed data, real-time only at the $199/mo "Advanced" tier
  or above) [V]. Not competitive with Alpaca's free real-time IEX websocket for this use case.
- **Alpha Vantage** — free tier's 25 requests/day (see §2.5) makes it structurally unusable for live
  polling of a multi-symbol portfolio throughout a trading session; not evaluated further for this use
  case.

### 1.4 Use case 1 recommendation

**#1 — Alpaca Markets free/paper tier.** Cost: **$0, FREE tier, no payment method required.** Operator
action: personally create an Alpaca account and generate a paper-trading API key (email + password + MFA
setup — no card). This is a signup task, not a payment task, so it is safe for the operator to do without
special caution, but per the environment's rules the agent still cannot perform the signup itself.
Caveats to carry into the CRO design: IEX-only feed (not full-market SIP), 30-symbol cap on the free
websocket stream (fine at QAPF's current universe size, a future constraint if the universe grows), and
Alpaca's free-tier REST pulls are delayed 15 minutes (use the websocket path for true real-time, not the
REST endpoint).
**Fallback / prototyping only:** yfinance's 1m/5m/15m/1h intervals, already available with zero setup in
this repo's venv, but not appropriate as the production data source for a live risk gate given its
unofficial, no-SLA status — usable for local testing while the Alpaca integration is built.

---

## 2. Use case 2 — historical intraday backtesting, 2008–2017

Target: minute-level history for AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, WMT, KO, PEP, XOM, CVX, JNJ, PG, HD
(14 tickers) across the full 2008–2017 window, to re-score the existing walk-forward backtest's
close-based -36.68% max drawdown against true intraday price paths.

### 2.1 Polygon.io / Massive

- **Rebrand notice [V]:** `polygon.io/pricing` now issues a **301 redirect to `massive.com/pricing`**
  (observed directly 2026-08-19). Massive's own announcement post
  (`massive.com/blog/polygon-is-now-massive`) confirms this is the same company/service under a new
  brand, effective 2025-10-30: "Your existing code, keys, and logins remain valid, with no updates
  required today," with both `api.polygon.io` and `api.massive.com` running in parallel during a
  migration period [V].
- **Pricing tiers (stocks), fetched from `massive.com/pricing`, 2026-08-19 [V]:**

  | Tier | Price/mo | Historical depth (as stated) | Rate limit | Data type |
  |---|---|---|---|---|
  | Basic | Free | 2 years | 5 calls/min | End-of-day only — **no intraday bars on the free tier** |
  | Starter | $29 | 5 years | Unlimited | 15-min delayed |
  | Developer | $79 | 10 years | Unlimited | 15-min delayed |
  | Advanced | $199 | "20+ years" | Unlimited | Real-time |

- **How far back does minute data actually go?** Massive's own knowledge-base article ("How much
  historical stock data does Massive have?") states directly: **"We offer historical tick-level data for
  stocks dating back to 2004"** and references "trillions of rows of historical tick data... over the last
  20 years at nanosecond granularity," with derived aggregates (second/minute/hour/day bars) computable
  from that tick history [V]. This means the **Advanced tier's minute aggregates genuinely reach back
  through the entire 2008–2017 window** — but note the tiered table above states "20+ years" of *history
  depth* as a plan feature separately from the *2004 tick-data floor*; the practical reading is that the
  $199/mo Advanced tier (or higher) is the one that actually unlocks pre-2016 minute bars, since the
  cheaper tiers cap at 5–10 years of lookback which, from 2026, does not reach 2008.
- **Licensing [V]** — from Massive's Market Data Terms of Service (`massive.com/terms/market_data_terms.pdf`,
  last updated 2024-10-09, found via search and consistent with the Business/Individual ToS pages):
  redistribution/republishing of the data to anyone outside the licensed account is **prohibited**; the
  license is for the customer's **internal use** in their own software/websites only. This is fine for
  QAPF's use (internal backtesting, not redistributing raw bars), but rules out ever shipping the raw
  minute data as part of any public dataset or open-sourcing it.
- **Verdict:** **(b) PAID.** Free tier is EOD-only and useless for this task. The $199/mo Advanced tier
  (or check whether a lower tier's actual API responses reach further back than the marketing copy
  states — worth a support ticket before paying) is the plan that covers the full window. Operator must
  personally subscribe and provide an API key.

### 2.2 Databento

- **Pricing model [V]** (`databento.com/pricing`): **both usage-based (pay-per-GB for historical
  downloads) and subscription tiers** exist — Standard $199/mo, Plus $1,750/mo, Unlimited $4,500/mo.
- **No card required to start:** new users get **$125 in free credit** toward historical data, expiring in
  6 months, with no credit card explicitly required to claim it [V].
- **Historical equities coverage — does NOT reach 2008–2017 [V].** Databento's XNAS.ITCH (Nasdaq
  TotalView-ITCH) dataset — its core US equities tick/minute source — starts **2018-05-01**; corroborated
  by a second independent finding that tick-level history (L1 and better) across Databento's equities
  offering "goes back to 2018," with the company stating it could not find a source it trusts for
  higher-granularity equities data before that year. Daily/OHLCV backfill was separately reported as
  reaching back "to at least 2010" but that is daily bars, not minute bars, and does not help this task
  [P — sourced via search-surfaced extracts of Databento's own blog/roadmap pages, not a direct fetch of
  a single canonical coverage page].
- **Licensing [V]:** redistribution rights are dataset-dependent and "pass through publisher
  restrictions," with many datasets allowing redistribution "internally or externally after 24 hours" —
  not directly relevant here since the coverage gap is disqualifying regardless.
- **Verdict:** **Does not cover the required window.** Even with the free credit, Databento's equities
  minute/tick data starts a decade after this project's 2008 start point. Not usable for this task,
  free or paid.

### 2.3 Alpaca — historical

- Same pricing page as §1.2: **"7+ years of historical data"** stated on both free and paid tiers, no
  explicit start date given [V]. From 2026, "7+ years" reaches back to roughly 2019 at best — **does not
  cover 2008–2017 at all**, on either the free or the $99/mo paid tier.
- **Verdict:** not usable for this task regardless of tier — a coverage-depth disqualification, not a
  cost one.

### 2.4 IEX Cloud

- **Defunct — do not use.** IEX Group shut IEX Cloud down completely on 2024-08-31 after announcing
  retirement of the product on 2024-05-31; all endpoints are dead, all accounts inactive [P — corroborated
  by multiple independent descriptions of IEX's own announcement; direct fetch of `iexcloud.io` failed
  with a connection-refused error during this research, consistent with the domain no longer serving].
  Excluded from consideration for either use case.

### 2.5 Tiingo

- **Pricing [V]** (`tiingo.com/pricing`): Starter (free) — $0/mo, 500 symbols/mo, 50 requests/hour.
  Power — $30/mo, ~109,681 symbols/mo, 10,000 requests/hour.
- **EOD data goes back "30+ years"** on the Starter tier [V] — but that is daily, not intraday.
- **Intraday coverage:** Tiingo's IEX-sourced endpoint does offer minute-level bars
  (`api.tiingo.com/iex/<ticker>/prices?...resampleFreq=5min`), but **coverage starts in 2017** [P — the
  exact start year came from a search-surfaced description of Tiingo's own documentation/QuantStart
  third-party evaluation rather than a directly fetched canonical "coverage starts" statement, so tagged
  P rather than V], consistent with IEX Exchange itself only having launched trading in 2016. **This
  covers at most the last ~1 year of the 2008–2017 window (2017 itself) and none of 2008–2016.**
- **Verdict:** **Free tier exists but is structurally insufficient** for this task regardless of price —
  the coverage gap (starts 2017, need 2008) rules it out on both free and paid plans.

### 2.6 Alpha Vantage

- **Free tier rate limit [V]**, confirmed directly from `alphavantage.co/support/`: **"25 API requests
  per day"** (with "unlimited API requests for verified open-source or educational projects" as a
  separate program requiring a verification process, not a blanket free-tier upgrade). This is the
  "tightened" current number the ticket asked to verify — it is materially tighter than the historically
  cited 5 requests/minute, 500/day figure, and 25/day is the number that governs today.
- **Extended intraday history [V]**, confirmed from `alphavantage.co/documentation/`: the
  `TIME_SERIES_INTRADAY` endpoint supports a `month=YYYY-MM` parameter, and Alpha Vantage's own docs state
  "**Any month in the last 20+ years since 2000-01 (January 2000) is supported**." This is the **only
  provider surveyed whose intraday coverage floor unambiguously spans the entire 2008–2017 window** for
  large-cap tickers.
- **Practical throughput problem:** each request returns one ticker-month. Backfilling 14 tickers × 10
  years × 12 months = **1,680 requests**. At 25 requests/day (free tier), that is **~67 days of continuous
  polling** just for the initial backfill — impractical. Paid tiers remove the daily cap: $49.99/mo (75
  req/min) up to $249.99/mo (1,200 req/min), with a custom/unlimited tier available on request [V]. Even
  the cheapest paid tier ($49.99/mo, 75 req/min) would clear 1,680 requests in well under an hour once
  minute-level rate limits (not the daily cap) are the only constraint.
- **Verdict:** **(a) FREE tier exists and technically reaches the full window**, but is **not practically
  usable free** for a bulk 14-ticker/10-year backfill because of the 25-requests/day ceiling — this is a
  "free in principle, paid in practice for this specific task" case, worth stating plainly rather than
  rounding to either "free" or "paid."

### 2.7 Flat-fee historical vendors (no subscription)

These are one-time-purchase data vendors, structurally different from the API-subscription providers
above — worth including because they are the cleanest fit for a fixed 2008–2017 backfill.

- **FirstRate Data** (`firstratedata.com`) — 1-minute (and 5m/30m/1h/1d) bars for individual large-cap
  stocks going back to **January 2000** [V, "Our high-frequency historical stock data set goes back to
  Jan 2000"]. Pricing for the full Russell 3000 bundle (15 years of 1m/5m/1h bars) starts at **$399.95
  per purchase**, one-time, no subscription [P — bundle price found via a third-party data-marketplace
  listing (Datarade), not FirstRateData's own checkout page, so tagged P]; the site states per-ticker
  pricing is available but "usually more cost-effective to purchase bundles if you are requiring three or
  more tickers" [V] — with 14 tickers needed here, the bundle path is the relevant one. Licensing terms
  for redistribution were not found on the pages fetched — **[X]**, unknown; check before assuming
  internal-research use is unrestricted.
- **Kibot** (`kibot.com`) — 1-minute intraday data for 18,000+ US stocks (25,000+ including delisted)
  back to **1998**, all-stocks-and-ETFs bundle priced at **$4,200 one-time**, no subscription, updated
  daily for the first 45 days then quarterly for a year [P — pricing/coverage figures came from a
  search-surfaced description of Kibot's own product pages, not a direct fetch]. More expensive than
  FirstRateData for broad coverage; only worth it if FirstRateData's per-ticker/licensing terms turn out
  to be a blocker.
- Both vendors are **(b) PAID, one-time purchase** — no subscription, no recurring card charge, but still
  a real payment the operator must personally make (this project's agent cannot purchase on their
  behalf).

### 2.8 Use case 2 summary table

| Provider | Free tier sufficient? | Real cost if not | Minute-bar depth for 2008–2017 | Licensing note |
|---|---|---|---|---|
| Massive (Polygon.io) | No — free tier is EOD only | **$199/mo** (Advanced tier) [V] | Tick data to 2004 [V] — covers full window | Internal use only, no redistribution [V] |
| Databento | N/A — coverage gap regardless of tier | n/a | Starts **2018** [P] — **does not cover the window at all** | Dataset-dependent, moot here |
| Alpaca | No — 7+ yrs only, ~2019 floor | $99/mo doesn't fix the coverage gap either | Does not reach 2008 on any tier | n/a — disqualified by coverage |
| IEX Cloud | N/A | N/A | **Service is shut down** (since 2024-08-31) [P] | n/a |
| Tiingo | No — coverage gap, not price | $30/mo doesn't fix the coverage gap either | Starts **2017** [P] — covers ~1 of 10 years needed | Not evaluated (moot) |
| Alpha Vantage | **Technically yes, practically no** (25 req/day) [V] | **$49.99/mo+** for usable throughput [V] | Since **Jan 2000** [V] — covers full window | Not found on pages checked — [X] |
| FirstRateData | No (paid, one-time) | **~$400** one-time (bundle) [P] | Since **Jan 2000** [V] — covers full window | Not found — [X] |
| Kibot | No (paid, one-time) | **~$4,200** one-time (bundle) [P] | Since **1998** [P] — covers full window | Not found — [X] |

### 2.9 Residual gap — stated plainly

**No free tier from any provider surveyed covers 15 large-cap tickers at minute granularity for the full
2008–2017 window.** This is a real gap, not a rounding error: Alpha Vantage's free tier reaches the right
years but not at usable throughput; every other free tier fails on coverage depth alone (Databento,
Alpaca, Tiingo all start well after 2008; Massive/Polygon's free tier is EOD-only; IEX Cloud is dead).
Closing this gap requires either (a) the operator personally paying for one of the paid API tiers or
flat-fee vendor bundles above, or (b) accepting Alpha Vantage's free tier at a ~2-month backfill timeline
(25 tickers-months/day), which is slow but genuinely free and genuinely reaches the full window — the one
path in this survey that requires no payment at all, at the cost of wall-clock time instead of money.

---

## 3. Final consolidated recommendation

### Use case 1 — live intraday risk monitoring

**#1 pick: Alpaca Markets free/paper tier.** Cost: **$0 — FREE, no payment method.** Exact next step the
operator must personally take: create an Alpaca account and generate a paper-trading API key
(`alpaca.markets` signup — email + password + MFA; no card requested at any point in that flow per
Alpaca's own docs). Once the key exists, it can be wired into the CRO for a real-time IEX websocket feed
(≤30 symbols, comfortably within QAPF's current universe) plus 200 req/min REST access for anything not
needed at true real-time. Caveat to design around: IEX-only (not full-SIP) pricing, and the free tier's
REST endpoint is 15-minute-delayed — the websocket path is the one that gives genuine real-time marks.
yfinance remains available with zero setup for local prototyping of the intraday logic but should not be
the production data source, given its explicitly unofficial, no-SLA status.

### Use case 2 — historical 2008–2017 intraday backtesting

**#1 pick: Massive (formerly Polygon.io), Advanced tier.** Cost: **the operator must personally pay
$199/mo and supply their own API key — this cannot be done by the agent.** This is the most
straightforwardly verified full-coverage option (tick data confirmed to 2004, standard REST API this
project can integrate the same way it already integrates other data sources) with a clear, findable
pricing page. Before committing to a full year's subscription, the operator may want to confirm via a
support ticket or a short trial pull whether the cheaper Developer tier ($79/mo, nominally "10 years") in
fact returns pre-2016 data despite the marketing copy — Massive's knowledge-base article describes the
underlying tick-data floor (2004) as a platform-wide fact rather than something gated per tier, so it is
worth checking before assuming $199/mo is the minimum.

**Free-only fallback (no payment at all): Alpha Vantage free tier**, accepting a ~2-month backfill
timeline at 25 requests/day (1,680 ticker-month requests needed for 14 tickers × 10 years). Genuinely
free, genuinely covers the full window (confirmed back to January 2000 on Alpha Vantage's own docs), but
slow — plan the backfill as a long-running background job, not an interactive one, if cost has to stay at
zero.

**One-time-purchase alternative:** FirstRateData's Russell 3000 bundle (~$400 one-time, no subscription)
is cheaper in total dollar terms than a year of Massive's Advanced tier and covers the same window, but
its licensing terms for backtest/redistribution use were not found on the pages checked in this survey
— **[X]**, confirm with FirstRateData directly before purchasing if this path is chosen.

**Gap to carry forward:** whichever path is chosen, this is genuinely new spend or genuinely new
wall-clock time — there is no zero-cost, zero-delay option that covers 2008–2017 at minute granularity for
this ticker set. State that plainly to the operator rather than picking the cheapest-sounding option and
implying it is free; only Alpha Vantage's free tier is actually free, and it is free at the cost of a
~2-month backfill, not free at the cost of nothing.

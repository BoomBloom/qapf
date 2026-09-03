# F1 — Cross-sectional equity factors and anomalies
Researched: 2026-08-27 | Researcher: subagent

**Environment note:** This session's egress proxy blocked essentially all direct fetches this
research would normally rely on — SSRN, NBER, Wiley/Oxford journal pages, Wikipedia, AQR, OSAM,
alphaarchitect.com, and even federalreserve.gov all returned `403` at the proxy/CONNECT layer, not
just the three domains the brief called out as blocked (arxiv, mdpi, thequantuminsider). I confirmed
this is a proxy-level policy block, not a WebFetch tool restriction, by hitting the same hosts with
raw `curl` (identical `403` on CONNECT). Practically, this means **every claim below is [reported]**
— read off WebSearch result summaries, which in several cases quote specific numbers from the primary
paper's abstract — rather than [verified] by reading a primary source myself. I have not fabricated
any citation; every source listed was returned by an actual search and its title/URL is reproduced
verbatim. Treat this file as a same-caliber-as-usual literature summary, not a personally-checked read.

## Bottom line (5 sentences max)

Post-publication decay is real and large — McLean & Pontiff (2016) found returns ~26% lower
out-of-sample and ~58% lower post-publication across 97 predictors [reported], and Chen & Velikov
(2023, JFQA) found that net of realistic trading costs and post-publication effects, the *average*
anomaly among 204 tested nets only ~4bps/month, with even the strongest netting ~10bps/month
[reported] — which should be the single most sobering number for this whole research family. Of the
candidate factors, quality/profitability and momentum (dynamically risk-managed) have the most
credible post-2015 live evidence, classic HML value and small-cap SMB in isolation are the closest
to "dead" (though value's 2021-2022 rebound complicates a clean "dead" verdict), and low-volatility
has decayed specifically because it got crowded and now trades expensive. The most retail-relevant
asymmetry is real: institutions structurally cannot fit into microcap/illiquid-name factor exposure,
and the evidence-backed illiquidity premium is concentrated almost entirely in that segment — but it's
also a segment where data quality, delisting bias, and execution slippage are hardest to get right,
which is exactly the kind of thing this platform's `docs/qapf-remaining-agents.spec.md`-style
discipline (verify against real data, not narrative) needs to interrogate before believing it. None of
this is a strategy yet — it's a shortlist of falsifiable, cheaply-killable theses, several of which
this platform's own `backend/agents/stats` (DSR) and `backend/agents/alpha` scaffolding could test
against real yfinance data in under a day.

## Candidate theses

### T1.1 — Quality/profitability (QMJ-style) factor still earns positive risk-adjusted returns out-of-sample post-2015, including through 2020-2025
- Evidence for: AQR's Quality-Minus-Junk (QMJ) construction reports monthly alphas of 16-38bps in
  published tests, most statistically significant [reported — AQR/Alpha Architect summary]. Multiple
  2024 sources describe quality (along with momentum and growth) as one of the factors that
  "performed exceptionally well over the past year" riding mega-cap tech strength [reported —
  Institutional Investor/PR Newswire coverage of a 2024 systematic-investing survey].
- Evidence against: the same sources flag that quality's recent strength is largely *because* it is
  crowded into the same handful of mega-cap tech names driving index concentration — in 2023 mega-caps
  drove "nearly two-thirds" of US equity index returns [reported]. That means quality's post-2015
  "success" may be a large-cap-momentum/growth proxy trade riding a concentration bubble, not an
  independent, diversifiable premium — the opposite of what you want for a small-capital strategy
  trying to avoid correlation to the index's own risk. No source found gives a clean, cost-adjusted,
  post-2015 Sharpe ratio for QMJ in isolation — this is the weakest-verified thesis of the set.
- Capital range where it works: works at any capital size in its large-cap-tilted institutional form,
  but a retail 20-50 name version concentrated in true "quality" (high profitability, low leverage,
  stable earnings) outside mega-cap tech is unverified — nobody found reported live numbers for that
  specific slice.
- Data required (and cost): fundamentals (ROE, gross profitability, accruals, leverage) — Stocklake/
  yfinance fundamentals (already in `backend/agents/macro`) are sufficient; free.
- Kill test (must be runnable in under 1 day with free/cheap data): construct a long-only top-quintile
  gross-profitability-minus-bottom-quintile spread on the current S&P 500 or Russell 3000 universe
  (yfinance fundamentals), 2016-2026, monthly rebalance, and check whether the spread's Sharpe survives
  after excluding the 10 largest-cap names each period. If the spread collapses once mega-caps are
  excluded, this thesis is dead as an independent edge (it's disguised beta to concentration).
- Verdict: marginal — real premium exists in the literature, but the specific claim "quality works
  independent of the mega-cap-tech trade, at retail scale, post-2015" is unverified and the kill test
  above should be run before building anything on it.

### T1.2 — Classic value (book-to-market, HML) is structurally impaired, not merely cyclically depressed
- Evidence for: value underperformed growth for roughly 2007-2020 with a reported 55% cumulative
  drawdown of the Fama-French HML factor by mid-2020 [reported — Alpha Architect/investing.com
  summaries]. The 2017-2020 window is explicitly termed the "Factor Investing Winter" in one source,
  where value and momentum both generated consistently negative returns [reported]. A separate strand
  of research attributes the decline specifically to HML's book-to-market construction failing to
  capture intangible assets (increasingly dominant in a software/IP-heavy economy) [reported —
  Asness/Ilmanen-adjacent AQR research described secondhand].
- Evidence against: value visibly recovered — Russell 1000 Value returned 24.95% in 2021 and, sources
  disagree on exact 2022 numbers but agree directionally, value materially outperformed growth in 2022
  as rates rose [reported — ycharts/Yahoo Finance summaries; note the two 2022 return figures returned
  by search (29.69% vs a stated "-7.74% decline") were internally inconsistent between sources, a
  reminder that even reported secondary numbers need cross-checking before being trusted]. A pure
  "value is dead" verdict is not well supported by the 2021-2024 window.
- Capital range where it works: value screens are simple (P/B, P/E) and don't require illiquid names,
  so this is capital-size-agnostic — the constraint is data quality (fundamentals field coverage), not
  capacity.
- Data required (and cost): P/B, P/E from yfinance or Stocklake fundamentals; free.
- Kill test: rebuild HML on the current investable universe (not Ken French's full CRSP universe) for
  2015-2026 with monthly rebalancing and realistic (0.1-0.3%) round-trip costs; check whether the
  long-short Sharpe is statistically distinguishable from zero using this platform's DSR
  implementation (`backend/agents/stats/toolkit.py`). If DSR says no, treat classic HML value as dead
  for this platform specifically, regardless of what the academic record says about other definitions.
- Verdict: marginal — the "dead" narrative was probably overstated even before 2021-2022 proved it
  wrong, but naive book-to-market value is a weak, noisy signal that needs the intangibles-adjusted or
  quality-combined variants to be credible; a DSR kill test on the naive version is cheap and should be
  run first since it's the version most builders reach for by default.

### T1.3 — Dynamically risk-managed momentum (not static 12-1 momentum) survives out-of-sample, including post-2015 crash periods
- Evidence for: Daniel & Moskowitz's "Momentum Crashes" [reported — NBER/SSRN abstract summary] shows
  crashes are partly forecastable (they cluster after market declines when volatility is high) and
  that a dynamic strategy conditioning position size on forecasted momentum mean/variance
  "approximately doubles the alpha and Sharpe Ratio of a static momentum strategy" [reported, directly
  from the abstract language returned by search]. This is a specific, falsifiable, load-bearing claim.
- Evidence against: static momentum crashed severely and repeatedly — reported figures include a >30%
  loss in weeks at the March 2009 bottom [reported], and a described crash again in March-May 2020 as
  momentum (long tech/healthcare, short beaten-down cyclicals) reversed violently on the 2020
  rebound/rotation [reported — no single hard percentage found and independently confirmed for
  2020, so treat the magnitude as unverified even though the direction is well corroborated across
  multiple sources]. Static long-only or long-short 12-1 momentum without the dynamic volatility
  scaling is exactly the naive version most retail builders implement, and it is the version most
  exposed to crash risk.
- Capital range where it works: works at any capital size for the long side; a long-short version needs
  shorting infrastructure this platform doesn't have (QAPF is long-only by deliberate decision per
  `backend/agents/portfolio/allocator.py`'s docstring), so only the long leg is accessible here —
  which changes the risk/return profile substantially versus what's reported in the literature (most
  momentum papers measure the long-short spread, not the long-only leg).
- Data required (and cost): trailing price returns (12-1 month skip-most-recent-month) — yfinance,
  free, already computed conceptually in `backend/agents/alpha` (momentum 12-1 factor is listed as
  already built there).
- Kill test: on the existing `backend/agents/alpha` momentum factor, add a volatility-scaling overlay
  (reduce position size when trailing realized vol or recent drawdown crosses a threshold, per the
  Daniel-Moskowitz "panic state" logic) and backtest 2018-2020 (spans COVID, already the platform's
  existing backtest window per `backend/agents/backtest`) with and without the overlay. If the overlay
  doesn't measurably reduce the drawdown/improve the Sharpe in that exact COVID window relative to
  static momentum, the dynamic-momentum thesis is not adding what the literature claims.
- Verdict: promising — this is the strongest-evidenced thesis in the set specifically because it's the
  most falsifiable and the platform already has 80% of the pieces (momentum factor, COVID backtest
  window, DSR) to run the kill test without new code.

### T1.4 — The low-volatility anomaly has decayed specifically because it is crowded and now trades expensive, not because the underlying mispricing disappeared
- Evidence for: multiple independent sources converge on the same mechanism — "low-volatility only
  works when it's cheap," and a 2014-era study found no alpha in a four-factor model except in
  "extremely cheap, low volatility environments" [reported]. Large ETF/product inflows since the 2010s
  are reported to have "compressed the prospective premium" and shifted low-vol strategies to be "more
  growth-oriented than even the overall market" [reported — evidenceinvestor.com summary].
- Evidence against: reported underperformance is large and recent — S&P 500 Low Volatility
  underperformed the market by "more than 30% cumulatively" from 2019-2020, and continued
  underperforming through the 2020-2021 rally [reported]. This is a long, multi-year underperformance
  stretch, not a brief blip, and it directly contradicts any framing of low-vol as a reliable
  small-capital edge today.
- Capital range where it works: in principle capacity-friendly (low-vol stocks tend to be larger,
  boring, liquid names) — this is one anomaly where retail capacity is *not* the binding constraint;
  crowding and valuation are.
- Data required (and cost): trailing realized volatility (already trivial from yfinance OHLCV) plus a
  valuation screen (P/B or P/E) to condition on "cheap low-vol" vs "expensive low-vol."
  Free.
- Kill test: split the current low-vol universe into cheap-low-vol vs expensive-low-vol quintiles by
  P/B, and check whether the return spread between them, not low-vol vs market, is where the alpha
  actually lives, 2015-2026. If cheap-low-vol doesn't clearly beat expensive-low-vol, the "it's a
  valuation-conditional effect" explanation itself is unsupported and low-vol should be treated as
  dead outright, not conditionally alive.
- Verdict: marginal-to-dead — the honest reading of the reported evidence is that unconditional
  low-vol has been a loser for most of the post-2015 period, and the "it still works if you buy it
  cheap" rescue is itself an unverified, not-yet-kill-tested claim rather than an established fact.

### T1.5 — Microcap/illiquid-name factor premia are more available to a $1,000-$100k account than to institutions, because institutions are structurally excluded from that segment
- Evidence for: this is the single most retail-relevant, well-corroborated structural claim found.
  Multiple independent sources agree: "the illiquidity premium... exists only among microcap stocks"
  and institutions can't access it because microcaps are collectively ~0.2-0.4% of total developed/EM
  market cap [reported — ScienceDirect/MSCI-adjacent summary]; a microcap-focused blog states plainly
  that illiquidity "is not so much of a barrier" for a retail-sized account the way it is for a fund
  managing billions [reported — microcapclub.com, a specialist community source, treated as [reported]
  not [verified] since not fetched directly]; O'Shaughnessy Asset Management's institutional-facing
  commentary (title only, page itself blocked) frames microcap factor spreads as wider precisely
  because institutions structurally cannot trade the space [reported, title/framing only — could not
  fetch body].
- Evidence against: the same "illiquidity premium... has negligible economic significance" framing
  cuts both ways — if the premium is only meaningful in a segment that's ~0.2-0.4% of total market cap,
  the number of genuinely investable, liquid-enough-to-actually-fill microcap names at even a $1,000-
  $100k position size may be small, and survivorship/delistment bias in microcap backtests is a known,
  serious problem that free data sources (yfinance) often handle poorly (delisted tickers silently
  vanish rather than being marked as a -100% return, which overstates the effect). No source found
  addressed data-quality/survivorship specifically for this segment — this is the biggest unverified
  risk in the whole thesis, and it's exactly the kind of thing `backend/agents/datainfra`'s stated
  mandate (feed staleness/gap/schema-drift) should be pointed at before trusting any microcap backtest.
- Capital range where it works: reported to work best exactly in the range this project is targeting
  ($1,000 scaling up) — this is the strongest capital-fit match of any thesis here, but "works" is
  currently a structural/theoretical claim, not a demonstrated net-of-cost live return.
- Data required (and cost): daily OHLCV + shares outstanding/float for microcap names (roughly
  sub-$300M market cap) with proper delisting-return handling — this is the one place free yfinance
  data is genuinely suspect (known to drop delisted tickers rather than recording the loss); a paid
  survivorship-bias-free dataset (e.g., CRSP-derived, or a paid provider) may be required to trust
  results, which is a real cost this platform doesn't currently have budgeted.
- Kill test: pull the current Russell Microcap or a sub-$300M-market-cap yfinance universe, and first
  just count how many names both (a) exist today and (b) have complete daily data back to 2016 without
  suspicious gaps — using the exact gap-detection logic already built in `backend/agents/datainfra`.
  If a large fraction of the "microcap universe" silently vanishes from the free data source over the
  period (delisting bias), that alone kills the free-data version of this thesis before any return
  number is even computed.
- Verdict: promising, but gated — the structural argument (institutions can't fit) is the best-
  evidenced retail-specific edge in this whole document, but it cannot be trusted until the data-
  quality kill test is run, because free-data survivorship bias could manufacture a fake premium out
  of nothing.

## What is definitively dead (don't waste time here)

- **The classic small-firm size effect (SMB) in isolation.** Convergent reported evidence: "it seems
  that the small-firm anomaly has disappeared since the initial publication of the papers that
  discovered it" [reported — Schwert (2003), quoted secondhand], with the effect essentially vanishing
  post-1980s. One line of research claims size resurfaces only after controlling for quality/junk
  ("Size Matters, if You Control Your Junk") [reported] — meaning naive size alone is not a strategy;
  it's a component that only shows up combined with quality. Don't build a standalone size factor.
- **Naive net-of-cost anomaly harvesting across the broad factor zoo.** Chen & Velikov's headline
  number — average anomaly nets ~4bps/month, best case ~10bps/month, after realistic costs and
  publication-effect adjustment across 204 tested anomalies [reported] — should be read as the base
  rate for "pick a factor from a paper and trade it." At that scale, retail commissions/spreads alone
  plausibly consume the entire edge for anything with real turnover. This doesn't kill the specific
  theses above, but it is the correct prior for anything not on this shortlist.
- **The t>2 standard for accepting a "new" factor.** Harvey, Liu & Zhu's multiple-testing correction
  reportedly leaves only 9 of 313 tested return-predicting variables significant at their |t|>3 bar
  [reported]. Any backtest result in this project reporting t~2 on a single trial should be treated as
  noise, not signal, before DSR correction — which is exactly what `backend/agents/stats`'s Deflated
  Sharpe Ratio implementation exists to catch; use it on every candidate here before trusting a Sharpe
  number.

## Sources
- [Does Academic Research Destroy Stock Return Predictability? — SSRN abstract page](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623) — McLean & Pontiff's headline decay numbers (26% out-of-sample, 58% post-publication decline across 97 predictors). [reported — could not fetch full text, egress-blocked]
- [Does Academic Research Destroy Stock Return Predictability? — Wiley/Journal of Finance](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365) — published version of the same paper. [reported, title/existence only — blocked]
- [Replicating Anomalies — NBER working paper](https://www.nber.org/system/files/working_papers/w23394/w23394.pdf) — Hou, Xue & Zhang's re-test of ~452 anomalies, roughly half failing to replicate. [reported — could not fetch full text, egress-blocked]
- [...and the Cross-Section of Expected Returns — Duke/Harvey personal page](https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF) — Harvey, Liu & Zhu's t>3.0 multiple-testing hurdle; "9 of 313" survive at that bar. [reported — could not fetch, egress-blocked]
- [A Taxonomy of Anomalies and their Trading Costs — SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2535173) — Novy-Marx & Velikov: anomalies with one-sided turnover <50% mostly survive net of costs; higher-turnover ones mostly don't. [reported]
- [Zeroing In on the Expected Returns of Anomalies — Federal Reserve working paper page](https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm) — Chen & Velikov (JFQA 2023): 204 anomalies, average net return ~4bps/month, best-case ~10bps/month after realistic costs and publication-effect adjustment. This is the single most important number in this file. [reported — egress-blocked from fetching full text]
- [Momentum Crashes — SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371227) — Daniel & Moskowitz: crashes cluster after market declines/high vol; dynamic (volatility-scaled) momentum roughly doubles static momentum's alpha and Sharpe. [reported]
- [Why Has the Size Effect Disappeared? — EFMA working paper](https://efmaefm.org/0efmameetings/efma%20annual%20meetings/2016-Switzerland/Papers/EFMA2016_0340_FullPaper.pdf) — size effect vanishing post-1980s, cited via Schwert (2003). [reported]
- [Size Matters, if You Control Your Junk — Jacobs Levy Center](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2015/05/Size-Matters-if-You-Control-Your-Junk.pdf) — size resurfaces when quality/junk is controlled for. [reported]
- [Is value dead? Has the story changed? No. — Alpha Architect](https://alphaarchitect.com/is-value-dead-has-the-story-changed-no/) — value's ~55% cumulative HML drawdown through mid-2020, and the intangibles-mismeasurement counter-argument. [reported — egress-blocked from fetching full text]
- [Deep Dive: Low-volatility investing — Evidence Investor](https://www.evidenceinvestor.com/post/low-volatility-investing) — low-vol crowding, valuation-conditional alpha, ~30% cumulative underperformance 2019-2020. [reported]
- [The Illiquidity Premium – Fact or Fiction? — MicrocapClub](https://microcapclub.com/the-illiquidity-premium-fact-or-fiction/) — practitioner argument that illiquidity is a much smaller barrier for small accounts than for institutional funds. [reported — egress-blocked from fetching full text]
- [Microcaps — Factor Spreads, Structural Biases, and the Institutional Imperative — OSAM](https://www.osam.com/Commentary/microcaps-factor-spreads-structural-biases-and-the-institutional-imperative) — institutional structural exclusion from microcap factor premia. [reported, title/framing only — egress-blocked]
- [Liquidity and the cross-section of international stock returns — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426621000819) — illiquidity premium concentrated almost entirely in microcaps, negligible at broader scale. [reported]
- [Mega-Cap Tech Stock Dominance Prompts Big Shifts in Systematic Investing — PR Newswire](https://www.prnewswire.com/news-releases/mega-cap-tech-stock-dominance-prompts-big-shifts-in-systematic-investing-302288200.html) — quality/momentum/growth factor strength tied to mega-cap tech concentration, 2023-2024. [reported]
- [Russell 1000 Value / Growth Total Return — ycharts](https://ycharts.com/indices/%5ERLVTR) and [IWD performance — Yahoo Finance](https://finance.yahoo.com/quote/IWD/performance/) — value's 2021-2022 return numbers (used with a noted internal inconsistency between the two 2022 figures returned by search — flagged in T1.2, not resolved). [reported]

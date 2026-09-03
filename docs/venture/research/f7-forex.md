# F7 — Foreign exchange
Researched: 2026-08-27 | Researcher: subagent

## Environment note (read before trusting any tag below)
This session's egress proxy blocked every direct fetch attempted — `goodmoneyguide.com`,
`cftc.gov`, `nber.org`-hosted PDFs, `quantpedia.com`, `sec.gov`, `federalreserve.gov`, and
others returned `EGRESS_BLOCKED` / 403 policy denials. Only WebSearch (result-summary) access
worked. **Every claim in this file is therefore `[reported]` at best** — a search-result
summary of a secondary or tertiary source, not a primary source I read myself. Where a
regulator's own disclosure numbers are quoted (ESMA/FCA loss percentages, CFTC leverage
caps), the underlying rule is real and independently well-known, but the specific figures
came through aggregator sites, not the regulator's own page, and must be re-verified from a
network with open access before being used to size a position or justify an architecture
decision. Nothing here is tagged `[verified]`.

## Bottom line (5 sentences max)
FX carry is the one genuinely documented risk premium in this family, but it is
short-volatility in disguise — small steady gains funded by an exposure to rare, fast,
double-digit-in-days crashes (2008, 2015 CHF, Aug 2024 yen) that a $1,000 account cannot
survive even at modest leverage. FX trend-following, which used to complement carry, has
been reported as running at roughly a fifth of its 2000s Sharpe ratio since the 2010s, so it
no longer reliably pays for carry's tail risk the way 2000s-era research assumed. PPP mean
reversion is real but operates on a 2.5–5 year half-life — a fine institutional risk premium,
unusable for a solo operator who needs feedback loops faster than years. The retail FX
industry's economics are the dominant finding of this research: regulator-mandated
disclosures show most retail FX/CFD accounts lose money (reported ranges from the mid-40s to
high-80s percent depending on broker and period), a structural outcome of a dealing-desk
("B-book") model where the broker is frequently the client's direct counterparty — this is
arguably a bigger threat to this operator's capital than any of the four theses above. Net:
FX's appeal to a small account is overwhelmingly its high leverage and near-zero minimum,
which is exactly the combination known to destroy small accounts fastest, and this operator's
engineering strengths (Qlib, walk-forward, DSR) are far better spent on a market structure
that is not adversarial to the retail counterparty by design.

## Retail FX industry structure — the B-book problem and what regulator disclosures show

**The mechanism.** A "B-book" (dealing-desk / market-maker) broker takes the other side of a
retail client's trade internally rather than routing it to the interbank/ECN market. If the
client loses, the broker's book profits directly; if the client wins, the broker's book
loses. This is a structural conflict of interest, not a rare abuse — it is the declared
business model of a large share of the retail FX/CFD industry, because most retail flow is
reported to be net-losing over time, which makes internalizing it profitable for the broker.
[reported] Some brokers run a hybrid — A-booking (routing to market) profitable/large clients
and B-booking the rest — determined algorithmically by the broker, invisibly to the client.
[reported]

**What regulator-mandated disclosures show.** Following the 2018 ESMA product-intervention
measures, EU/UK CFD (which in practice means most retail FX-as-CFD) providers must publish
the percentage of their own retail client accounts that lost money over a trailing 12-month
window, refreshed quarterly, in a standardized risk warning ("[X]% of retail CFD accounts
lose money"). This is one of the only pieces of ground-truth retail-outcome data anywhere in
finance, because it is regulator-compelled rather than broker-marketed. [reported]

- ESMA's own 2018 review across the CFD industry found **74–89%** of retail CFD accounts lost
  money, with average per-client losses of roughly €1,600–€29,000. [reported]
- Individual UK broker disclosures reported via aggregator sites in 2025: CMC Markets UK
  ~68%, IG UK ~68%, IG International ~71%, eToro ~46%, Saxo/Spreadex/Interactive Brokers in a
  ~60–70% range, Plus500 ~76%; one aggregator's cross-broker range was **62–82%**. [reported —
  I could not reach the FCA's own register or brokers' own disclosure pages directly; these
  numbers came through secondary aggregator sites, not the primary disclosures]
- FCA commentary (via secondary source) frames its leverage caps and loss-protection rules as
  preventing roughly 400,000 UK retail clients per year from losing more than their deposited
  stake, worth an estimated £267m–£451m in avoided losses. [reported]

**Is there a structural reason retail FX is worse than retail equities?** Yes, and it is not
just leverage. In equities, a retail broker executing a stock trade is not typically the
counterparty to that trade — it routes to an exchange or a wholesale market maker under
Reg NMS best-execution obligations, and payment-for-order-flow economics, while also
conflicted, do not require the retail client to lose for the broker to profit on that specific
trade. In OTC retail FX, the *broker itself* can legally be the counterparty with no
exchange, no central limit order book, and (in the US) no obligation to internalize losses
either way — the broker's quote **is** the market the retail client sees. Combined with
leverage regularly 20–50x (vs. 2x/4x in equities) and no exchange-mandated price transparency,
the retail FX structure concentrates three loss-amplifying features (counterparty conflict,
opaque pricing, high leverage) that retail equities mostly do not have simultaneously.
[reported / synthesized from the above — this specific comparative framing is my own
inference from the sourced facts, not itself a cited claim, and should be flagged as such]

## US regulatory constraints (CFTC/NFA) that change what is implementable

- **Leverage caps:** 50:1 on major currency pairs, 20:1 on minors/others, set by CFTC final
  rule under Dodd-Frank. [reported] This is far below the 200–500:1 leverage historically
  offered by offshore/EU brokers pre-ESMA, and is itself a partial protective feature — it
  structurally limits how fast a US retail account can be wiped out by a single gap move
  compared to, e.g., the 2015 CHF shock at brokers offering 200:1+.
- **FIFO rule (NFA Compliance Rule 2-43b):** same-pair, same-size positions must be closed in
  the order they were opened. This constrains position-management techniques (e.g., partial
  scaling out of a specific tranche) that are routine at non-US brokers. [reported]
- **No-hedging rule:** a US retail account cannot hold simultaneous long and short positions
  in the same pair at the same broker — a new opposite trade offsets the existing one instead
  of creating a hedge position. [reported] This forecloses certain options-adjacent or
  dual-direction retail structures that are legal in other jurisdictions.
- **No negative-balance protection mandate:** unlike the EU/UK post-2015 reforms, the CFTC does
  not require US retail forex dealers to cap client losses at the deposited amount, so a
  fast-enough gap can in principle put a US retail FX account in debt to the broker.
  [reported — one source describes this as the consistent position across multiple secondary
  sources, though one aggregator noted conflicting claims; treat the "no NBP mandate" reading
  as the more consistent one across sources, not fully verified]
- **Which brokers are actually eligible:** reported list of firms actually registered as CFTC
  Retail Foreign Exchange Dealers (RFED) / NFA Forex Dealer Members serving US retail spot FX
  in 2026: **Forex.com (StoneX), OANDA, IG US (rebranded tastyfx), Interactive Brokers**, and
  historically Charles Schwab/thinkorswim (post-TD Ameritrade integration). [reported — this
  is a short, consistent list across several aggregator sources but I could not cross-check it
  against the NFA's own member registry directly]
- **PDT rule does not apply:** the pattern-day-trader rule (3 day-trades per 5 days under
  $25k equity) is a FINRA rule scoped to US-securities margin accounts. Spot FX at an
  NFA-regulated dealer is CFTC/NFA-regulated, not FINRA-regulated, so PDT does not apply.
  [reported] This is one of the few genuine structural advantages FX offers a small account
  relative to equities.
- **CME (exchange-traded) alternative exists:** Micro FX futures (1/10-size EUR/USD, GBP/USD,
  JPY/USD, etc.) trade on CME's central limit order book with CME Clearing as counterparty —
  eliminating the B-book conflict entirely, at the cost of futures-account overhead and
  (modest, but nonzero) minimum margin per micro contract. [reported] This is a materially
  different market-structure proposition from OTC spot FX and is discussed further below.

## Candidate theses

### T7.1 — FX carry (buy high-yield currencies funded by low-yield currencies) still earns a positive risk premium on average, but the premium is compensation for rare, fast crash risk that a $1,000 account cannot survive.
- **Evidence for:** The forward premium puzzle — high-interest-rate currencies do not
  depreciate enough to offset the rate differential, contrary to uncovered interest parity —
  is one of the most replicated findings in international finance, and academic carry
  strategies (Lustig/Verdelhan-style dollar-neutral, multi-currency baskets) reported
  pre-2008 Sharpe ratios around 0.78–1.08. [reported]
- **Evidence against / crash history:** Post-2008, reported Sharpe fell to roughly 0.2–0.25 —
  a >70% degradation — and carry "significantly underperformed equities" in the following
  decade. [reported] Quantified crash episodes: the 2007–2009 unwind produced drawdowns
  reported at -7.2% (30 days) up to -32% (399 days) for developed-market carry baskets, with
  the worst window early Aug 2008–early Feb 2009. [reported, citing the Daniel/Hodrick/Lu NBER
  working paper "The Carry Trade: Risks and Drawdowns," which I could not fetch directly].
  The Jan 15, 2015 Swiss National Bank floor removal produced a ~30% single-session move in
  CHF pairs with ~45 minutes of near-zero liquidity; FXCM alone reported $225M in client
  negative balances and required emergency financing to survive; Alpari UK went insolvent.
  [reported] The Aug 5, 2024 yen-carry unwind produced the Nikkei's worst single-day fall since
  1987 (-12.4%) alongside a record one-day VIX spike, in what was reported as the largest
  cross-asset shock since March 2020, on an estimated $500B–$1.5T unwound carry position.
  [reported]
- **Risk premium or mispricing?** Genuinely debated as a risk premium (compensation for
  crash/liquidity/global-risk exposure — this is the mainstream academic framing) rather than
  a pure inefficiency; either way the compensation is explicitly for bearing negative-skew
  tail risk, not a free lunch.
- **Cost arithmetic (spread + swap):** Retail majors run roughly 0.5–1.5 pip spreads (~$5–$15
  per $100k lot per round-trip); minors/crosses ~1.5–5 pips; exotics (the pairs where carry
  differentials are largest, e.g. USD/TRY, USD/ZAR, USD/MXN) can run 20+ pips (~$200/lot).
  [reported] Swap/rollover is quoted per-lot per-night and the broker keeps a spread on it
  (pays less on the favorable-direction swap than it charges on the unfavorable direction), so
  realized carry income is systematically below the textbook interest-differential number.
  [reported] Because the largest carry differentials live in the exotics with the widest
  spreads, a meaningful share of the theoretical annual carry return at retail size is
  consumed by entry/exit cost and rollover-spread leakage before any crash risk is even
  considered — I could not obtain current, broker-specific numbers precise enough to quantify
  "what fraction" with confidence; this needs re-verification with live broker data.
- **Capital range where it works:** Carry as an institutional risk premium is arguably viable
  at scale where the operator can (a) diversify across many currency pairs to dampen
  single-pair crash exposure, (b) survive a -20 to -30% drawdown without forced liquidation,
  and (c) access swap/spread pricing meaningfully better than retail. None of the three hold
  at $1,000.
- **Kill test (runnable in under 1 day with free data):** Pull daily FX spot (or futures)
  data for a standard G10 carry basket (long historically-high-yield currencies vs. short
  historically-low-yield, e.g. AUD/JPY, NZD/JPY, TRY-adjacent proxies where data allows) over
  2005–2026 from free sources (yfinance FX tickers or `fredgraph` series), compute the
  strategy's max drawdown and its Deflated Sharpe Ratio, and explicitly check the return
  distribution's skew and kurtosis. If skew is strongly negative and the worst historical
  drawdown, sized to $1,000 at any leverage that produces a competitive return, would have
  breached the account (or come close), the thesis is falsified for this operator regardless
  of the average Sharpe.
- **Verdict: dead** for this account size, specifically because of the disqualifying negative
  skew and quantified crash history (2008, 2015 CHF, 2024 yen) relative to $1,000 of capital
  — not because the premium isn't real.

### T7.2 — FX trend-following / momentum, once a credible complement to carry, has decayed to a near-zero edge out of sample since the 2010s and does not reliably survive a modern walk-forward test.
- **Evidence for:** Time-series and cross-sectional currency momentum was a documented anomaly
  in the 2000s, with one reported source citing 2000s Sharpe/Sortino near 1.9/2.9 for a
  price-based trend strategy. [reported]
- **Evidence against / decay:** The same source reports 2010s–2020s Sharpe/Sortino collapsing
  to roughly 0.2/0.3 — an ~85–90% degradation — attributed to the ultra-low-rate,
  policy-dominated, "trendless"/whipsaw regime of that period. [reported] A separate
  2003–2025 walk-forward validation study reportedly found only 2 of 7 currency pairs
  (USD/JPY and EUR/USD, both using time-series momentum) clearing a 0.5 Sharpe "tradeability"
  bar out of sample — i.e., most pairs/specifications failed. [reported]
- **Risk premium or mispricing?** More consistent with a (possibly time-varying,
  regime-dependent) inefficiency than a stable risk premium — trend strategies pay out unevenly
  across decades in a way that doesn't map cleanly to a persistent risk exposure, which is also
  why it can decay this hard.
- **Cost arithmetic:** Trend-following trades less frequently than pure scalping but still
  needs to clear spread + swap on every rotation; on the majors where trend signals are most
  reliably tested this is the cheaper end of the retail cost spectrum (sub-1.5 pip spreads),
  but a strategy running at reported 0.2–0.3 Sharpe has very little room to absorb even modest
  retail frictions before turning negative net of costs.
- **Capital range where it works:** Unclear that it robustly "works" anywhere at the reported
  post-2010 Sharpe levels; if it does, scale/diversification (many pairs, many timeframes)
  matters more than capital size per se, which still disadvantages a single-account operator
  relative to a fund running the same signal across 20+ instruments.
- **Kill test (runnable in under 1 day with free data):** Implement a plain time-series
  momentum signal (e.g., 12-month or moving-average-crossover) on free daily FX data for the
  major pairs, walk-forward it 2010–2026 out of sample with a strategy-selected-before-fitting
  train/test split, and compute the DSR. Given the reported literature already shows this
  decayed hard in exactly this period, the prior going in should be low; the kill test is
  whether this operator's own harness reproduces a Sharpe anywhere near the reported ~0.2–0.3
  (weak but survivable) or effectively zero/negative net of realistic retail costs (dead).
- **Verdict: marginal-to-dead** — worth a cheap confirmatory kill test only because the data
  is free and the harness already exists, but the literature consensus going in is that this
  edge has been arbitraged/regime-shifted away for a decade.

### T7.3 — PPP-based currency value/mean-reversion is a real, replicated finding, but its half-life (2.5–5 years) makes it structurally unusable for a solo operator who needs a shorter feedback loop.
- **Evidence for:** Multiple independent methodologies (long single-country time series back
  to 1900, post-1973 floating-era panels, 150-country panel data, and a 2002–2022 OECD panel)
  converge on real-exchange-rate deviations from PPP having half-lives of roughly 2.5–5 years,
  eroding at a rate reported around ~15%/year. [reported, multiple converging secondary
  summaries of the academic literature — this is one of the more robustly triangulated
  findings in this whole report, even though none of the underlying papers were read directly]
- **Evidence against / crash history:** Not crash-prone in the way carry is — the "cost" here
  is not tail risk but time and patience: a genuinely mean-reverting deviation can take years
  to close, and can widen further before it narrows (no clean stop-loss discipline maps onto a
  multi-year reversion horizon the way it does onto a directional trade).
- **Risk premium or mispricing?** Closer to a slow-moving mispricing/anomaly than a
  compensated risk premium — but the practical constraint is horizon, not classification.
- **Cost arithmetic:** Low trading frequency (positions held years) means spread/swap cost is
  nearly irrelevant per trade, but swap is charged **every single night** a position is held,
  so multi-year holding periods compound rollover cost in a way that is easy to underestimate
  if only spread is modeled; this needs explicit multi-year swap accrual math before being
  taken seriously, which I did not have live broker rate data to perform.
- **Capital range where it works:** Institutional/pension-style capital that can hold a
  multi-year position through interim volatility without needing the capital for anything
  else — the opposite of a $1,000 account explicitly trying to compound and scale.
- **Kill test:** Not really a same-day kill test in the traditional sense — the test is a
  capital-and-time-horizon check, not a statistical one: can this operator hold a position for
  2–5 years while it might be underwater, without needing the capital? For a $1,000 account
  aiming to scale, the honest answer is no.
- **Verdict: dead for this operator** — not because the anomaly is false, but because the
  horizon is incompatible with the stated goal (a verifiable edge on a path to scaling capital
  soon, not a multi-year buy-and-hold).

### T7.4 — Central-bank policy-divergence trading is discretionary macro dressed as a strategy for a solo retail operator, not a systematic, backtestable edge at this scale.
- **Evidence for:** Rate-differential/policy-divergence framing does explain large, real,
  multi-year currency moves after the fact (Fed-vs-ECB 2022–2024 divergence coinciding with
  USD/EUR moving from ~1.05 to ~1.12; BoJ-vs-Fed divergence 2016–2024 coinciding with a
  reported ~36% USD/JPY move). [reported] One secondary source claims interest-rate
  differentials alone explain roughly 50% of forward-premium-puzzle variance in majors, and
  that divergence/yield differentials explain 60%+ of major-pair movement over multi-year
  horizons, attributed to academic work (Clarida/Gali/Gertler-style monetary-policy-rule
  literature). [reported — I was not able to verify this specific attribution or the 50%/60%
  figures against the named authors' actual work; treat this figure with more caution than the
  PPP half-life numbers above, since it came from a single lower-quality aggregator summary
  rather than multiple converging sources]
- **Evidence against:** This is fundamentally a narrative/explanatory framework applied after
  the fact to known moves, not a demonstrated systematic signal with a published, replicated,
  out-of-sample backtest the way carry or momentum have. Turning "the Fed and ECB are
  diverging" into a tradeable, falsifiable, mechanically-defined signal (which meeting, which
  dot-plot revision, what threshold of divergence, what entry/exit rule) requires building the
  systematic strategy from scratch — the "evidence" found here supports the general economic
  logic of FX, not a specific implementable rule.
- **Risk premium or mispricing?** Neither, as stated — it's closer to a macro thesis than a
  strategy until someone formalizes it into rules and backtests those rules.
- **Cost arithmetic / capital range:** Not assessable until the signal is formalized into
  actual entry/exit rules.
- **Kill test:** Not runnable as stated — the prerequisite work (defining the systematic rule)
  hasn't been done. If pursued, the kill test is: formalize one specific, mechanical
  policy-divergence signal (e.g., a rules-based rate-differential z-score with a defined
  rebalance schedule) and DSR-test it walk-forward before believing any of the narrative
  evidence above applies to it.
- **Verdict: dead as stated (not a strategy yet)** — this is the weakest-evidenced thesis in
  this report and should not be pursued without first doing the rule-definition work that
  would make it comparable to carry or momentum.

### T7.5 — The retail FX/CFD industry's own regulator-mandated loss disclosures are themselves the strongest, best-evidenced finding in this whole report, and function as a standing disqualifier for trading FX through a typical retail OTC broker regardless of which strategy is chosen.
- **Evidence for:** See "Retail FX industry structure" above — ESMA's own 74–89% figure and
  the cross-broker 46–82% range from individual FCA-regulated broker disclosures are
  regulator-compelled, not marketing claims, and are internally consistent with each other
  (different brokers, same order of magnitude, same regime). [reported, multiple converging
  sources]
- **Evidence against:** These disclosures are EU/UK-specific (ESMA/FCA COBS 22.5); the CFTC
  does not appear to mandate an equivalent public per-broker loss-rate disclosure for US
  retail forex dealers, so the closest analog for the actual US brokers this operator could
  legally use (Forex.com, OANDA, IG US/tastyfx, Interactive Brokers) was not found in this
  research pass — this is a real gap, not an assumption that US numbers match EU numbers.
  [explicitly unverified for the US-specific case]
- **Risk premium or mispricing? N/A** — this is a market-structure finding, not a strategy
  thesis.
- **Cost arithmetic:** Not a cost line item — it's evidence about the counterparty
  relationship itself.
- **Kill test:** Directly actionable: before funding any US account, check (a) whether the
  chosen broker executes as agency/STP to an exchange or ECN vs. running a dealing desk, and
  (b) whether Micro FX futures on CME (which eliminate the B-book conflict via central
  clearing) are a viable substitute for the same directional exposure at comparable size.
- **Verdict: this is not a "thesis" to grade promising/marginal/dead — it's a standing
  constraint.** Any FX strategy this operator pursues should default to CME Micro FX futures
  or a verified agency-model broker, not a dealing-desk OTC spot account, independent of which
  of T7.1–T7.4 (if any) is ever revisited.

## Does FX offer this operator anything equities/futures do not? (direct answer required)

**Mostly no, on the strategy side — and the one real structural advantage doesn't come from
"FX" as an asset class, it comes from being CFTC/NFA-regulated instead of FINRA-regulated.**
Specifically:
- **No PDT rule** applies to spot FX or FX futures (both are CFTC/NFA, not FINRA), unlike
  equities where sub-$25k accounts are capped at 3 day trades per 5 days. This is real and
  useful for a $1,000 account that wants intraday flexibility. But note: **this exact same
  advantage is available via CME Micro FX futures or other futures products** — it is not
  unique to OTC spot FX, and futures avoid the B-book conflict entirely.
- **24/5 market access and very low minimums** are real, but these are precisely the two
  features (always-open, low-friction entry) that combine with high leverage to produce the
  worst-documented retail outcomes in this entire research pass. Ease of entry is not an edge;
  it's the mechanism by which capital is destroyed fastest.
- **Genuinely documented risk premia exist (carry, historically momentum)** the way they do in
  equities, but this research did not find that FX's specific premia are *more* accessible or
  *more* survivable at $1,000 than equity-factor or futures-based alternatives — if anything,
  carry's crash profile is worse-documented and worse-quantified (2008, 2015, 2024) than most
  single equity-factor drawdowns, and FX trend-following's post-2010 decay is comparable to or
  worse than reported equity-momentum decay.
- **The honest comparison:** FX's appeal to this operator is overwhelmingly (a) high leverage
  and (b) a $1,000-friendly minimum, both of which are available with *less* structural
  counterparty conflict via CME Micro FX futures than via a typical OTC retail FX broker. If
  this operator wants FX exposure specifically, futures are the better-evidenced venue; if the
  operator wants "a verifiable edge that isn't fighting its own broker," this research did not
  surface a compelling reason to prefer FX over the other six families this Phase 1 study
  covers.

## Sources
- [FX Carry Trade - Quantpedia](https://quantpedia.com/strategies/fx-carry-trade) — carry trade summary; page itself unreachable (proxy-blocked), used via search snippet only
- [Carry Trades and Currency Crashes | NBER Macroeconomics Annual](https://www.journals.uchicago.edu/doi/full/10.1086/593088) — carry crash risk framing; not fetched directly
- [NBER Working Paper w20433 — The Carry Trade: Risks and Drawdowns (Daniel, Hodrick, Lu)](https://www.nber.org/system/files/working_papers/w20433/w20433.pdf) — source of quantified carry drawdown figures; not fetched directly (nber.org blocked), used via search summary
- [CXO Advisory — Currency Carry Trade Drawdowns](https://www.cxoadvisory.com/currency-trading/currency-carry-trade-drawdowns/) — drawdown data aggregation; not fetched directly
- [CNBC — The big 'carry trade' unwind is far from over](https://www.cnbc.com/2024/08/13/carry-trades-why-strategists-believe-a-major-unwind-is-far-from-over.html) — Aug 2024 yen unwind magnitude and position-size estimates
- [Fortune — Retail investors lose more than $400 million on Swiss currency bets](https://fortune.com/2015/01/16/swiss-franc-400-million-losses/) — 2015 CHF shock retail losses
- [LeapRate — How Forex Brokers Went Bankrupt Overnight amid EURCHF Flash Crash](https://www.leaprate.com/news/how-forex-brokers-went-bankrupt-overnight-amid-eurchf-flash-crash-infographic/) — broker insolvencies (FXCM, Alpari UK) from the 2015 shock
- [Finance Magnates — FXCM Gives a Second-by-Second Account of SNB Flash Crash](https://www.financemagnates.com/forex/brokers/fxcm-publishes-data-of-snb-mishandling-of-the-swiss-franc/) — FXCM's $225M negative-balance figure
- [Macrosynergy — Diversified trend following in emerging FX markets](https://macrosynergy.com/research/diversified-trend-following-in-emerging-fx-markets/) — FX trend Sharpe decay 2000s vs 2010s/2020s
- [QuantInsti EPAT — FX Trend-Following: A Walk-Forward Validation Study](https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets-epat-project/) — 2003–2025 walk-forward tradeability results (2 of 7 pairs cleared bar)
- [ScienceDirect — A panel project on purchasing power parity: Mean reversion within and between countries](https://sciencedirect.com/science/article/abs/pii/0022199695013962) — PPP half-life panel evidence; abstract-level only
- [Berkeley/Papell — Long Run Purchasing Power Parity: Cassel or Balassa-Samuelson?](https://eml.berkeley.edu/~obstfeld/281_sp04/papell.pdf) — PPP half-life literature review; not fetched directly
- [ESMA — ESMA agrees to prohibit binary options and restrict CFDs to protect retail investors](https://www.esma.europa.eu/press-news/esma-news/esma-agrees-prohibit-binary-options-and-restrict-cfds-protect-retail-investors) — origin of the 74–89% retail-CFD-loss figure and the standardized risk-warning requirement; press release, not the underlying data study
- [Finance Magnates — FCA Reports £75M CFD Loss for 90K Retail Investors](https://www.financemagnates.com/forex/fca-reports-75m-cfd-loss-for-90k-retail-investors-at-one-firm-promoted-by-finfluencers/) — recent FCA enforcement context
- [FCA Handbook COBS 22.5](https://handbook.fca.org.uk/handbook/cobs22/cobs22s5) — the actual UK rule requiring quarterly per-broker loss-percentage disclosure; page not fetched directly, rule text summarized via search
- Broker-specific loss percentages (CMC ~68%, IG UK ~68%, IG Intl ~71%, eToro ~46%, Plus500 ~76%, cross-broker range 62–82%) — sourced via WebSearch summaries of aggregator sites (goodmoneyguide.com, quantifiedstrategies.com); goodmoneyguide.com itself returned `EGRESS_BLOCKED` on direct fetch, so these figures are one hop further from the primary disclosure than ideal — re-verify against each broker's own published risk-warning page before relying on a specific number
- [CFTC — Final Rule Regarding Retail Foreign Exchange Transactions (fact sheet PDF)](https://www.cftc.gov/sites/default/files/idc/groups/public/@newsroom/documents/file/forexfinalrulefactsheet.pdf) — leverage caps, FIFO, no-hedging rule; PDF blocked on direct fetch, summarized via search snippet only
- [BabyPips — New CFTC Rules on Retail Forex Trading](https://www.babypips.com/news/new_cftc_rules_on_retail_forex) — secondary summary of the same CFTC rule
- [SEC — Fast Answers: Pattern Day Trader](https://www.sec.gov/fast-answers/answerspatterndaytraderhtm.html) — confirms PDT is a FINRA/securities-margin-account rule; page blocked on direct fetch, summarized via search
- [CME Group — Micro FX Futures](https://www.cmegroup.com/markets/microsuite/fx.html) — CME Micro FX futures as a centrally-cleared alternative to OTC spot FX
- Broker spread figures (OANDA EUR/USD ~0.8–0.94 pips, exotics like USD/TRY 20+ pips) — via WebSearch summaries of comparison sites (compareforexbrokers.com, alphaexcapital.com); not independently verified against OANDA's own live pricing
- Retail forex profitability aggregate statistics (various "% of traders lose money" figures from Medium/blog aggregators) — explicitly flagged as low-quality secondary sources in this file; only the ESMA/FCA regulator-disclosure-derived figures above should be treated as reasonably reliable

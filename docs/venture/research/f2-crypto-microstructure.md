# F2 — Crypto market structure and carry
Researched: 2026-08-27 | Researcher: subagent

## Research-access disclosure (read before trusting any number below)

This session's egress proxy blocks essentially every primary crypto data/exchange source
(binance.com, bybit.com, okx.com, coinglass.com, deribit.com, kraken.com, coinbase.com,
hyperliquid docs, defillama.com, even en.wikipedia.org — both the websites and their public
REST APIs, confirmed with raw `curl`). Only `github.com` raw content and the `WebSearch` tool
(which returns synthesized snippets, not raw pages) were reachable. This means **no number in
this report is [verified]** in the strict "I read the primary source" sense used elsewhere in
this project — the tagging below uses [reported] for numbers that came from a specific named
secondary source via search, and [unverified] where sources disagreed or coverage was thin.
Before trading on any figure here, re-pull it from the exchange's own docs/API from the actual
dev machine (which is very likely not subject to this sandbox's blocklist).

## Bottom line (5 sentences max)

Perpetual funding-rate capture is the one thesis with real, repeated evidence of positive
net-of-fee carry through 2025–2026, but its economics scale *up* with capital (practical
minimum ~$5–10k per position per multiple sources) while a $1,000 account sits below that
threshold and is additionally locked out of the deepest, cheapest venues (Binance, Bybit, OKX,
Hyperliquid all restrict US persons) — so it is real but currently the wrong size and the wrong
jurisdiction, not dead. Cash-and-carry basis on CME is arithmetically dead at $1,000 (a single
Micro BTC futures contract alone needs ~$2,800 of margin); cross-exchange latency arbitrage and
solo MEV are both dead for a technically strong solo operator without colocated/validator-adjacent
infrastructure regardless of capital. Concentrated-liquidity DEX LPing is a coin-flip at best
(>51% of Uniswap v3 LPs studied were net unprofitable) and needs active management, not passive
yield. The single most important fact for tail risk: on 2025-10-10, ~$19B was liquidated in
hours and Binance's own delta-neutral "market-neutral" clients got hurt when unrelated collateral
assets (USDe, BNSOL, wBETH) de-pegged on Binance's internal price feed and dragged supposedly
hedged accounts into liquidation — proving "delta-neutral" crypto carry is not neutral to
exchange-specific infrastructure risk. Statistical edges (weekend effect, altcoin-BTC lead-lag)
are the cheapest to test and the least verified either way — they belong in a kill-test, not a
funded strategy, until run against real data.

## Candidate theses

### T2.1 — Delta-neutral perpetual funding-rate capture (long spot / short perp) still nets positive carry after fees, but only once position size clears exchange fixed-cost minimums.

- Evidence for: Multiple 2025–2026 secondary sources converge on a positive-carry range: "10–30%"
  average annual yield in 2026, "19.26%" average 2025 return with <2% max drawdown from one cited
  fund, and a separate claim of "3–12% net APR on BTC/ETH, 20–60%+ on mid/long-tail pairs" on
  Hyperliquid. [reported — CoinMarketCap Academy, ArbitrageGhost/Medium via search, Buildix,
  NeuralArb via search]
- Evidence against: The same sources warn most retail funding-arb traders lose money from
  under-accounting fees and not monitoring delta in real time [reported — ArbitrageGhost]. More
  seriously: on 2025-10-10 Binance's Unified Margin Account used *internal* order-book pricing
  (not external oracles) to value collateral assets USDe/BNSOL/wBETH; when those de-pegged on
  Binance specifically (USDe to $0.65, BNSOL to $35, WBETH to $450) accounts running standard
  long-spot/short-perp "market-neutral" books were auto-deleveraged (ADL) out of their hedges —
  "positions that would have survived in isolated margin systems were liquidated due to unrelated
  collateral depegging." [reported — TradingView/Uphold research, Medium/Nicola Harvey, CoinDesk
  data blog, via search]. Binance later compensated affected users for the 2025-10-10 21:36–22:16
  UTC window specifically [reported]. This is direct, dated evidence that "delta-neutral" does not
  mean "risk-neutral" — it is neutral to spot-price risk only, not to exchange infrastructure risk.
- Net-of-fee arithmetic: Round-trip transaction cost (open spot + open perp + close spot + close
  perp, all taker) is commonly cited at **0.2–0.3% one-time** [reported — arbitragescanner.io via
  search], consistent with adding two legs of Kraken's 0.05% taker fee twice (0.05% × 4 = 0.20%)
  [reported — Kraken support via search, standard-tier schedule]. Against a funding APY in the
  10–20% range, the one-time cost is recovered in roughly (0.2–0.3%) / (10–20% ÷ 365) ≈ **4–11
  days** — fees are not the binding constraint if the position is held weeks to months. The
  binding constraint is fixed costs relative to size: withdrawal/gas fees and minimum order sizes
  are roughly fixed in dollar terms, so at $1,000 total capital they consume a much larger share
  of expected return than at $10,000+. Binance's own minimum BTCUSDT perp order is ~0.001 BTC
  (~$67 notional) [reported], meaning position granularity itself isn't the blocker at $1,000 —
  the blocker is that funding often turns negative or near-zero (funding is a two-sided market,
  not a guaranteed subsidy) and a $1,000 book can't diversify across enough coin-legs to smooth
  that out the way a $10k+ book running 10–20 pairs simultaneously can.
- Capital range where it works: Multiple independent sources put the "practical sweet spot" at
  **$5,000–$50,000 per opportunity**, with one calling <$5,000 "economically infeasible" given
  0.2–0.3% round-trip cost, and another citing a $10,000–$25,000 recommended working minimum
  [reported — arbiscreen, sharpe.ai via search, both unverified independently]. Scales roughly
  linearly up to ~$500k per coin before the trader's own flow starts moving funding rates
  [reported]. **At exactly $1,000, this thesis sits below its own stated viability floor** —
  it is a strategy this project should revisit once capital is 5–10x larger, not one to build now.
- Data/infra required (and cost): A live position needs simultaneous spot + perp accounts on the
  same or correlated-margin venue, real-time funding-rate and mark-price feeds, and automated
  delta-rebalancing (funding-rate direction can flip; a manually-monitored book will miss flips).
  Free tier: exchange REST/WS APIs are free to query (rate-limited); the real cost is capital
  itself, not data. **Jurisdiction is a bigger blocker than infra for a US-based operator**:
  Binance, Bybit, OKX, and Hyperliquid (the venues cited as having the deepest funding-arb
  liquidity) all restrict US persons — Binance suspended US futures access after its Nov 2023
  DOJ settlement, Bybit lists the US in its excluded jurisdictions, Hyperliquid geo-blocks US IPs
  and its ToS bans using a VPN to route around that [reported — coinperps.com, datawallet.com,
  hyperliquidguide.com via search]. US-accessible CFTC-regulated alternatives (Coinbase Financial
  Markets perps launched July 2025, Kraken derivatives, Kalshi's crypto perpetuals launched May
  2026) are newer, thinner markets with correspondingly less funding-rate dispersion to capture
  [reported]. This report assumes a US-based operator because the project charter's PDT-rule
  discussion implies US jurisdiction — if that assumption is wrong, re-run this section.
- Tail risk / how you lose everything: Exchange-specific collateral/oracle failure cascading into
  ADL of the "safe" leg (2025-10-10, above) — this is not a tail scenario invented for this report,
  it happened, at scale, twelve months before this research was written. Secondary tail risks:
  exchange insolvency taking both legs' collateral simultaneously (FTX 2022 is the standing proof
  this is not hypothetical), and funding-rate regime change (persistent negative funding, which
  happened during 2022's bear market, inverts the trade's core premise and can force a costly
  unwind mid-position).
- Kill test (runnable in under 1 day with free data): Pull free public funding-rate history from
  any CEX's public API (rate-limited, no key needed on most) for BTC and 10–15 mid-cap perps over
  the trailing 12 months. Compute realized annualized funding capture net of the round-trip cost
  above, assuming rebalancing every funding interval, and report the fraction of time funding was
  negative per coin. If net realized carry over the trailing year is below ~8–10% annualized after
  the 0.2–0.3% round-trip drag, or negative-funding periods exceed ~25% of the sample, the thesis
  fails at current market conditions independent of the capital-size problem above.
- Verdict: **marginal** — real edge, wrong size and partly wrong jurisdiction for this operator
  today; worth re-testing once capital clears ~$5–10k and/or a CFTC-regulated US venue's funding
  dispersion is directly measured.

### T2.2 — Cash-and-carry basis (long spot/ETF, short dated futures) captures a positive, shrinking-but-real annualized spread.

- Evidence for: Post spot-ETF-approval (Jan 2024) basis peaked at 20–25% annualized in 2024
  [reported — flowtraders.substack, coindesk via search]. A BIS working paper ("Crypto carry:
  Market segmentation and price distortions in digital asset markets," BIS Working Paper No. 1087)
  is cited as finding crypto carry decreased ~3 percentage points across exchanges and a further
  ~5pp on CME specifically after ETF introduction, via a difference-in-differences design
  [reported — cepr.org/BIS via search; the underlying PDF at bis.org was not independently
  fetched due to the egress block, so treat the specific magnitude as reported, not verified].
- Evidence against: By mid-2025 basis had compressed to roughly 10% [reported — coindesk via
  search], and a March 2025 CoinDesk piece is literally titled "U.S. BTC ETF Cash-and-Carry Trade
  Collapses" [reported]. ETF inflows "stalled" in 2025 relative to 2024, reducing the demand
  imbalance that generates positive basis in the first place [reported].
- Net-of-fee arithmetic: At even a compressed ~10% annualized basis, the arithmetic is favorable
  in percentage terms — the problem is not fees, it's minimum contract size (see below). Futures
  commissions on CME-adjacent brokers are a few dollars per contract round-trip, immaterial next
  to a $2,800+ margined position.
- Capital range where it works: **Dead at $1,000 via the regulated/CME route** — CME's Micro
  Bitcoin (/MBT) initial margin was ~$2,800 as of March 2026 [reported — multiple futures-broker
  sites via search], already 2.8x the entire account, before even funding the spot leg. The
  full-size /BTC contract needs roughly $140,000 [reported]. A retail account could in principle
  run the trade on an offshore dated-futures venue (Deribit, Binance/Bybit quarterlies) at much
  smaller size, but those are the same venues restricted for US persons discussed under T2.1.
- Data/infra required (and cost): CME data/margin is free to look up (cmegroup.com — blocked in
  this sandbox but not generally); execution needs an FCM/broker account, not unusual retail infra.
- Tail risk / how you lose everything: Basis can go negative (backwardation) around regulatory
  shocks or a spot crash faster than futures, forcing a loss on unwind; ETF-share creation/
  redemption mechanics that historically supported the trade are counterparty-dependent on the
  ETF issuer and its authorized participants, an added link most retail cash-and-carry writeups
  don't model.
- Kill test: Pull CME futures term structure (freely published) vs. spot for the last 90 days,
  compute annualized basis, and compare to the $2,800 Micro margin requirement as a share of
  account size — this alone kills the thesis at $1,000 without needing any further data.
- Verdict: **dead at current capital** (not dead as a strategy in general — revisit at
  ~$25k–50k+ where a handful of Micro contracts plus spot become a sane fraction of the book).

### T2.3 — Cross-exchange/cross-venue price dislocations remain exploitable in the long tail of smaller exchanges.

- Evidence for: Top-tier spreads have compressed to 1–2bps (from 50–100bps in 2017) [reported —
  quantt.co.uk via search], but newer/smaller-cap-token listings on second-tier exchanges (cited
  example: KuCoin) reportedly show 5–10% spreads in the first hours after a listing [reported —
  coinbureau via search].
- Evidence against: A cited 2025 Kaiko Research study found the average cross-exchange arbitrage
  window for major pairs is **under 4 seconds** [reported, via search summary only — the Kaiko
  report itself was not independently reachable]. Sources uniformly describe this space as now
  requiring "low-latency servers, direct exchange APIs... microsecond execution" — i.e., the same
  professional HFT infrastructure investment regardless of trade size, which does not fit "a
  small, technically strong solo operator" without dedicated colocation spend.
- Net-of-fee arithmetic: Cannot be made favorable without first solving latency — a 1-2bp spread
  window open for <4 seconds is smaller than most retail-accessible round-trip taker fees (0.05%
  × 2 = 10bps) unless the operator is a maker on both legs, which requires resting orders ahead
  of the dislocation, which requires the same low-latency infrastructure being argued against.
  New-listing spreads (5-10%) are large enough to clear fees but are contested by bots that also
  monitor listing announcements in milliseconds — no evidence found that a manually-coded solo
  bot without colocation can win this race with any regularity.
- Capital range where it works: Unclear/unverified either way — no source quantified minimum
  viable capital for this specific sub-strategy, which is itself a signal that solo-scale evidence
  for it is thin.
- Data/infra required (and cost): Direct exchange WS feeds on multiple venues, sub-second order
  routing, ideally colocated or cloud-region-adjacent hosting near exchange matching engines —
  ongoing infra cost, not a one-time build.
- Tail risk / how you lose everything: Being adversely selected — arriving second in the race
  means buying the spike and selling the trough, the mirror image of the intended trade, on both
  legs simultaneously, for every failed attempt.
- Kill test: Log top-of-book bid/ask across 3-5 exchanges via free public WS feeds for a week and
  measure how many cross-exchange dislocations exceed round-trip fee + realistic execution latency
  (assume 200-500ms for a non-colocated solo bot, not the sub-second figures HFT firms achieve) —
  if near-zero survive that latency haircut, the thesis is dead without further need for capital.
- Verdict: **marginal-to-dead** for a solo operator without dedicated colocation infrastructure;
  the "long tail of smaller venues" framing in the brief is plausible but unverified — no source
  found actually quantified a persistent, capturable edge there net of the infra cost to find it.

### T2.4 — Concentrated liquidity provision (Uniswap-v3-style) generates fee income that exceeds impermanent loss for a passive/lightly-managed solo LP.

- Evidence for: Concentrated ranges materially increase capital efficiency vs. full-range LPing,
  so fee APR per dollar deployed can be much higher when price stays inside the chosen range
  [reported — cyfrin.io via search].
- Evidence against: A cited Bancor/IntoTheBlock study found **over 51% of Uniswap v3 LPs were net
  unprofitable** once impermanent loss was netted against fee income [reported — search summary;
  original study not independently reached]. When price exits the chosen range the position stops
  earning fees entirely and converts fully into the worse-performing asset, which is an active-
  management problem, not a set-and-forget one.
- Net-of-fee arithmetic: Cannot be generalized — IL/fee-income math is pair- and range-specific
  and depends on realized volatility inside vs. outside the chosen band. This is the correct
  reason to distrust any blanket "X% APY" DeFi-yield marketing claim without a specific pair,
  range width, and rebalance frequency attached.
- Capital range where it works: Gas costs on L1 Ethereum historically made narrow-range active
  rebalancing uneconomical below several thousand dollars; cheap L2s (Base, Arbitrum) reduce this
  friction substantially and could make $1,000-scale LPing gas-viable — but gas cost was never the
  primary driver of the >51%-unprofitable finding above, IL was, so moving to an L2 does not fix
  the core problem.
- Data/infra required (and cost): On-chain data (subgraphs, free), a rebalancing bot/keeper
  (Gelato, or self-hosted), gas budget (small on L2s).
- Tail risk / how you lose everything: A sharp one-directional move outside the LP range converts
  the position entirely into the losing asset at the worst possible time — the "loss" is realized
  IL, not a bounded fee, and there is no equivalent of a stop-loss inside a passive LP position.
- Kill test: Backtest a specific concentrated range (e.g., ±5% around spot, weekly rebalance) on
  a liquid pair (ETH/USDC) over the trailing 12 months using free on-chain historical price/volume
  data, netting simulated fee income against IL at each rebalance — if net return is below a
  passive HODL of the same two assets, the thesis is dead for that config.
- Verdict: **marginal** — plausible only with active, frequently-rebalanced management and
  pair-specific backtesting; the base rate (>51% unprofitable) means the default case is a loss,
  not a coin flip in the LP's favor.

### T2.5 — Solo MEV extraction (arbitrage/sandwich/liquidation-bot searching) is accessible to a technically strong individual without a validator relationship.

- Evidence for: MEV is a real, measured revenue stream at the network level (ethereum.org
  documents the mechanism as structural, not a bug) [reported].
- Evidence against: "In any given week, the number of unique 'core' entities consistently winning
  bids and generating significant profit often does not exceed 20" [reported — academy.extropy.io
  via search], and on Solana specifically, the winning factor was not strategy sophistication but
  infrastructure: colocating the bot, RPC node, and validator on the same physical LAN segment
  gives a **5-10x latency reduction** over a remote cloud instance [reported — dysnix.com via
  search]. This is a direct, blunt statement that solo MEV searching without physical colocation
  is not competitive, independent of code quality.
- Net-of-fee arithmetic: Not computable as a generic edge — MEV profitability is a winner-take-
  most auction (highest bid wins the block slot), so "average" numbers are meaningless; a solo
  searcher without colocation is bidding against entities with a 5-10x latency advantage and loses
  essentially every contested opportunity.
- Capital range where it works: This does not scale down with capital — the barrier is
  infrastructure/relationship access, not position size. A well-funded solo operator faces the
  same colocation requirement as a small firm.
- Data/infra required (and cost): Colocated or validator-adjacent infrastructure, mempool/private-
  orderflow access, builder relationships — realistically a multi-thousand-dollar/month
  infrastructure commitment before the first dollar of MEV is captured, which does not fit the
  "$1,000 total capital" constraint at all.
- Tail risk / how you lose everything: Failed/reverted transactions still cost gas; being
  "backrun" by a faster searcher on your own detected opportunity is a real and common outcome.
- Kill test: Not worth a day of building — the infra barrier (colocation) is a fixed cost that
  exceeds the entire account before any backtest is needed. If the infra cost can be verified as
  lower than believed here, redo this thesis; as researched, it fails the "$1,000 capital" filter
  on infra cost alone, before touching strategy quality.
- Verdict: **dead** at current capital and infra budget — not because the edge doesn't exist at
  the network level, but because capturing it requires infrastructure investment this project's
  capital constraint rules out, independent of code skill.

### T2.6 — Crypto-specific statistical/seasonal anomalies (weekend effect, altcoin-BTC lead-lag, post-cascade mean reversion) remain tradeable.

- Evidence for (weekend effect): Weekend trading volume, volatility, and liquidity are
  consistently lower than weekday levels across multiple studies spanning 2014-2024 [reported —
  ScienceDirect/liquidity-commonality paper via search].
- Evidence against (weekend effect as a *return* anomaly): The same body of research finds **no
  detectable weekend-weekday gap in average returns** across 2016-2019, 2020-2023, and early 2024
  subsamples — "quieter weekends rather than compensating return premia" [reported — search
  summary of a paper on Bitcoin's weekend effect]. One conflicting citation (Sahu et al. 2024) is
  reported to find a weekend effect specifically during COVID — i.e., a regime-specific, not
  persistent, effect. **Net verdict: the return-premium version of this thesis appears to already
  be arbitraged away/never robustly existed; only the liquidity/volatility pattern is real, and
  that's a market-microstructure fact useful for execution timing, not a standalone alpha source.**
- Evidence for (altcoin-BTC lead-lag): Widely described qualitatively (altcoins "follow" BTC
  moves with a lag; academic spillover-effect literature confirms directional and bidirectional
  volatility spillovers exist) [reported — blockscholes, search-summarized spillover papers].
- Evidence against (altcoin-BTC lead-lag): No source found gives a clean, dated, out-of-sample
  Sharpe/return number for a lead-lag trading rule, and no source directly addresses whether this
  specific effect has been arbitraged away since 2021 — search results describe the *phenomenon*
  (altcoin rotation, altcoin-season index) but not a rigorously tested trading edge. **This thesis
  is genuinely unverified in either direction** — it needs an actual backtest before any further
  claim, positive or negative, is credible.
- Evidence for (liquidation-cascade mean reversion): The 2025-10-10 cascade (~$19B liquidated,
  70% of the damage in 40 minutes, order-book depth down >90% at the extreme, spreads widening
  from single-digit bps to double-digit percentages) is a large, real, dated microstructure event
  [reported — FTI Consulting, Amberdata, CoinGecko explainer, via search]. A separate cited paper
  ("Where does the criticality live? Early-warning signals are event-heterogeneous across seven
  crypto-perpetual liquidation cascades") reports one signal that held across all six analyzed
  cascades: "the variance of the taker buy/sell ratio falls before all six cascades" [reported —
  search summary only; note this source's host domain (arxiv.org) is explicitly blocked per this
  task's own rules, so this specific claim is flagged extra-weak — secondhand summary of a paper
  I could not read].
- Evidence against (liquidation-cascade mean reversion): The same October 2025 event is the one
  cited elsewhere in this report as the case where "safe" delta-neutral hedges were broken by ADL
  — i.e., the exact conditions that create a mean-reversion opportunity (extreme dislocation) are
  the same conditions that are most dangerous to be levered or hedged through. A retail solo
  operator attempting to "buy the wick" needs capital sitting idle and unlevered specifically to
  survive the version of this event that goes further than expected — which is capital-inefficient
  by design and directly in tension with a $1,000 account's need to deploy capital productively.
- Net-of-fee arithmetic: Not computable without a specific backtested rule; fees are not likely
  the binding constraint for a strategy that trades a few times per year around discrete cascade
  events — execution speed and having dry powder are.
- Capital range where it works: Potentially small-size-friendly in principle (a mean-reversion
  buyer doesn't need deep liquidity to place a modest order into a liquidity vacuum), which makes
  this the one thesis in this family that could plausibly fit the brief's "only works at small
  size" interest — but this is inference, not evidence; no source quantified it.
- Data/infra required (and cost): Free OHLCV + free order-book snapshots (where available) are
  sufficient for the weekend-effect and lead-lag kill tests. The cascade-reversion kill test needs
  tick-level or at least minute-level data around specific known cascade dates.
- Tail risk / how you lose everything: For lead-lag/momentum rules, the tail risk is the strategy
  degrading silently as more participants trade the same signal (the generic "alpha decay" risk,
  not a specific catastrophic one). For cascade mean-reversion, the tail risk is buying a wick that
  is not a wick — i.e., a genuine repricing (a de-peg, an exchange insolvency) rather than a
  liquidity-driven overshoot; October 2025's USDe/BNSOL/wBETH de-pegs on Binance show these two
  scenarios can be genuinely hard to distinguish in real time.
- Kill test: (a) Weekend effect: pull daily BTC/ETH returns for the last 3-5 years from any free
  OHLCV source, split by day-of-week, run a simple t-test on mean returns — expect no significant
  difference per the research above, which would confirm this specific sub-thesis is dead as
  currently understood. (b) Lead-lag: compute lagged cross-correlation of daily BTC returns
  against a basket of 10-20 large-cap alts over the last 2 years, check if a next-day-alt-return
  ~ today's-BTC-return regression has out-of-sample predictive power after fees — this is
  genuinely a same-day, free-data test. (c) Cascade reversion: identify the 5-10 largest single-day
  liquidation events in the last 3 years (dated, publicly reported), measure forward 24h/72h
  returns from the intraday low — if reversion is not both frequent and large enough to clear
  slippage on a size a $1,000 account could actually get filled at during a liquidity vacuum, the
  thesis is dead.
- Verdict: **unverified** (weekend-return-premium sub-thesis: effectively **dead**, already
  disproven by cited research; liquidity/volatility pattern: real but not a standalone edge) —
  this whole family should go through the one-day kill tests above before any further research
  time is spent on it, since it's the cheapest of the six theses to actually test rather than
  read about.

## What is definitively arbitraged away

- **Top-tier cross-exchange spreads.** 1-2bps today vs. 50-100bps in 2017 on major pairs
  [reported — quantt.co.uk via search]. The "wild edge of 2017-2021 is gone" per the same source.
- **Sub-4-second latency arbitrage for humans/non-colocated bots.** The cited Kaiko 2025 window
  (<4 seconds average) is far below any manually-triggered or even simply-coded solo bot's
  realistic reaction time.
- **A meaningful chunk of the ETF-driven basis trade's excess return.** BIS-cited research finds
  ETF introduction compressed crypto carry by ~3pp broadly and ~5pp further on CME specifically —
  the basis trade didn't disappear but institutional access via regulated ETFs ate a measurable
  slice of what used to accrue to whoever could access the trade first.
- **The weekend return premium**, if it ever robustly existed — the most recent (2024) academic
  treatment found none across a decade of data; only the *liquidity* pattern (not a return
  pattern) persists.
- **Uncontested MEV**, per the "<20 core entities per week" concentration finding — this was
  likely never accessible to a retail solo operator even at its most permissionless, but the
  degree of concentration is explicitly documented as increasing, not decreasing.

## Sources

- https://www.coinmarketcap.com/academy/article/crypto-delta-neutral-strategy-2026 — 2026 delta-neutral funding-arb yield range (10-30%), search-summarized.
- (via search) ArbitrageGhost/Medium, "Funding Rate Arbitrage in 2026" — cited 19.26% 2025 average return, <2% max drawdown, round-trip fee 0.2-0.3%, capital-viability thresholds; page itself unreachable (medium.com blocked), summary only.
- (via search) Buildix.trade blog on Hyperliquid/Binance delta-neutral arb — cited as source for "still viable in 2026" framing; page unreachable, summary only.
- (via search) NeuralArb, "Hyperliquid vs CEXs: Is Perp Arbitrage Still Worth It" (2026-04-24) — cited 3-12% BTC/ETH net APR, 20-60%+ altcoin net APR on Hyperliquid; page unreachable, summary only.
- (via search) arbiscreen.io / sharpe.ai funding-arb guides — cited $5,000-$50,000 practical capital sweet spot and $10,000-$25,000 recommended minimum working capital; pages unreachable, summaries only.
- (via search) TradingView News (Uphold research), Medium/Nicola Harvey, CoinDesk data blog, FTI Consulting, Amberdata, CoinGecko, Forbes/Insights4VC — 2025-10-10 crash details ($19B liquidated, 70% of damage in 40 min, Binance Unified Margin oracle/collateral flaw, USDe/BNSOL/wBETH de-peg, compensation window). Convergent across many independent secondary sources — higher confidence than single-source claims in this report, though still [reported] not [verified].
- (via search) flowtraders.substack.com, coindesk.com (Mar 2025 "cash-and-carry trade collapses"), cepr.org/BIS Working Paper 1087 summary — basis trade peak 20-25% (2024) compressing to ~10% (2025), BIS DiD estimate of ETF-driven carry compression.
- (via search) CME-adjacent broker sites (optimusfutures, schwab, marketswiki, stonex) — Micro Bitcoin futures ~$2,800 initial margin as of March 2026, full-size ~$140,000.
- (via search) coinperps.com, datawallet.com, hyperliquidguide.com, kalshi.com — US-person restrictions on Binance/Bybit/OKX/Hyperliquid; Coinbase Financial Markets and Kalshi as CFTC-regulated 2025/2026 US alternatives.
- (via search) Kraken support (fee schedule) — 0.02%/0.05% standard maker/taker on derivatives, funding typically -0.01% to 0.01% per 8h at the low end.
- (via search) quantt.co.uk "Crypto Quant Strategies 2026" — 1-2bps top-tier spread compression from 50-100bps in 2017; Wintermute/Jump/B2C2/Cumberland professionalization.
- (via search) academy.extropy.io MEV cross-chain analysis, dysnix.com Solana MEV infra piece — <20 core weekly MEV-profitable entities; colocation gives 5-10x latency edge over cloud.
- (via search) ScienceDirect-hosted weekend-effect and liquidity-commonality papers (titles only reachable via search snippet) — no detectable weekend return premium 2016-2024; weekend liquidity/volatility genuinely lower.
- (via search) academic paper "Where does the criticality live?" (hosted on arxiv.org, a domain this task explicitly disallows) — cited only as a secondhand claim about taker buy/sell ratio variance preceding cascades; flagged as extra-low-confidence since the source itself could not be read under this task's own rules.
- (via search) TokenTax, Schwab, KAS CPAs — Section 1256 mark-to-market/60-40 treatment for CFTC-regulated crypto futures (CME, Coinbase Derivatives); crypto spot/derivatives currently exempt from wash-sale rules under current US law (2026); crypto not eligible for §475(f) mark-to-market election since it isn't a "security."

# Retail Prop-Firm Rules — Primary-Source Survey

**Date checked: 2026-08-19.** Every figure below was read from the firm's own website or help centre on that
date unless explicitly flagged otherwise. Prop-firm rules change frequently (FTMO's Best Day Rule and
FundingPips' Profit Concentration Policy are both recent additions) — re-verify before committing money.

**Sourcing policy for this document:** no affiliate blogs, no "top 10 prop firms" review sites, no
comparison aggregators. Only firm-owned domains (`ftmo.com`, `fundednext.com`, `help.fundednext.com`,
`the5ers.com`, `help.the5ers.com`, `topstep.com`, `help.topstep.com`, `fundingpips.com`,
`help.fundingpips.com`, `tradethepool.com`, `apextraderfunding.com`, `support.apextraderfunding.com`).

**Verification levels used below:**
- **[V]** — retrieved the firm's own page directly and read the text.
- **[P]** — partially verified: the claim comes from the firm's own page as surfaced through a
  search-engine extract of that page, but direct retrieval of that specific page failed.
- **[X]** — could not verify. Stated as unknown, not guessed.

---

## 0. Executive summary for the QAPF use case

Three structural facts dominate everything else in this survey:

1. **No retail prop firm anywhere in this survey allows anything close to a 36.68% drawdown.** The
   loosest overall loss cap found is **FundingPips 2 Step Flex at 12% (static)**. The typical cap is
   6–10%. QAPF's current walk-forward max drawdown of -36.68% is roughly **3× the most permissive cap
   in the entire retail prop industry.**
2. **The daily loss limit is a tighter binding constraint than the total drawdown cap** for a
   long-only equity book. A 3–5% daily equity limit is breached by a single bad market day at full
   equity exposure. Every firm here has a daily limit of 3–5% except FundingPips' 4% and Topstep's
   optional-in-evaluation DLL.
3. **Only one firm in this survey trades real US cash equities: Trade The Pool.** FTMO offers stock
   *CFDs*; FundedNext, The5ers and FundingPips offer no stocks at all; Topstep and Apex are
   futures-only. This matters because QAPF's Agent 7/Agent 2 stack is built on US cash-equity
   cross-sectional factors.

---

## 1. Comparison table

| | FTMO (2-Step) | FTMO (1-Step) | FundedNext (Stellar 2-Step) | The5ers (High Stakes) | FundingPips (2 Step Flex) | Topstep (Trading Combine) | Apex Trader Funding | Trade The Pool (Swing) |
|---|---|---|---|---|---|---|---|---|
| **Max total loss** | 10% **static** [V] | 10% **end-of-day trailing** [V] | 10% **static** [V] | 10% **static** [V] | 12% **static** [V] | $2K/$3K/$4.5K on 50K/100K/150K — **trailing** (EOD balance, ratchets up only, locks at starting balance) [V] | Trailing threshold, e.g. $2,500 on a 50K acct — **intraday trailing incl. unrealised**, stops trailing once threshold reaches profit goal [P] | 7% max loss [V] |
| **Max daily loss** | 5% of initial balance, resets 00:00 CE(S)T [V] | 3% of initial balance [V] | 5% of initial balance [V] | 5% [V] | 4% of the higher of opening balance or equity [V] | Optional in the Combine, automatic on Live Funded [P] | None separately documented; the trailing threshold is the binding limit [P] | 3% "daily pause" [V] |
| **Profit target** | P1 10%, P2 5% [V] | 10% single phase [V] | P1 8%, P2 5% [V] | P1 10%, P2 5% [V] | P1 10%, P2 6% [V] | $3,000 / $6,000 / $9,000 on 50K/100K/150K [V] | e.g. $3,000 on a 50K acct [P] | 15% [V] |
| **Time limit** | Unlimited [V] | Unlimited [V] | No deadline; 60-day inactivity rule [V] | Unlimited [V] | Unlimited; 30-day inactivity rule [V] | No stated limit (monthly subscription) [V] | No max time; 7 trading days minimum [P] | MAX Swing 100 days; FLEX unlimited [V] |
| **Min trading days** | 4 [V] | None [V] | 5 per phase [V] | 3 profitable days (≥0.5%) per step [V] | None on the 85% split; 3 profitable days on the 95% split [V] | Not found [X] | 7 trading days [P] | 5 positions minimum [V] |
| **Instruments** | FX, indices, commodities, **stock CFDs**, crypto — all CFD/simulated [V] | same [V] | FX, indices, commodities, crypto — **no stocks** [P] | FX, metals, indices, oil, crypto — **no stocks** [V] | FX, metals, energies, indices, crypto — **no stocks** [V] | CME futures only — equity index, metals, energy, ags, FX futures, crypto futures, rates. **No forex, no equities** [V] | Futures only [P] | **Real US shares + ETFs** (12,000+ US-listed), spot, short selling available [V] |
| **Platforms** | MT4, MT5, cTrader [V] | same [V] | MT4, MT5, cTrader, Match-Trader [V] | MT5 Hedge [V] | MT5 (broker: Tradin) [V] | TopstepX + **REST API** ($29/mo, $14.50 for Topstep traders) [V] | Not verified [X] | TraderEvolution desktop/web/mobile [V] |
| **Algorithmic / EA trading** | **Allowed**, incl. EAs; hard cap of 2,000 server requests/day [V] | same [V] | **MT4/MT5 only, with an EA usage fee**; cTrader and Match-Trader are manual-only. US clients are Match-Trader-only ⇒ effectively **no EAs for US clients** [V] | **Allowed, but you must own the EA source code**; no HFT, tick scalping, arbitrage or emulators [V] | **Own EA: full automation allowed with proof of ownership.** Third-party EA: trade/risk manager only. **VPN and VPS banned** [V] | **API automation allowed**, but **VPS, VPNs and remote servers are prohibited** — all activity must originate from your personal device [V] | **Automation banned outright** — AI, autobots, algorithms, fully automated systems and HFT prohibited on all account types; only ATM (stop/target) automation exempt [P] | **Automated trading supported but in beta**, ≤2 requests/min, firm reserves approval rights [V] |
| **Overnight holding** | Yes during evaluation; on funded, Standard must flatten before weekend, **Swing account has no restriction** [V] | same [V] | Yes, at every stage; swaps apply [P] | Yes; high weekend swaps on indices/commodities [V] | Yes, evaluation and Master account [V] | **No** — flatten by 3:10 PM CT daily, no session-to-session holding [V] | **No** — close by ~4:50 PM ET, no overnight [P] | **Yes** for Swing accounts, overnight and weekends [V] |
| **Account sizes** | $10K–$200K [V] | $10K–$200K [V] | $6K–$200K [V] | $2.5K–$100K [V] | $5K–$100K [V] | $50K/$100K/$150K [V] | $25K–$300K [P] | $2K–$40K swing BP; $5K–$200K day BP [V] |
| **Cost** | €89 / €250 / €345 / €439 / €1,080 (10K/25K/50K/100K/200K), one-time, **refundable** [V] | €79 / €199 / €319 / €399 / €999, one-time, **non-refundable** [V] | $59.99 / $119.99 / $199.99 / $299.99 / $549.99 / $1,099.99 (6K–200K) [V] | From $19 (2.5K) [V]; Bootcamp advertised at $95 [P] | Not retrieved [X] | $49 / $99 / $199 per month + $149 activation, **or** $85–$95 / $129–$149 / $199–$229 per month with no activation fee (**the two Topstep pages disagree — see note**) [V] | ~$167/mo for 25K and 50K [P] | Swing: $87 (2K), $420 (10K), $670 (20K), $1,240 (40K); "Advanced" pricing lower [V] |
| **Profit split** | up to 90% [V] | 90% [V] | up to 95% [V] | 80%→100% [V] | 85% / 95% / 100% depending on reward cycle [V] | 90% [P] | Not verified [X] | 70% [V] |

---

## 2. Firm-by-firm detail

### 2.1 FTMO

Source pages: [Trading Objectives](https://ftmo.com/en/trading-objectives/),
[1-Step Challenge](https://ftmo.com/en/1-step-challenge/),
[What is the FTMO Challenge](https://ftmo.com/en/challenge/),
[Forbidden Trading Practices](https://ftmo.com/en/forbidden-trading-practices/),
[Instruments & strategies FAQ](https://ftmo.com/en/faq/which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/),
[Overnight/weekend FAQ](https://ftmo.com/en/faq/do-i-have-to-close-my-positions-overnight/),
[Best Day Rule FAQ](https://ftmo.com/au/faq/how-does-the-best-day-rule-50-work-in-ftmo-challenge-1-step/).

**Drawdown.** The 2-Step Challenge uses a **static** 10% Maximum Loss — "equity on your trading account
must not drop below 90% of the initial account balance at any given time." The 1-Step Challenge uses the
same 10% number but as an **end-of-day trailing** limit, which is materially harder [V]. Maximum Daily
Loss is 5% (2-Step) or 3% (1-Step) of the initial balance, recalculated at 00:00 CE(S)T. Note the daily
limit is measured on **equity**, i.e. it includes open unrealised P/L
([FTMO Academy — Maximum Daily Loss](https://academy.ftmo.com/lesson/maximum-daily-loss/)) [P].

**Targets and time.** 2-Step: 10% then 5%, minimum 4 trading days per phase, unlimited time.
1-Step: 10%, no minimum trading days, unlimited time, plus a **Best Day Rule** — your single best day
must be ≤50% of total positive-days profit. Breaching it is not a fail; you simply have to keep trading
until the ratio comes back in line [V].

**Instruments.** FX, indices, commodities, stocks and crypto — but FTMO states outright that its
environment "mirror[s] the conditions you would experience with a CFD (Contract for Difference)
broker," so **stocks are CFDs, not real shares**, and everything is simulated [V].

**Algo policy — the most permissive of the FX-CFD firms.** FTMO: "whether it's discretionary trading,
algorithmic trading, EAs, etc." there are "no reasons for limiting or restricting your trading
strategy," subject to a hard cap of **2,000 server requests per day** and the general ban on
latency/price-error exploitation, gap trading around scheduled news, and cross-account hedging [V].
Whether FTMO permits running an EA on a VPS was **[X] not verified** — FTMO's forbidden-practices page
does not address hosting, unlike FundingPips and Topstep which explicitly ban it.

**Overnight.** Allowed throughout the evaluation. On a funded account, Standard accounts must flatten
before the weekend and whenever rollover exceeds 2 hours; the **Swing account type has no overnight or
weekend restriction** [V]. If FTMO is used at all for a swing/systematic book, the Swing account is the
only viable variant.

**Cost.** 2-Step fees are refundable with the first reward withdrawal; 1-Step fees are **not** refunded
[P — from FTMO's own refund FAQ via search extract].

### 2.2 FundedNext

Source pages: [CFD Trading Objectives](https://fundednext.com/general-rules/cfds/trading-objectives),
[General Rules](https://fundednext.com/general-rules),
[Trading Platforms](https://fundednext.com/general-rules/cfds/trading-platforms),
[Stellar 2-Step](https://fundednext.com/cfds/stellar-2-step),
[EA policy](https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext).

**Models.** Stellar 1-Step (10% target, 3% daily, **6% static** max loss, 2 min days); Stellar 2-Step
(8% → 5%, 5% daily, **10% static**, 5 min days); Stellar Lite (8% → 4%, 4% daily, **8% static**);
Stellar Instant (no target, no daily limit, **6% trailing** max loss) [V]. No time limit; a 60-day
inactivity rule applies to all CFD accounts [V].

**Algo policy — the significant catch.** EAs and bots are permitted **only on MT4 and MT5, and carry an
additional EA usage fee**. On cTrader and Match-Trader "all trades must be executed manually" [V].
Additional constraints: max $300,000 allocation per EA strategy, each EA must run a distinct strategy,
strategies designed specifically to pass prop challenges are banned, and tools that only modify SL/TP
or lot size still count as EAs [V].

**This is the important one for a US-resident user:** FundedNext's platforms page states **US clients
are restricted to Match-Trader** — and Match-Trader is manual-only. If that combination holds, a US
client **cannot run an EA at FundedNext at all** [V for both halves; the conjunction is my inference,
flagged as such — confirm with FundedNext support before buying].

**Instruments.** FX, indices, commodities, crypto. **No stocks** [P]. Overnight and weekend holding
allowed at every stage on CFD accounts, with swaps [P]. Note **FundedNext Futures is a different product
that bans overnight holding entirely** (flat by 3:10 PM CT) [P].

**Funded-account gotcha.** A "News Reward Share Rule" claws 40% of the profit from trades executed
within ±5 minutes of listed high-impact news [P]. A systematic system with no news-blackout logic will
trip this repeatedly.

### 2.3 The5ers

Source pages: [High Stakes](https://the5ers.com/high-stakes/),
[Challenge Programs explained](https://the5ers.com/challenge-programs-bootcamp-high-stakes-hyper-growth-explained/),
[Prohibited Trading Practices](https://www.the5ers.com/faqs/prohibited-trading-practices/),
[EA FAQ](https://the5ers.com/faqs/can-i-use-an-ea-expert-advisor-can-i-set-a-stealth-mode-stop-loss/),
[Asset Specifications](https://the5ers.com/asset-specifications/).

**Programs.** Bootcamp: 3 steps × 6% target, 5% max loss per step (4% funded), 3% daily pause on the
funded stage, 1:30 leverage. High Stakes: 10% → 5%, **10% static** max loss, 5% daily loss (terminates
the account), 3 profitable days ≥0.5% per step, 1:100 leverage. Hyper Growth and Pro Growth: 1 step,
10% target, **6% static** max loss, 3% daily. Instant Funding: 6% static from day one [V].

**Drawdown mechanics.** All The5ers programs use a **static** stop-out measured from the initial
balance [V]. The daily figure is measured from the higher of the previous day's closing balance or
equity [P — the help-centre article that stated this now returns 404; the static/initial-balance half is
confirmed on the5ers.com's own program pages].

**Algo policy — a real blocker for third-party code, fine for self-built.** EAs are allowed, **but "the
trader must own the source code of the EA."** Explicitly prohibited: black-box EAs from providers,
third-party EAs where other traders hold the same trades (copy trading), HFT ("the majority of trade
durations… measured within a few seconds or less"), tick scalping, rollover scalping, and all arbitrage
variants [V]. A self-written QAPF signal generator satisfies the source-code ownership requirement.

**Instruments.** FX, metals, indices, oil/commodities, crypto. **No stocks** — The5ers points stock
traders to its sister firm Trade The Pool [V]. Platform is MT5 Hedge only [V]. Overnight and weekend
holding allowed, with high weekend swaps on indices and commodities (Crude Oil swap is quoted at -$20,
×10 on weekends) [P].

### 2.4 FundingPips

Source pages: [Trading Objectives](https://fundingpips.com/trading-objectives),
[2 Step Flex](https://help.fundingpips.com/hc/en-us/articles/47835196271249-2-Step-Flex),
[2 Step Standard](https://help.fundingpips.com/hc/en-us/articles/34501809112081-2-Step-Standard),
[Trading Conduct and Security Standards](https://help.fundingpips.com/hc/en-us/articles/34505029138449-Trading-Conduct-and-Security-Standards).

**Why it is in this survey:** the 2 Step Flex model has the **loosest overall loss cap found anywhere in
this survey — 12%, static** — combined with a 4% daily limit and 10% → 6% targets, unlimited time, and
overnight/weekend holding explicitly allowed in both the evaluation and the Master account [V].

**Static confirmed.** The 2 Step Standard help page states the mechanic verbatim: "Your equity or
balance cannot hit 10% below the starting account size at any time" — a fixed floor, not a trail [V].
2 Step Flex uses the same mechanic at 12% [V].

**Algo policy — best-in-class for a self-built system, worst-in-class for hosting.**
"If the EA is your own, developed by you, **full automation is permitted with proof of ownership**."
Accepted proof includes uncompiled `.mq4`/`.mq5` source, **version control history showing iterative
development**, development-environment evidence, or explaining the logic on a live call. "A compiled
binary on its own is not proof." Third-party EAs are permitted **only** as a trade/risk manager [V].

But: **"Connecting to a VPN or VPS while accessing your trading account is not permitted."** IP region
is logged and must stay consistent; unrealistic region changes trigger a request for a boarding pass,
passport stamp or live video [V]. Forbidden strategies include HFT, server spamming, latency arbitrage,
hedging, long-short arbitrage, tick scalping and gap trading [V].

**Other constraints.** Master accounts ≥$25K carry a **Risk Per Trade Idea** cap of 3% ($25K–<$50K) or
2% (≥$50K), and a "trade idea" groups all positions on the same instrument in the same direction
including re-entries within 10 minutes of closing a loser [V]. A **Profit Concentration Policy** applies
to evaluation accounts ≥$25K created on/after 2026-06-27: a single trade idea >60% of the profit target
forces 4 minimum profitable days on the Master account before any reward request [V]. News trading is
restricted on the Master account (±5 min around red-folder events; profits deducted) [V].

Account sizes $5K–$100K. **Prices [X] — not retrieved.**

### 2.5 Topstep

Source pages: [Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters),
[Maximum Loss Limit](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit),
[Products and hours](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade),
[TopstepX API Access](https://help.topstep.com/en/articles/11187768-topstepx-api-access),
[Prohibited Trading Strategies](https://help.topstep.com/en/articles/10305426-prohibited-trading-strategies-at-topstep),
[Pricing](https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions),
[No Activation Fee](https://www.topstep.com/no-activation-fee).

**Drawdown is trailing.** The Maximum Loss Limit "rises as your end-of-day balance grows, but never
moves down," stops trailing once it reaches the starting balance, and then locks permanently. It is
evaluated against **both realised and unrealised P&L in real time** — "if your Net P&L hits the limit at
any point during the day, your account is liquidated immediately." $2,000 / $3,000 / $4,500 on the
$50K / $100K / $150K accounts [V]. That is a **4% / 3% / 3% effective drawdown budget**, trailing.

**Targets and consistency.** $3,000 / $6,000 / $9,000. Consistency target: your best single day must
stay ≤50% of the profit target or the target increases [V].

**Instruments.** CME futures only — equity index (ES/NQ/RTY + micros), metals (gold, silver, copper),
energy, agriculture, FX futures, micro crypto, rates. **Explicitly "No Forex," and no equities** [V].

**Automation — allowed, but hosting is banned.** TopstepX API Access ($29/mo, $14.50 with the `topstep`
code) explicitly exists to "build and run automated trading strategies… execute trades directly through
your TopstepX account," with live and historical market data. But: "The use of VPS, VPNs, and remote
servers is prohibited by Topstep's Terms of Use," all activity must originate from your personal device,
"orders executed via the API are final," and Topstep provides no support for it [V]. Separately, using
"software, AI, ultra-high speed systems, or mass data entry" for unfair advantage is prohibited, as are
"scalping algorithms designed to exploit unrealistic SIM fills" [V].

**Overnight holding: not permitted.** All positions must be closed by 3:10 PM CT every weekday (risk
managers begin flattening at 3:08 PM CT); trading resumes at 5:00 PM CT; no session-to-session holding
[V]. This alone rules Topstep out for any strategy with a holding period longer than a day.

**Pricing discrepancy — flagging rather than resolving.** `help.topstep.com` gives the No-Activation-Fee
path as $95 / $149 / $229 per month; `topstep.com/no-activation-fee` gives $85 / $129 / $199. Both are
first-party pages read on the same day. Standard-path pricing agrees at $49 / $99 / $199 + a $149
activation fee per Express Funded Account earned [V]. **Treat Topstep's monthly price as approximate
until confirmed at checkout.**

### 2.6 Apex Trader Funding — ⚠️ verification caveat

**I could not retrieve any Apex page directly.** Both `apextraderfunding.com` and
`support.apextraderfunding.com` returned HTTP 403 to `WebFetch` and to `curl`, and loading them in a
browser produced: "Sorry but you are in a country that has been blocked from accessing our services."
Apex geo-blocks this location. **Everything in this section is [P]** — the wording comes from
search-engine extracts of Apex's own help-centre pages, not from pages I read directly. Independently
re-verify before acting on any of it.

Relevant Apex pages (blocked for me, may work for you):
[Prohibited Activities](https://support.apextraderfunding.com/hc/en-us/articles/40463668243099-Prohibited-Activities),
[Intraday Trailing Drawdown Evaluations](https://apextraderfunding.com/help-center/evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/),
[EOD Drawdown Explained](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-drawdown-explained/),
[All Apex Trading Account Rules](https://apextraderfunding.com/help-center/legacy-helpful-items/all-apex-trading-account-rules/),
[Futures Trading Times](https://apextraderfunding.com/help-center/getting-started/futures-trading-times/).

**Automation is banned outright — this is the decisive fact.** Per Apex's own Prohibited Activities
page: "the use of automation is strictly prohibited on all account types. This includes any form of AI
(Artificial Intelligence), Autobots, algorithms, fully automated trading systems, and high-frequency
trading (HFTs)"; "any type of hands-off, set-and-forget, or set-and-walk-away trading, including systems
that run continuously 24 hours a day, is strictly prohibited." Violation results in "immediate closure…
and the forfeiture of all funds and balances." The only exception is ATM (stop-loss / profit-target)
automation [P].

**Drawdown is intraday trailing including unrealised gains** — it "moves dynamically with your account's
highest balance (Peak Balance), including unrealized gains, and is enforced intraday at all times." It
stops trailing once the *threshold* (not the balance) reaches the profit goal [P]. Reported thresholds:
$1,500 on 25K, $2,500 on 50K, $3,000 on 100K, $3,500 on 250K, with profit goals of $1,500 / $3,000 /
$6,000 / $12,500 respectively [P]. An EOD-trailing variant also exists [P]. Minimum 7 trading days, no
maximum time [P]. Futures only; overnight holding not permitted (close by ~4:50 PM ET) [P].

### 2.7 Trade The Pool — the only real-equities firm found

Source pages: [Program Terms](https://tradethepool.com/program-terms/),
[The Program](https://tradethepool.com/the-program/),
[Markets](https://tradethepool.com/markets/).

Sister firm of The5ers, focused entirely on **US cash equities**. This is the one firm in the survey
whose asset class matches what QAPF actually trades today.

**Instruments.** "Almost any stock and ETF in the U.S. markets" — 12,000+ US-listed stocks and ETFs,
"spot trading — meaning you are trading actual stock and ETF prices," not CFDs. Short selling is
supported. Index futures (ES/NQ) are not offered, but their ETF equivalents are [V]. Overnight session
access is via the Blue Ocean ATS [V].

**Programs.** Day trading: 6% profit target, 1–2% daily pause, 3–4% max loss, 10–20 minimum positions,
buying power $5K–$200K intraday (with reduced overnight BP). Swing trading: **15% profit target, 3%
daily pause, 7% max loss**, 5 minimum positions, $2K–$40K buying power [V]. Evaluation windows: MAX Day
60 calendar days, MAX Swing 100 calendar days, **FLEX unlimited** [V]. Profit split 70/30 [V].

**Overnight/weekend.** Swing accounts hold overnight and over weekends during both evaluation and funded
phases [V]. Day accounts are auto-liquidated 10 minutes before the close [V]. Corporate-action rules
apply and are unusually strict for a systematic book: **no overnight positions in companies reporting
earnings**, all positions closed before an announced split, and positions must be closed before the
ex-dividend date [V]. A US cash-equity strategy holding a broad cross-section will hit earnings dates
constantly — this needs an explicit earnings-calendar filter in the portfolio agent.

**Automation.** Supported but explicitly **in beta**: "no more than 2 requests/min," the firm "reserves
approval rights for algorithms," may "request or require adjustments to make any automation less
demanding," and availability "is not guaranteed" [V]. 2 requests/minute is workable for a daily-rebalance
system and unworkable for anything intraday.

**Cost.** Swing: $87 (2K BP), $420 (10K), $670 (20K), $1,240 (40K) at "Beginner" pricing, less at
"Advanced". Day: $59 (5K) up to $1,475 (200K) [V].

---

## 3. Things I could not verify

- **Apex Trader Funding: everything.** Geo-blocked from this location on both domains. Section 2.6 is
  entirely [P].
- **FundingPips pricing.** The account sizes are on the trading-objectives page; the fees are not, and I
  did not reach a checkout page.
- **FTMO's VPS policy.** FTMO's forbidden-practices page does not mention hosting either way. Given that
  both FundingPips and Topstep explicitly ban VPS, FTMO's silence should not be read as permission
  without asking them.
- **The5ers' exact daily-drawdown reference point.** The help-centre article that documented
  "previous day's closing equity or balance, whichever is higher" now 404s.
- **Topstep monthly pricing.** Two first-party pages give different numbers (see 2.5).
- **Topstep minimum trading days.** Not stated on the parameters page.
- **Whether the FundedNext US-client restriction genuinely forecloses EAs.** Both facts are separately
  confirmed on FundedNext's own pages; the conclusion that they combine to block US algo traders is my
  inference and needs confirming with the firm.
- **Whether any of these firms would treat a multi-agent LLM system as "AI" under an anti-AI clause.**
  Topstep prohibits "software, AI, ultra-high speed systems… that manipulates, abuses, or provides an
  unfair advantage"; Apex bans "any form of AI." Neither defines the term. QAPF is exactly the kind of
  system a compliance team might read into that language. This is an open legal-interpretation risk, not
  a resolved fact.

---

## 4. Implications for QAPF

### 4.1 The arithmetic that rules almost everything out

QAPF's backtested max drawdown is **-36.68%**. The most permissive total-loss cap in this survey is
**12% static** (FundingPips 2 Step Flex). Percentage drawdown is scale-invariant — trading smaller lots
does not shrink it. The only lever that does is **de-levering**: deploying only a fraction *k* of the
account into the strategy and holding the rest in cash, which scales both drawdown and return by
approximately *k*.

That produces the real test. To survive a cap of *D* and still reach a target of *T*, you need

> *T* / *D* ≤ (strategy return over the evaluation horizon) / (strategy max drawdown)

i.e. **the strategy's MAR-like ratio over the evaluation window must beat the firm's target-to-drawdown
ratio.** Computed from the table:

| Firm / model | Target ÷ max loss (Phase 1) | Effective de-levering *k* to fit the cap with 20% headroom |
|---|---|---|
| FundingPips 2 Step Flex | 10 / 12 = **0.83** | ~0.26 |
| FTMO 2-Step | 10 / 10 = 1.00 | ~0.22 |
| The5ers High Stakes | 10 / 10 = 1.00 | ~0.22 |
| FundedNext Stellar 2-Step | 8 / 10 = **0.80** | ~0.22 |
| The5ers Bootcamp | 6 / 5 = 1.20 | ~0.11 |
| Topstep 50K | 3,000 / 2,000 = 1.50 (and trailing) | n/a |
| Apex 50K | 3,000 / 2,500 = 1.20 (and intraday trailing) | n/a |
| Trade The Pool Swing | 15 / 7 = **2.14** | ~0.15 |

**FundedNext 2-Step and FundingPips 2 Step Flex have the friendliest ratios; Trade The Pool's swing
program has by far the worst** (15% target against a 7% cap), which is ironic given it is the only firm
whose asset class matches QAPF's.

At *k* ≈ 0.22–0.26 the strategy would need an annualised return above ~40% *before* de-levering to clear
a 10% phase target inside a plausible evaluation window. QAPF's walk-forward numbers should be checked
against that bar directly (`backend/agents/backtest/walkforward.py` output) before spending anything.

### 4.2 The daily loss limit is the harder constraint, and it is not currently modelled

Every firm here enforces a **3–5% daily equity limit measured intraday, including unrealised P&L**. A
long-only US equity book at full exposure breaches a 5% daily limit on any single -5% index day; at 4%
(FundingPips) or 3% (FTMO 1-Step, The5ers Hyper Growth) the margin is thinner still.

QAPF's CRO (`backend/risk/`) currently implements VaR/CVaR, drawdown tracking and a kill-switch, but the
kill-switch thresholds `max_drawdown_pct` / `max_daily_loss_pct` are deliberately left unset in
`backend/risk/__main__.py`. **A prop-firm deployment turns those from a risk-appetite decision into a
hard external constraint**, and the daily one has to be enforced on intraday equity, not on end-of-day
marks — which QAPF does not currently compute, because Agent 9 backtests on daily bars.

### 4.3 Ruled out, and why

- **Apex Trader Funding — ruled out unconditionally.** Automation is banned on all account types in
  Apex's own words, including "algorithms" and "systems that run continuously 24 hours a day." QAPF is
  precisely the prohibited category. Also futures-only, no overnight holding, and intraday-trailing
  drawdown including unrealised gains — the single most hostile drawdown mechanic in the survey for a
  systematic book.
- **Topstep — ruled out on holding period, not on automation.** Topstep is unusual and commendable in
  offering a documented REST API for automation. But positions must be flat by 3:10 PM CT with no
  session-to-session holding, which is incompatible with any multi-day factor strategy; it is
  futures-only with no equities and explicitly no FX; the MLL is trailing and evaluated intraday on
  unrealised P&L; and the VPS/VPN ban means the system must run on the user's own machine. Viable only
  if QAPF were rebuilt as an intraday futures strategy — a different project.
- **Trade The Pool — right asset class, wrong risk budget.** It is the only firm trading real US shares,
  supports short selling, allows swing overnight/weekend holding, and permits automation. But a 15%
  target against a 7% max loss is the worst ratio in the survey; the API is capped at 2 requests/minute
  and is in beta with discretionary approval; buying power for swing accounts tops out at $40K; and the
  mandatory earnings/split/ex-dividend closeouts require calendar logic QAPF does not have. **Best
  candidate for a proof-of-concept, worst candidate for the economics.**
- **FundedNext — conditionally ruled out, pending one fact.** Good ratio (8% ÷ 10% static), overnight
  and weekend holding allowed at every stage, no time limit. But EAs run on MT4/MT5 only, carry a usage
  fee, and **US clients appear to be restricted to Match-Trader, which is manual-only.** Confirm
  residency treatment with FundedNext before considering it. No stocks — FX/indices/commodities/crypto
  only.

### 4.4 The two that could plausibly work

- **FundingPips 2 Step Flex** — the most permissive total loss cap found (12% static), 4% daily, 10% →
  6% targets, unlimited time, overnight and weekend holding allowed at both stages, and — uniquely —
  **full automation explicitly permitted for an EA you wrote yourself, with git history accepted as
  proof of ownership.** QAPF's repo is literally that proof. The blockers are structural rather than
  legal: it is **MT5-only** (a Python/LangGraph stack needs an MQL5 or bridge layer), offers **no
  equities** (so QAPF's cash-equity factor pipeline does not transfer — Agent 7's momentum/reversal/
  low-vol factors would have to be re-derived on FX/metals/indices), the **VPS/VPN ban** means the
  system must run on the user's own hardware from a stable IP, and the Master-account **Risk Per Trade
  Idea cap of 2–3%** constrains position sizing in a way Agent 2's optimiser does not currently model.
- **FTMO 2-Step (Swing account on the funded stage)** — 10% static max loss, 5% daily, 10% → 5%,
  unlimited time, refundable fee, MT4/MT5/cTrader, and the **clearest pro-algorithmic policy of any firm
  here**: algorithmic trading and EAs are named as explicitly acceptable, with the only quantified limit
  being 2,000 server requests/day (trivially satisfied by a daily-rebalance system). FTMO is also the
  only firm offering **stock CFDs**, so QAPF's equity factor signals could at least be expressed
  directionally, albeit as CFDs with financing costs rather than real shares. Two conditions: the
  **Swing account type is mandatory** if positions are to survive weekends on the funded stage, and the
  **1-Step product must be avoided** because its 10% max loss trails end-of-day.

### 4.5 Recommended next steps

1. **Compute QAPF's return-over-max-drawdown across the walk-forward windows** and compare against the
   0.80–1.00 target-to-drawdown ratios in 4.1. If the ratio does not clear ~1.0 with headroom, no prop
   firm in this survey is viable at any position size and the question is settled on arithmetic alone.
2. **Set `max_drawdown_pct` and `max_daily_loss_pct` in `backend/risk/__main__.py`** to the tightest
   candidate firm's numbers (FundingPips: 12% / 4%) and re-run the backtest with the CRO kill-switch
   live, to see how often the strategy would have been terminated. This is a concrete, cheap experiment
   the existing code supports today.
3. **Add intraday equity tracking to the CRO** — every firm's daily limit is evaluated on intraday
   equity including unrealised P&L, and QAPF currently reasons in daily closes only. Without this, any
   backtested "pass" is optimistic.
4. **Before paying for anything**, confirm directly with the firm: (a) FTMO's VPS policy; (b) whether
   FundedNext's US clients can use EAs; (c) whether a multi-agent LLM system falls foul of any
   "AI / unfair technology" clause. That last one is genuinely unresolved industry-wide and is the
   biggest non-quantitative risk to this whole plan.
5. **Treat the whole prop-firm route as a capital-efficiency question, not a validation question.**
   Every firm here operates a *simulated* environment (FundingPips states outright: "All accounts
   provided by FundingPips are demo accounts operating exclusively in a simulated trading environment.
   No actual trades are executed on live financial markets"). Passing an evaluation validates
   risk-limit compliance, not execution quality — Agent 11's impact model and Agent 12's reconciliation
   would still be untested against real fills.

# Position Sizing and Risk Limits — Primary-Source Survey

**Date checked: 2026-08-19.** This document exists to set two numbers that are currently `None` in
`backend/risk/__main__.py`: `max_drawdown_pct` and `max_daily_loss_pct`. It is written to the same
standard as `docs/research/prop-firm-rules.md` — every claim is tagged with a verification level and a
citable source, because this feeds a decision about $1,000 of real money.

**Verification levels used below (same convention as `prop-firm-rules.md`):**
- **[V]** — read the primary source directly (the author's own blog, the repo's own code, a paper's own
  text).
- **[P]** — partially verified: secondary summary of a primary source (a book review, a paywalled book's
  content surfaced through a practitioner summary or search extract), or a primary source whose full
  text I could not retrieve.
- **[X]** — could not verify; stated as unknown, not guessed.

**Sourcing honesty up front:** Vince's *The Mathematics of Money Management* and *The Leverage Space
Trading Model*, and Kaufman's *Trading Systems and Methods*, are not available to me as full text —
no free legal full-text source was found (not on archive.org's lending library in a form I could open,
not on Google Books preview beyond a few pages). Everything attributed to those three books below is
**[P]**: secondary summaries, practitioner reviews that quote specific passages, or an interview with
the author in his own words. Carver's book and blog, Chan's blog, and the repo's own source code are
**[V]** — I read those directly. This gap matters and is flagged again in §7.

---

## 0. Executive summary

1. **The repo's kill-switch is a binary, stateless, non-enforcing threshold check today, not a
   graduated de-risking mechanism.** It compares peak-to-current drawdown and the latest single day's
   return against two flat percentages and returns a boolean. Nothing in the codebase currently *acts*
   on that boolean — no execution-blocking wiring exists yet (`backend/risk/monitor.py:15-64`,
   confirmed by grep — see §1.3). Today's decision is "what number to report against," not yet "what
   number stops an order."
2. **The literature does not converge on one instrument.** Vince and Kaufman [P] think in terms of
   position-size fractions calibrated to a worst historical loss (optimal f); Carver [V] explicitly
   rejects a fixed drawdown-percentage halt in favor of continuous volatility-targeted position scaling;
   de Prado [P] and the Research Affiliates/Syzygy paper [P] treat stop-rules as a defensible but
   separate risk-premium layer; Varma [V, blog] argues naive fixed-percentage stops can *destroy* more
   capital than they save via "death by a thousand cuts." These are genuinely different, not
   reconcilable into one number — see §5.
3. **At $1,000 across 14-15 whole-share US large-caps, none of the textbook sizing formulas apply
   mechanically.** Real August 2026 prices for this exact universe (`backend/agents/portfolio/__main__.py:24-28`)
   run from ~$87 (KO) to ~$493 (MSFT) — see §4. Equal-weighting $1,000 over 15 names is $66.67/name,
   which cannot buy one share of 9 of the 15 tickers. Optimal-f, Kelly, and vol-targeting all output a
   *continuous* capital fraction; whole-share rounding at this size turns that continuous fraction into
   a coarse, often-zero, integer decision the formulas were never designed to survive.
4. **Recommendation:** `max_drawdown_pct = 0.20`, `max_daily_loss_pct = 0.06`. Reasoning chain in §6.
   Both sit strictly inside the two measured anchors (15% halted on ordinary Q4 2018 volatility, 25%
   halted the day before the COVID snap-back) and are argued from the literature's actual disagreements,
   not split the difference by default.
5. **Keep the hard halt for now, but flag it as the wrong long-run mechanism.** §7 explains why: the
   literature's own preferred alternative (continuous vol-targeting/de-risking, per Carver) requires
   machinery — an intraday risk-scaling loop, position-level vol-adjusted sizing — that QAPF does not
   have yet, and a solo operator with $1,000 and no ability to watch the account intraday needs a rule
   simple enough to be mechanically enforceable without discretion. That is a deliberate, cited
   trade-off, not an oversight.

---

## 1. What the repo actually does today (read from source)

### 1.1 The two numbers and what happens once they're set

`backend/risk/__main__.py:164-165`:

```python
max_drawdown_pct = None  # e.g. 0.20 for "halt at 20% drawdown from peak"
max_daily_loss_pct = None  # e.g. 0.05 for "halt on any single day worse than -5%"
```

Confirmed deliberately unset — `__main__.py:167-172` explicitly checks for `None` and prints an
instruction to set them rather than defaulting, then returns without ever constructing a `RiskMonitor`.
Once both are set, `main()` (`__main__.py:174-177`) constructs `RiskLimits(max_drawdown_pct=...,
max_daily_loss_pct=...)`, calls `RiskMonitor(limits).assess(daily_returns)` on the real 2018-2020
walk-forward return series produced by Agent 9's backtest, and prints the resulting `RiskAssessment` as
JSON. That is the entire consuming code path today — a single as-of-the-last-date assessment printed to
stdout. It is *not* wired into `backend/agents/execution/` to block an order, and no other agent's
`__main__.py` imports `RiskMonitor` (checked by grep across `backend/agents/` — no hits). **The
kill-switch currently reports; it does not yet enforce.**

### 1.2 The metric definitions (`backend/risk/metrics.py`)

- `drawdown_series` (`metrics.py:43-46`): standard peak-to-current — `equity = (1+returns).cumprod()`,
  `running_max = equity.cummax()`, drawdown `= (equity - running_max) / running_max`. This is drawdown
  from the running historical peak, not from account inception and not a fixed lookback window.
- `max_drawdown` (`metrics.py:49-50`) — the worst point in that series — is computed but, per §1.3
  below, is **not** what the kill-switch actually compares against; it's reported for information only.

### 1.3 The kill-switch mechanics (`backend/risk/monitor.py`)

`RiskMonitor.assess()` (`monitor.py:19-64`):
- `current_dd = dd_series.iloc[-1]` — the drawdown **as of the last observation in whatever slice is
  passed in**, not the all-time worst (`worst_dd` is computed separately at `monitor.py:29` and reported
  in the output, but never compared against a limit).
- Breach test: `if abs(current_dd) >= self.limits.max_drawdown_pct` (`monitor.py:35`). This is a
  **level check on current peak-to-date drawdown, not a rate-of-change or duration test.**
- `latest_return = returns.iloc[-1]` (`monitor.py:30`) — the single most recent bar's return.
- Breach test: `if latest_return < 0 and abs(latest_return) >= self.limits.max_daily_loss_pct`
  (`monitor.py:41`). This only fires on a genuinely negative day; a return of exactly the limit or worse
  trips it.
- **No explicit "reset" logic exists for the daily check** — there is no stored state between calls.
  Each call to `assess()` looks only at the last row of whatever `returns` series is handed to it, so
  the "reset" is implicit in the caller passing a fresh daily bar each day. This also means the daily
  check is evaluated **once per day on a close-to-close bar**, not intraday and not on unrealized
  mark-to-market — a materially looser mechanic than the prop-firm daily-loss rules surveyed in
  `docs/research/prop-firm-rules.md` (§0 point 2 there: "every firm's daily limit is evaluated on
  intraday equity including unrealised P&L"). If QAPF ever needs to match an external daily-loss
  covenant, this gap has to close first; for a personal-capital deployment with no external covenant,
  a close-to-close check is the honest reading of what a daily-rebalance system can even measure.
- `kill_switch_triggered = len(breaches) > 0` (`monitor.py:62`) — a pure boolean OR of the two
  independent tests. **There is no partial/graduated response** — no position scaling, no soft
  de-risking step. It's binary: triggered or not.
- `assess_history()` (`monitor.py:66-71`) re-runs `assess()` at every date using only data up to that
  date, which is what produced the two anchor data points in the prompt (`__main__.py:131-145`,
  `show_kill_switch_tradeoff`): a 15% limit and a 25% limit run against the real COVID-era backtest
  return series.

**Net mechanical picture:** this is a stateless, hard, binary, peak-to-current level check, run once per
day on close-to-close returns, that currently only prints a verdict and is not yet wired to stop an
order. Everything in §§2-7 below is about what number to put in it and whether "binary halt" is even the
right instrument once/if it is wired up.

---

## 2. The literature, author by author

### 2.1 Ralph Vince — optimal f and the asymmetry of overbetting [P]

Vince's own framework (*Portfolio Management Formulas*, *The Mathematics of Money Management*, later
*The Handbook of Portfolio Mathematics* and *The Leverage Space Trading Model*) computes **optimal f**:
the fraction of capital per bet that maximizes the geometric growth rate (Terminal Wealth Relative) of a
trade sequence, given the historical worst loss. This is Vince's own Kelly-family formula, calibrated to
*trade-level* worst-case loss rather than win/loss probabilities directly.

**The load-bearing point requested — asymmetry above vs. below optimal f — verified across two
independent secondary sources**, including Vince's own words in interview:

> "Below the peak, you are under-leveraged. Above the peak, you are over-leveraged and growth declines
> — dramatically so as you approach full exposure."
> — Ralph Vince, quoted in the *Better System Trader* interview [P — interview summary, phrasing
> attributed directly to Vince] (episode 011, https://bettersystemtrader.com/011-ralph-vince/)

The TWR-vs-f curve is not symmetric around its peak: it rises smoothly on the under-betting side and
falls off a cliff on the over-betting side, because the compounding penalty from a large loss (a −50%
drawdown needs +100% just to recover; see the mechanical point in §2.6) grows faster than the marginal
gain from a slightly larger bet. This is why Vince and every serious secondary source on him ("For
traders with any constraint on drawdown or volatility, the answer is a fraction of Optimal f" — echoed
across multiple summaries) converge on *fractional* f (e.g., half-f or quarter-f) as the practically
usable version, never full optimal f. Vince illustrates the real-world violence of trading at/near
optimal f with Larry Williams's 1987 Robbins World Cup performance — turning $10,000 into over $1
million while enduring an intra-year drawdown Vince describes as on the order of a 900% notional
retracement of gains, i.e., full-optimal-f growth is not survivable psychologically or in
capital-preservation terms even when it "worked" **[P, from the same interview]**.

**Vince's own quantitative heuristic for position sizing without full optimal-f machinery** (relevant
directly to a small, simple account): "Take your probability of winning, divide by two, then divide your
largest loss by that result" — his words, per the same interview **[P]** — with the explicit caveat that
this still produces "very wild swings." This is *not* what QAPF should implement as-is (it's a per-trade
heuristic for a single-instrument system, not a 15-name cross-sectional book), but it is direct evidence
that Vince himself treats his own formula's raw output as too aggressive for practical use without
further shrinkage.

**Structural limitation, independently confirmed:** optimal f is anchored to the largest historical loss
observed in-sample. The moment live trading produces a new worst loss — which markets do regularly — the
calibration is stale and the "optimal" fraction was optimal for a distribution that no longer describes
the live one. Multiple secondary sources converge on this critique independently of each other
**[P]** (turtletrader.com's review; the QuantPedia summary). This is directly relevant to QAPF: the
strategy's known max drawdown (−36.68%, 2018-2020 walk-forward) is itself an in-sample worst case that a
live 2026+ deployment could exceed.

### 2.2 Robert Carver — volatility targeting, and explicit small-account guidance [V]

Carver's *Systematic Trading* replaces a fixed-drawdown-halt mentality with **continuous volatility
targeting**: pick an annualized standard-deviation target for the portfolio, size every position so the
book's realized/forecast volatility tracks that target, and let position size fall automatically as
realized volatility rises (and rise as it falls) — a *soft, continuous* de-risking mechanism rather than
a binary halt. This is explicitly the alternative the prompt asked me to evaluate against a fixed
drawdown percentage.

**Numeric small-account guidance, read directly from Carver's own blog, qoppac.blogspot.com** — this is
the first-party primary source the operator specifically asked me to check, and it gives concrete
numbers not in the book summaries:

- *"Diversification and small account size"* (https://qoppac.blogspot.com/2016/03/diversification-and-small-account-size.html)
  **[V]**: Carver gives explicit capital thresholds for how many instruments a systematic account can
  meaningfully diversify across — roughly **$2,500 for one instrument**, **$5,000 for two with
  thresholding**, **$100,000 for eight instruments without thresholding**, up to **$3.25 million for 37
  instruments at a minimum of 3 contracts each**. His own words: *"you're probably better off using a
  binary or thresholded forecast filter with as wide a range of instruments as you can manage, at least
  until you have $100K or so."* He states a **minimum of ~4 contracts at maximum forecast** as the
  threshold below which position sizing granularity itself materially damages the strategy, and quantifies
  the cost of forcing sub-scale diversification via thresholding at **roughly a 20% Sharpe-ratio penalty**
  versus running the full, properly-scaled version. His summary framing: *"you're caught between the
  devil of fractional contracts and the deep blue sea of insufficient diversification."**
- *"Vol targeting: A CA(g)R race"* (https://qoppac.blogspot.com/2022/06/vol-targeting-cagr-race.html)
  **[V]**: Carver's central empirical claim is that vol-targeted position sizing produces materially
  higher compound annual growth than static sizing at the same nominal risk, because it avoids being
  overexposed exactly when volatility (and typically correlation and downside risk) is highest. He does
  not propose a fixed drawdown-percentage halt anywhere in this framework — position size is a continuous
  function of trailing realized volatility, not a step function that flips off at a threshold.

**Carver's stated risk-target framing (from secondary summaries of the book, consistent with the primary
blog posts above) [P for the exact number, V for the underlying mechanism]:** Carver ties the volatility
target to the strategy's own expected Sharpe ratio — a system with an expected Sharpe of ~0.25 might run
at a 25% annualized-vol target — and separately recommends **half-Kelly, not full Kelly**, as his
practical ceiling, for the same overbetting-asymmetry reason Vince gives in §2.1.

**Direct answer to the prompt's core instrument question:** Carver's own published framework is explicit
that position size should be a **continuous function of realized/forecast volatility**, adjusted
constantly, not a binary account-level halt triggered at a fixed drawdown percentage. He does discuss
maximum-drawdown *statistics* as an output/consequence of a chosen risk target (higher targets produce
proportionally worse max drawdowns), but he does not advocate a hard stop-trading rule as his primary
risk-control instrument the way QAPF's CRO currently implements one.

**Applicability to QAPF's $2,500-threshold-per-instrument guidance and a $1,000/15-name book:** Carver's
own numbers put a *single*-instrument systematic account at a **$2,500 minimum** and treat sub-scale
diversification below that as materially Sharpe-damaging. QAPF proposes 14-15 instruments on $1,000 —
roughly 6-8x below Carver's stated minimum *per instrument he'd recommend holding at all*, and nowhere
close to the ~$100K he names as the point where diversification across ~8 instruments stops requiring
thresholding tricks. This is direct evidence, from the specific source the operator asked me to check,
that Carver's own vol-targeting machinery is **not mechanically appropriate at this account size and
name count** — it was designed and calibrated for accounts one to two orders of magnitude larger. See
§4 for the concrete whole-share consequence.

### 2.3 Perry Kaufman — *Trading Systems and Methods* [P — could not access full text]

I could not obtain the primary text (paywalled; no accessible preview covering the relevant chapter).
Multiple independent secondary sources (a dedicated book review site, an O'Reilly/Wiley catalog
description, and a document excerpt search) converge on the same chapter structure: **Chapter 23,
"Risk Control,"** covers leverage, individual-trade risk sizing, stop placement, market ranking, and
"investing and reinvesting using optimal f" as one of several sizing frameworks presented side by side
rather than endorsed exclusively **[P]**. Kaufman is described consistently as treating risk control as
inseparable from position sizing rather than a bolt-on afterthought, and as presenting optimal f
alongside — not instead of — simpler fixed-fractional and volatility-based methods. I was not able to
extract Kaufman's own numeric recommendations or his explicit stance on hard halts vs. de-risking from
these secondary sources; **flagging this as a real gap** rather than inventing a position for him. Given
that gap, Kaufman is not used as a load-bearing source for the final numeric recommendation in §6 —
only Carver [V] and Vince [P, but corroborated across multiple independent secondary sources plus his
own interview words] carry that weight, with de Prado and the Research Affiliates paper as secondary
support.

### 2.4 Ernie Chan — Kelly-based drawdown-limiting, read from his own blog [V]

Chan's blog post, *"How do you limit drawdown using Kelly formula?"*
(http://epchan.blogspot.com/2010/04/how-do-you-limit-drawdown-using-kelly.html) **[V, read directly]**
gives a specific, actionable mechanism that is directly relevant to reconciling "use Kelly/optimal-f
sizing" with "also want a hard drawdown ceiling" — the exact tension the prompt raises between Vince's
approach and a kill-switch:

> "Kelly formula won't prevent a deep drawdown, though we are assured that the drawdown won't be as much
> as 100%. ... Suppose the optimal Kelly leverage of your strategy is determined to be K. And suppose you
> only allow a maximum drawdown ... to be D%. Then you can simply set aside D% of your initial total
> account equity for trading, and apply a leverage of K to this sub-account."

Mechanically: overall effective leverage becomes `K × D`, the remainder `(1-D)` sits in cash as a hard
floor, and the sub-account is rebalanced back to `D%` of total equity as equity marks new highs. This is
a **hybrid** of Vince's fractional-Kelly sizing and a hard capital-preservation floor — closer in spirit
to Carver's continuous scaling than to QAPF's current binary halt, because the "floor" is enforced by
capital allocation (only D% of the book is ever at risk) rather than by a stop-everything trigger at a
threshold. Chan elsewhere (secondary-sourced, consistent across the search results) recommends **1/4 to
1/2 Kelly** as the practically used range across quant funds, for the same estimation-error and
overbetting-asymmetry reasons Vince and Carver both give — a third independent voice converging on
fractional, not full, aggressive sizing.

### 2.5 Marcos López de Prado — bet sizing and structural-break detection [P — secondary summaries]

*Advances in Financial Machine Learning*, Chapter 10 ("Bet Sizing") **[P]**: de Prado sizes bets as a
continuous function of a classifier's *predicted probability* that a signal is correct, not a fixed
fraction per position — closer in spirit to Carver's continuous scaling than to a flat per-name
percentage. I could not obtain his exact formula and worked numeric example from primary text; treat this
as directionally confirmed (probability-scaled sizing exists and is his approach) but not numerically
verified.

Chapter 17 ("Structural Breaks") **[P]**, directly relevant to the prompt's sub-question 3 (statistically
distinguishing a broken strategy from normal variation): de Prado presents two families of tests —
**CUSUM tests**, which check whether the cumulative sum of recursive one-step-ahead forecast errors
deviates from white noise (a live, real-time-computable version of change-point detection, not a
retrospective one), and **explosiveness tests** (e.g., supremum Augmented Dickey-Fuller), which test
whether a series is behaving in an unsustainable, non-stationary way. Directionally, this is the closest
thing the literature offers to a "principled statistical test" for distinguishing a regime break from
normal variation — **but it is a test for a break in the price/return process being traded, not a
validated test for "has my specific strategy's edge broken."** I found no primary or secondary source
that applies de Prado's CUSUM/explosiveness machinery directly to a live-vs-backtest strategy P&L
comparison (e.g., "is this drawdown outside the backtest's own historical drawdown distribution at some
confidence level") — that specific, more targeted test does not appear to be a standard, named tool in
the literature I could locate. **This is a real gap, not a citation I'm withholding**, and it directly
answers part of sub-question 3: no, there is no clean, off-the-shelf statistical test in the sources
surveyed for "is this drawdown broken-strategy or normal-variation" — CUSUM/SPRT-family tools exist for
detecting a change-point in a *process*, and could in principle be pointed at a live return stream
compared against a backtest reference distribution, but I found no author treating that construction as
established or validated. Building it would be original work, not literature-application.

**Sequential Probability Ratio Test (SPRT)** — searched directly per the prompt's suggestion. SPRT is a
well-established sequential hypothesis-testing framework (accumulate evidence, stop as soon as a
likelihood-ratio threshold is crossed either way, with no penalty for continuous "peeking" — a real
advantage over fixed-sample tests for live monitoring) **[V for the general statistical method — this is
textbook sequential-analysis theory, not attributed to a specific trading-book author]**. I found no
primary or credible secondary source applying SPRT specifically to "has my live trading strategy's
edge disappeared" monitoring, despite a targeted search. It is a mechanically plausible tool (frame the
null as "true edge matches the backtest's return distribution," the alternative as "edge has degraded
below some threshold," and monitor sequentially) but I am not aware of it being validated for this
specific use in the literature, so I am not recommending building it now — flagged as a candidate for
future work, not as an established practice to adopt today.

### 2.6 The two-sided empirical view on drawdown-based stop rules

**Against fixed-threshold halts — Samir Varma, "The Stop-Loss That Stops Gains"** [V, read directly]
(https://samirvarma.substack.com/p/the-stop-loss-that-stops-gains): argues mechanical, fixed-percentage
drawdown rules can produce a "death by a thousand cuts" pattern — repeatedly cutting a losing position at
a threshold, missing the subsequent recovery, re-entering, and cutting again — that in aggregate can
destroy more capital than tolerating one larger drawdown that would have mean-reverted. His own numeric
illustration is exactly the anchor pattern in this prompt: SPY's Feb 21–Mar 23, 2020 COVID crash (−33%
max drawdown, −99% annualized over that window) is the canonical case where a threshold rule locks in the
loss right before the snap-back — structurally the same failure mode as QAPF's own measured 25%-halt
result on 2020-02-27. His proposed alternative is not "no rule," but **context-aware, cross-asset-confirmed,
regime-dependent thresholds** rather than one flat static percentage — directionally consistent with
Carver's continuous approach, though less formally specified.

**For stop rules, as an established risk-premium technique — Research Affiliates/Syzygy Asset
Management, "Stop the Losses!"** (Jim Masturzo, CFA and Jay Jeon, October 2025,
https://www.syzygyassetmanagement.com/insights/publications/articles/1099-stop-the-losses) **[P — the
page's full analysis sits behind a PDF download I could not retrieve; only the abstract-level framing was
accessible]**: the paper's own stated thesis is that "stop losses help mitigate downside risk by limiting
behavioral biases and reducing drawdowns and skewness for both alternative risk premia and
trend-following strategies" — i.e., a reputable quantitative-research shop's institutional position is
that stop-loss/drawdown rules are a *defensible, evidence-based* risk-management layer, not merely a
retail behavioral crutch. I could not extract their specific numeric thresholds or backtested results, so
this is cited for its institutional position on the general question (rules can help), not for a specific
number.

**The honest synthesis of §2.6:** the literature genuinely disagrees on whether fixed-threshold rules
help or hurt, and the disagreement tracks *what the rule is protecting against*. Varma's critique targets
naive, static, single-threshold rules applied blindly across regimes. The Research Affiliates/Syzygy
position defends stop rules specifically in the context of "alternative risk premia and trend-following
strategies" — a different edge structure than QAPF's cross-sectional factor book. Neither source, nor any
other found in this survey, directly resolves what QAPF specifically should do; §6 makes an explicit,
reasoned choice rather than presenting a false consensus.

---

## 3. The six sub-questions, answered explicitly

**1. Is a fixed-percentage drawdown limit the right instrument, or do these authors favor volatility
targeting / dynamic scaling instead?** Carver [V] explicitly favors continuous volatility-targeted
position scaling over a binary threshold halt — this is the clearest, most direct answer in the survey.
Vince and Kaufman [P] operate at the *position-sizing* layer (how big is each bet), not the
*account-level halt* layer, and are silent on whether a account-wide stop-trading rule should exist on
top of correctly-sized bets — their implicit answer is "size correctly and you may not need a separate
halt," which is a different claim from Carver's "continuously de-risk instead of halting." De Prado's
bet-sizing chapter [P] is also a continuous-scaling approach. Chan's [V] sub-account method is a hybrid.
No source in this survey affirmatively argues *for* QAPF's current binary account-level halt as the
best available mechanism — that design is defensible on other grounds (see §7), not on "the literature
recommends it."

**2. What does Vince's optimal-f work imply about overbetting, and what does that imply for per-name
sizing in a 14-15 name, $1,000 book?** The asymmetry is confirmed [P, §2.1]: overbetting past the TWR
peak destroys growth "dramatically," non-linearly, while underbetting only costs some upside — the
literature's answer is "err smaller, always," typically landing on fractional f (half or quarter) as the
practically usable version, and every other author surveyed (Carver's half-Kelly, Chan's 1/4-1/2 Kelly)
converges on the same fractional-sizing instinct independently. For QAPF's per-name sizing, this argues
for **capping single-name exposure well below what a naive full-Kelly/full-optimal-f calculation would
suggest** — directly consistent with the repo's existing 35% per-position cap
(`backend/agents/portfolio/allocator.py:129`), which is already a fractional, not maximal, concentration
limit. It does *not* by itself argue for a specific `max_drawdown_pct` number — that is a portfolio-level
question the per-trade asymmetry argument doesn't directly answer.

**3. Is there a principled statistical test for "broken strategy" vs. "normal variation," or is it a
judgment call?** **The literature does not offer a clean, validated, off-the-shelf answer** — stated
plainly per the prompt's request. De Prado's CUSUM/explosiveness tests [P, §2.5] detect breaks in the
*underlying return process*, not validated tests for "has this specific strategy's edge broken." SPRT
[V as general theory] is mechanically applicable in principle but I found no source validating its
use for this exact purpose. Comparing live drawdown against the backtest's *own* historical drawdown
distribution (e.g., "is the current drawdown beyond the 95th percentile of drawdowns seen in the
2018-2020 walk-forward") is a sound, simple idea but was not found as an established named technique in
any source surveyed — it would be a reasonable ad hoc extension QAPF could build (the data already
exists: `report.max_drawdown` in Agent 9's output, and `drawdown_series()` already in
`backend/risk/metrics.py:43`), not something the literature hands over pre-validated. **Honest answer:
this remains substantially a judgment call**, informed by but not resolved by the tools above.

**4. Hard halt vs. soft de-risking — the recovery-participation failure mode.** Both sides are real and
both are cited, not blended into a false consensus. *Against* the hard halt: Varma's "death by a thousand
cuts" [V, §2.6] and the prompt's own measured anchor — a 25% limit would have halted QAPF on 2020-02-27,
the day before the COVID crash even began, locking in the loss and forfeiting the subsequent snap-back
rally entirely, structurally the exact failure mode Varma describes with the same event (SPY's Feb-Mar
2020 crash). Carver's continuous scaling [V] would have *reduced* exposure as volatility spiked without
fully exiting, preserving some recovery participation. *For* the hard halt: it bounds tail risk to a
known, auditable number; it removes the operator's own behavioral temptation to "let it ride" during a
crisis (a known, serious risk for solo discretionary override — none of the sources dispute that
behavioral bias is real, Research Affiliates/Syzygy [P, §2.6] cite it explicitly as a reason stop rules
exist); and it is mechanically simple enough for a stateless, once-a-day check to enforce correctly,
which matters when there is no other human or system watching intraday. **Net judgment, made explicit in
§7: keep the hard halt for now, not because the literature prefers it, but because the alternative the
literature does prefer (continuous vol-targeting) is not yet built and a $1,000 solo-operator deployment
needs *something* mechanically enforceable today.**

**5. Do optimal-f / vol-targeting / Kelly-style methods even apply mechanically at $1,000 across 14-15
names?** No, not without material modification — quantified in §4. Carver's own stated minimum for a
*single* instrument is $2,500 [V, §2.2]; QAPF proposes ~$67-$350 per name (depending on equal-weight vs.
cap) across up to 15 names simultaneously. Real August 2026 prices for this exact universe (§4) mean
equal-weighting cannot buy a whole share in 9 of 15 names. This is not a minor rounding nuisance — it is
the kind of granularity breakdown Carver's own writing on small accounts explicitly warns about
("caught between the devil of fractional contracts and the deep blue sea of insufficient
diversification").

**6. Where do these authors explicitly disagree?** Tabulated in §5, not blended.

---

## 4. Whole-share mechanics at $1,000 — the concrete numbers

QAPF's universe is fixed at 15 names (`backend/agents/portfolio/__main__.py:24-28`):
`AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, V, WMT, KO, PEP, XOM, CVX, JNJ, PG, HD`. Per-position cap is 35% of
gross exposure (`backend/agents/portfolio/allocator.py:129`), and gross exposure itself scales by regime
— 100% (risk-on), 80% (neutral), or 50% (risk-off) of the account
(`backend/agents/portfolio/allocator.py:62-66`).

**Real prices for this exact universe, retrieved 2026-08-19 (approximate, intraday snapshot) [P — search
extract, not a direct quote screen]:** AAPL ≈ $309, MSFT ≈ $493, GOOGL ≈ $375, AMZN ≈ $277,
NVDA ≈ $212, JPM ≈ $358, V ≈ $370, WMT ≈ $112, KO ≈ $87, CVX ≈ $190, JNJ ≈ $255, PG ≈ $148,
HD ≈ $348 (PEP and XOM not retrieved in the same query, but both trade well above $65).

**The arithmetic:**
- **Equal-weight, all 15 names, RISK_ON (100% deployed):** $1,000 / 15 = **$66.67 per name.** That
  amount cannot buy a single share of MSFT, GOOGL, AMZN, JPM, V, CVX, JNJ, PG, or HD — **9 of the 15
  names in the universe.** Only KO, WMT, and possibly PEP/XOM (unconfirmed prices, but plausibly under
  $115) are even reachable at one whole share.
- **35% cap, single name:** $350 — enough for exactly one share of most of these names but not two, and
  still not enough for MSFT ($493) or V ($370, marginal).
- **RISK_OFF regime (50% gross exposure):** total deployed capital drops to $500 across however many
  names have a positive signal — the equal-weight figure falls to as low as $33-40/name, making the
  whole-share problem strictly worse exactly when the regime classifier says risk should be reduced.

**What this means for the literature above:** optimal f, Kelly-fraction, and vol-targeting are all
*continuous* functions of capital — they output a real number like "8.3% of equity," which in a
$1,000/15-name book is a dollar figure ($83) that then has to round to a whole number of shares of a
$100-500 stock. That rounding is not a rounding error at this scale — it is the dominant effect. A
computed "optimal" weight of 8% for MSFT is $80, which is zero shares; the actual position is either
$0 (0%) or $493 (49.3%) — nothing in between is achievable. **This is exactly the mechanism Carver's own
small-account writing warns about** (§2.2), and it means QAPF's existing 35% cap and regime-based gross
exposure scaling are already doing real, load-bearing work in *constraining* concentration risk that a
naive continuous-formula sizing approach would recommend but the account cannot physically implement at
this size. The practical implication is not "abandon these formulas" but "treat their output as a
directional signal for which few names to concentrate in, not as a precise fraction to implement," and
recognize that true diversification benefit across 14-15 names is not actually available at $1,000 —
the account will, in practice, often hold a much smaller effective number of positions than 14-15,
which raises (not lowers) the effective per-name concentration risk relative to what the portfolio
optimizer's math assumes.

---

## 5. Where the sources explicitly disagree

| Question | Vince [P] | Carver [V] | Chan [V] | de Prado [P] | Research Affiliates/Syzygy [P] | Varma [V] |
|---|---|---|---|---|---|---|
| Primary sizing instrument | Fraction of optimal f (worst-loss-calibrated) | Continuous vol-target scaling | Fractional Kelly + capital sub-account floor | Probability-scaled bet size | Not a sizing framework — a stop-rule study | Not a sizing framework — a stop-rule critique |
| Account-level hard halt? | Not addressed directly | Explicitly not the primary mechanism — favors continuous scaling | Implicit floor via capital allocation, not a stop-trading trigger | Not addressed in bet-sizing chapter | Favors stop rules as a defensible risk-premium technique | Warns hard, static thresholds can destroy more capital than they save |
| Aggressive full-Kelly/full-f? | No — explicitly dangerous, use a fraction | No — recommends half-Kelly | No — recommends 1/4 to 1/2 Kelly | N/A | N/A | N/A |
| View on fixed drawdown % rules | Silent (works at trade level, not account level) | Not his preferred instrument | A hybrid, not a pure threshold | Silent in bet-sizing chapter | Institutionally supportive, in general | Skeptical of naive static thresholds |

**The genuine disagreement that matters most for QAPF:** Carver and Varma both push away from a flat,
static, binary drawdown percentage toward something continuous or context-dependent. Research
Affiliates/Syzygy's institutional framing pushes toward stop rules being defensible. Vince, Chan, and
implicitly de Prado operate one layer down (per-bet sizing) and simply don't take a position on whether
an account-level halt should exist on top of correctly-sized bets. **No source in this survey explicitly
recommends QAPF's current mechanism (a flat, binary, peak-to-current drawdown percentage with no
graduation) as the best available design** — it is a reasonable, simple, defensible choice made for
reasons outside the literature (operational simplicity, solo-operator enforceability), argued explicitly
in §7, not because any author here said "do this."

---

## 6. Concrete recommendation

**`max_drawdown_pct = 0.20`**
**`max_daily_loss_pct = 0.06`**

### Reasoning chain for `max_drawdown_pct = 0.20`

- The two measured anchors bound the decision: **15% halted in Q4 2018 on ordinary, non-crisis
  volatility** (a false positive that would have taken the strategy out of the market for no
  strategy-relevant reason), and **25% halted on 2020-02-27, the day before the COVID crash, forfeiting
  the entire subsequent recovery** (arguably closer to a true positive on tail-risk grounds, but a
  textbook case of Varma's "locks in the loss right before the snap-back" failure mode, §2.6).
- 20% sits inside that range, closer to the 25% anchor than the 15% one, deliberately: the Q4 2018
  false-positive at 15% is the stronger argument in this survey, because every fractional-sizing author
  surveyed (Vince, Carver, Chan) independently converges on "don't be so tight that ordinary variation
  trips the rule" — that is precisely what a fractional-Kelly/fractional-optimal-f/half-Kelly philosophy
  is *for*: leaving headroom against normal variance so a bad-but-survivable stretch doesn't force an
  exit. A 15% limit that fires on ordinary volatility is analogous to running at too tight a Kelly
  fraction — technically "protective" but in practice indistinguishable from overbetting's
  dollars-in-fees version: it forces exits at exactly the wrong, high-variance-but-not-broken moments.
- 20% is still meaningfully tighter than QAPF's own backtested worst case of −36.68%
  (2018-2020 walk-forward) — it would have caught the strategy well before its own historical worst
  drawdown, which is the entire point of having a limit at all, while giving roughly 5 percentage points
  more headroom than the 15% anchor that is known to produce a false-positive halt.
- This is explicitly **not** split-the-difference arithmetic between 15 and 25 — it is reasoned from
  which of the two anchors the cited literature argues is the worse failure mode for a fractionally-sized
  strategy (the too-tight one), landing closer to, but still inside, the 25% anchor.
- Caveat, stated plainly: the pending 2008-2017 validation backtest (mentioned as in progress, not yet
  available) spans the 2008 financial crisis, a genuinely different and probably worse drawdown regime
  than 2018-2020's COVID shock. **This 0.20 recommendation should be revisited once that validation run
  is in hand** — if 2008-2017's max drawdown materially exceeds 36.68%, the same reasoning chain above
  would likely still argue for a number in the high-teens-to-low-twenties range (bounded below the
  strategy's own worst historical case with headroom, bounded above the level known to produce
  ordinary-volatility false positives), but the specific number could shift.

### Reasoning chain for `max_daily_loss_pct = 0.06`

- No source in this survey gives a directly load-bearing number for a daily loss limit specifically —
  this is reasoned by analogy from two things: (a) the prop-firm survey's own finding
  (`docs/research/prop-firm-rules.md`, §0 point 2) that **every firm in that survey uses a 3-5% daily
  equity limit**, evaluated *intraday including unrealized P&L*, and (b) the repo's own daily check
  (`monitor.py:41`) is materially looser than that — it fires only on a **close-to-close** daily bar,
  not intraday, and only for a daily-rebalance system, not continuously.
- Because QAPF's daily check is mechanically a close-to-close test (not intraday-with-unrealized-P&L
  like every prop firm surveyed), a same-number match to the prop-firm 3-5% range would actually be
  *tighter in effect* than those firms' rules, since QAPF's number never benefits from an intraday
  bounce back before the close the way a same-day recovery would soften an intraday-marked limit. A
  single ordinary 3-5% down day for a 14-15 name long-only large-cap book is not unusual (e.g., broad
  index moves of that size occur multiple times a year) — a 3-5% flat limit risks the same
  ordinary-variation false-positive problem the 15% drawdown anchor already demonstrated at the
  portfolio level.
- 6% is chosen to sit **just above** the top of the prop-firm daily-limit range (4-5%), acknowledging
  that QAPF's own check is structurally stricter (close-to-close, no intraday recovery credit) than
  those firms' intraday-marked checks, and that the daily check should not be the more binding constraint
  relative to the 20% drawdown limit for a book that only rebalances once a day. This is a reasoned
  choice, not a literature-derived one — flagged explicitly as the weaker-sourced of the two numbers.

### Sensitivity check against the current backtest

Both numbers should be re-run through `show_kill_switch_tradeoff`-style scanning
(`backend/risk/__main__.py:131-145` already has the pattern) before going live, to see exactly which
dates in the 2018-2020 series a 20%/6% combination would have fired on — the same discipline used to
produce the 15%/25% anchors in the first place. This document sets the starting values; it does not
replace running that check.

---

## 7. Is the current hard-halt mechanism the right one?

**Short answer: keep it for now, as a deliberately temporary and simple mechanism — not because the
literature endorses it, but because the alternative it doesn't yet implement (continuous, Carver-style
volatility-targeted de-risking) requires infrastructure QAPF does not have.**

The literature's clearest voice on this exact question, Carver [V, §2.2], argues for continuous position
scaling as risk rises, not a binary account-level halt. That is very likely the *better* mechanism in the
abstract — it participates in recoveries, avoids the Varma "death by a thousand cuts" pattern, and is the
approach an institutional systematic shop would actually run. But implementing it requires: (a) a
volatility-forecasting layer that scales *position sizes*, not just a single account-wide gross-exposure
knob (QAPF's regime-based `RISK_GROSS_EXPOSURE` dict, `allocator.py:62-66`, is a step in this direction
but is a 3-value regime switch, not continuous vol-targeting); (b) enough capital and share-price
granularity for continuous scaling to be expressible at all (§4 shows this book cannot even express
continuous per-name weights cleanly at $1,000); and (c) either automated intraday monitoring or enough
operator attention to execute graduated de-risking correctly and without the exact behavioral bias
("just this once, let it ride") that a hard, mechanical rule exists specifically to remove
(Research Affiliates/Syzygy [P, §2.6] cite behavioral-bias mitigation as a first-order reason stop rules
exist at all).

For a **solo operator running $1,000 with no ability to watch the account intraday and no continuous
scaling infrastructure built yet**, a hard, auditable, once-a-day binary check is the more honestly
implementable choice today, even knowing it will occasionally produce a Varma-style false positive like
the 15% Q4-2018 case. The cost of that false positive at $1,000 stakes is bounded and recoverable; the
cost of building and trusting an unvalidated continuous de-risking system for the first live-money
deployment is a different, arguably larger kind of risk (an unverified risk-control mechanism is worse
than a verified simple one — consistent with this repo's own stated working principle in `CLAUDE.md`,
"verify before building on a claim"). **This is a considered trade-off for this specific
deployment size and operator setup, not a claim that binary halts are best practice in general** — the
literature surveyed here leans the other way for larger, more automated operations.

**One structural gap to close regardless of the threshold chosen:** per §1.1, the kill-switch currently
has no consumer — `kill_switch_triggered=True` is computed and printed but nothing stops an order. Before
this is meaningfully protective with real money, `backend/agents/execution/` (or a new orchestration
check) needs to actually query `RiskMonitor.assess()` and block/flatten on a breach. Setting the two
numbers in this document is necessary but not sufficient for the kill-switch to do anything in production
today.

---

## 8. Confidence level and what remains unverified

- **High confidence:** the repo's own mechanics (§1) — read directly from source, file:line cited.
  Carver's blog content (§2.2) and Chan's blog content (§2.4) — read directly, primary source.
  Varma's argument (§2.6) — read directly. The $1,000/15-name whole-share arithmetic (§4) — computed
  directly from real, recently-retrieved prices for this exact universe.
- **Medium confidence:** Vince's asymmetry argument (§2.1) — corroborated across multiple independent
  secondary sources plus his own words in a direct interview, but I never read his books' primary text,
  so precise numeric examples (e.g., an exact TWR curve) are not verified beyond what the interview and
  reviews state.
- **Lower confidence, flagged explicitly:** Kaufman (§2.3) — secondary-summary only, and I could not
  extract his specific numeric stance; not used as load-bearing for the final recommendation. De Prado's
  bet-sizing formula details (§2.5) — directionally confirmed, not numerically verified. The Research
  Affiliates/Syzygy paper's actual quantitative results (§2.6) — only the abstract-level framing was
  retrievable, not the underlying backtest or thresholds.
- **Explicitly unresolved by the literature, stated as such rather than papered over:** whether a
  principled statistical test exists for "broken strategy vs. normal variation" (§3, sub-question 3) —
  it does not, in the sources surveyed. This is a real gap in the field's tooling for exactly this
  question, not a gap in this research pass.
- **Pending and not waited on, per the task instructions:** a 2008-2017 validation backtest was reported
  as running separately. §6 already notes this recommendation should be revisited once that number is
  available, particularly for `max_drawdown_pct`, since 2008 plausibly produced a worse drawdown than
  the 2018-2020 window this document's anchors are based on.

# Regime-Conditional Factor Weighting: What the Published Evidence Actually Says

**Question:** Do equity factor premia (momentum, low-volatility, short-term reversal, volume/liquidity)
behave differently across macroeconomic regimes defined by growth and inflation — enough to justify
hand-set, regime-conditional factor weights?

**Scope of sources.** Peer-reviewed journals (JF, JFE, RFS, FAJ, JPM, JOIM), NBER/SSRN working-paper
versions of those same papers, and one primary practitioner document (Bridgewater) cited only for what
its own framework claims. Every empirical claim below was read out of the paper's own text, not from a
summary. Where I could only obtain the abstract rather than the full text, that is stated inline.

**Headline answer, stated up front.** The literature strongly supports conditioning momentum on
**market state and volatility** (bear market × high variance), and it strongly *fails* to support
conditioning factor weights on **macroeconomic growth × inflation quadrants**. Those two things are
easy to conflate and QAPF's Agent 7 conflates them.

---

## 1. Momentum: the relationship is real, but it is not a business-cycle relationship

### 1.1 The core finding — Daniel & Moskowitz (2016)

Kent Daniel and Tobias J. Moskowitz, "Momentum crashes," *Journal of Financial Economics* 122(2),
2016, 221–247. [Author copy (PDF)](https://www.kentdaniel.net/papers/published/jfe_16.pdf) ·
[NBER w20439](https://www.nber.org/papers/w20439) ·
[SSRN 2371227](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371227)

Sample: US equities 1927:01–2013:03, decile winner-minus-loser (WML) portfolio, plus international
equity and four other asset classes.

What they actually find:

- **The unconditional momentum premium is large but violently negatively skewed.** WML earns an
  annualized alpha of 22.2% (t = 7.3) with a market beta of −0.58 and Sharpe 0.60, but its monthly
  log-return skewness is **−4.70** (daily −1.18) — Table 1. The two worst months are consecutive
  (July–August 1932): the loser decile returned +232% while winners gained only 32%.
- **Crashes cluster in a specific, forecastable state — and it is a *market* state, not a macro state.**
  "Fourteen of the 15 worst momentum returns occur when the lagged two-year market return is negative.
  All occur in months in which the market rose" (discussion of Table 2). Their bear-market indicator
  `I_B` is defined purely as *the cumulative CRSP value-weighted index return over the past 24 months
  being negative* — no GDP, no CPI, no NBER dates. It is on in 183 of 1,035 months.
- **The mechanism is conditional beta, not macro risk.** In bear markets the WML portfolio's up-market
  beta is more than double its down-market beta (−1.51 vs −0.70, t on the difference = 4.5). "Outside
  of bear markets, there is no statistically reliable difference in betas." In the Henriksson–Merton
  specification (Table 3, regression 3) the bear-market up-market interaction is β̂_{B,U} = −0.815
  (t = −4.5); conditional on a bear market, WML's beta is −0.742 when the market falls and −1.796 when
  it rises. "The momentum portfolio is effectively short a call option on the market."
- **Bear market alone is not enough — it is bear market *times* volatility.** Table 5 is the decisive
  regression. With the bear indicator alone, α̂_B = −2.626 (t = −3.8). With ex-ante market variance
  alone, α̂_σ² = −0.330 (t = −5.1). With all three terms including the interaction, the standalone
  terms collapse to α̂_B = 0.023 (t = 0.0) and α̂_σ² = −0.088 (t = −0.8), while only the interaction
  survives: α̂_int = −0.323 (t = −2.2). Using VIX-implied variance-swap data (Table 6), the WML mean is
  31.48%/yr when `I_B = 0` and roughly **59 percentage points per year lower** in panic states
  (coefficient −58.62, t = −5.2).
- **What conditioning is worth.** Their dynamic strategy scales WML by forecast mean / forecast
  variance. Annualized Sharpe over 1934:01–2013:03: static WML **0.682**, constant-volatility
  **1.041**, out-of-sample dynamic **1.194** (Table 7). Applied across all markets and asset classes,
  the dynamic strategy reaches 1.19 versus a static US-equity Sharpe roughly a quarter of that.

The complementary risk-management result is Pedro Barroso and Pedro Santa-Clara, "Momentum has its
moments," *JFE* 116(1), 2015, 111–120
([SSRN 2041429](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2041429)): momentum's *risk* is
"highly variable over time and predictable," and managing it "virtually eliminates crashes and nearly
doubles the Sharpe ratio." (Read from the published abstract; Daniel & Moskowitz replicate and extend
it, and show their mean-forecasting adds an appraisal ratio of 0.396 on top of constant-volatility
scaling.)

### 1.2 Market state, again not macro state — Cooper, Gutierrez & Hameed (2004)

Michael J. Cooper, Roberto C. Gutierrez Jr. and Allaudeen Hameed, "Market States and Momentum,"
*Journal of Finance* 59(3), 2004, 1345–1365.
[Author copy (PDF)](https://rogutierrez.net/files/States_and_Momentum.pdf) ·
[Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00665.x)

- State definition is, again, a **lagged market return**: "UP" is a non-negative lagged three-year CRSP
  value-weighted return, "DOWN" is negative.
- 1929–1995, six-month momentum: **+0.93% per month after UP markets, an insignificant −0.37% after
  DOWN markets**, and the difference is significant. Robust to one- and two-year state definitions and
  to Fama–French risk adjustment.
- Critically for our question, they test the macro alternative head-on. Two-way sorts on
  macro-model-predicted returns show "the macroeconomic model has no ability to explain the momentum
  profits following UP states"; momentum is at least 0.50%/month in *every* quintile of macro-predicted
  return. "Dividend yield, default spread, term spread, and short-term interest rates do not capture
  the asymmetry in momentum profits." In recursive out-of-sample tests, "the lagged return on the
  market is a robust predictor of the time-series of momentum profits, while the macroeconomic
  multifactor model is not."
- UP-market momentum reverses long-run (−0.36%/month over holding months 13–60), and there is also
  long-run reversal after DOWN states (−0.67% raw, −0.52% CAPM-adjusted) — i.e. reversal exists without
  prior momentum.

### 1.3 The one prominent pro-macro paper, and its rebuttals

Tarun Chordia and Lakshmanan Shivakumar, "Momentum, Business Cycle, and Time-Varying Expected Returns,"
*Journal of Finance* 57(2), 2002, 985–1019
([Wiley](https://onlinelibrary.wiley.com/doi/10.1111/1540-6261.00449) ·
[SSRN 243807](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=243807)) argues that momentum profits
*are* explained by a set of lagged macroeconomic variables and disappear once returns are adjusted for
macro-predictability. This is the strongest published claim in favour of macro-conditioned momentum.
(Read from the published abstract.)

It has been contested from three directions, and the contests have held up better:

1. **International failure.** John M. Griffin, Xiuqing Ji and J. Spencer Martin, "Momentum Investing
   and Business Cycle Risk: Evidence from Pole to Pole," *Journal of Finance* 58(6), 2003, 2515–2547
   ([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1046/j.1540-6261.2003.00614.x) ·
   [SSRN 291225](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=291225)) find only modest support
   for the macro explanation outside the US, and note momentum profits comove only weakly across
   countries — hard to square with a common macro risk driver. (Read from abstract and from Cooper et
   al.'s and AQR's characterisations of it.)
2. **Methodological fragility.** Cooper, Gutierrez & Hameed replicate Chordia–Shivakumar's method and
   report that "the success of the macroeconomic multifactor model in explaining momentum documented by
   CS is not robust to common screens used to mitigate microstructure-induced" effects (price screens,
   skipping the formation month).
3. **Century-scale non-replication** — see §3 below.

### 1.4 Bottom line on momentum

There *is* strong published evidence that momentum's conditional expected return varies with state, and
the sign is broadly "worse in bad states." But the state variable that carries the evidence is
**trailing market return interacted with market volatility**, realised at daily/monthly frequency and
measured from prices. The evidence that momentum's premium tracks **GDP growth or CPI inflation** is
weak, contested, and does not replicate internationally or over longer samples. The common shorthand
"momentum works in expansions, breaks in contractions" is *directionally* consistent with the price-based
literature but is using the wrong instrument.

---

## 2. Low-volatility / defensive across regimes: weaker and, on inflation, pointing the *wrong* way

### 2.1 The unconditional effect is robust

Andrea Frazzini and Lasse Heje Pedersen, "Betting against beta," *JFE* 111(1), 2014, 1–25.
[NBER w16601 (PDF)](https://www.nber.org/system/files/working_papers/w16601/w16601.pdf) ·
[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0304405X13002675)

- The US BAB factor realizes a **Sharpe ratio of 0.75 between 1926 and 2009** — "about twice the Sharpe
  ratio of the value effect over the same period and 40% higher than the Sharpe ratio of momentum" —
  with significant 1-, 3-, 4- and 5-factor alphas and positive returns in each of four 20-year
  sub-periods.

David Blitz, Pim van Vliet and Guido Baltussen, "The Volatility Effect Revisited," *JPM* 46(2), 2020,
45–63 ([SSRN 3442749](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3442749) ·
[Erasmus copy](https://pure.eur.nl/ws/portalfiles/portal/196005365/JPM-2019-Blitz-45-63.pdf)) confirm
the effect is "highly persistent over time and across markets," not explained by value, profitability,
or interest-rate exposure. (Read from published abstract.)

### 2.2 But the *conditional* story is the opposite of the intuitive one in two important places

**(a) Tightening funding conditions hurt BAB.** Frazzini–Pedersen's model "predicts that the BAB factor
has negative returns during times of tightening funding liquidity constraints," and they confirm it:
"high contemporaneous TED spreads predicts BAB returns negatively," and "the lagged TED spread predicts
returns negatively" too. They also find beta compression — cross-sectional beta dispersion falls when
the TED spread is high, and BAB picks up a positive market beta in those periods. In other words, the
*long-short, leveraged* defensive factor does **badly** precisely in the deleveraging episodes a
deflationary-contraction regime is meant to capture.

**(b) Rising inflation hurts BAB, and this is the single most statistically significant regime effect
in the literature I found.** Henry Neville, Teun Draaisma, Ben Funnell, Campbell R. Harvey and Otto Van
Hemert, "The Best Strategies for Inflationary Times," *JPM* 47(8), 2021, 8–37.
[Duke copy (PDF)](https://people.duke.edu/~charvey/Research/Published_Papers/P154_The_best_strategies.pdf) ·
[SSRN 3813202](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3813202)

Regime definition: "times when headline, year-over-year (YoY) inflation is accelerating and when the
level moves to 5% or more" — **eight US episodes since 1926**. Exhibit 13, annualized real long–short
returns, inflationary vs. other, with hit rate and heteroskedasticity-consistent t-statistic:

| Factor | Inflationary | Other | Hit rate | t-stat |
|---|---|---|---|---|
| Momentum (12-1) | **+8%** | +4% | 75% | **0.6** |
| QMJ (quality) | +3% | +3% | 60% | −0.1 |
| CMA (investment) | +2% | +2% | 40% | −0.1 |
| RMW (profitability) | −1% | +2% | 60% | −1.5 |
| HML (value) | −1% | +2% | 25% | −1.5 |
| SMB (size) | −4% | +1% | 25% | −1.8 |
| **BAB (low vol)** | **−3%** | **+8%** | **25%** | **−4.2** |

Coverage differs by row — the paper's own note: "Data are from 1926 in the case of SMB and HML, from
1927 in the case of momentum, from 1963 for RMW and CMA, from 1930 for BAB, and from 1957 for QMJ." So
momentum, SMB, HML and BAB span all eight episodes; QMJ spans five and RMW/CMA five.

Two things matter here. First, **momentum is the *best* equity factor in inflationary regimes**, not
the worst — the opposite of a common prior, though the authors are explicit that "the difference is not
statistically significant for this volatile, high-turnover strategy" (t = 0.6). Second, **BAB is the
worst, and that one *is* significant** (t = −4.2, positive in only 2 of 8 episodes).

The authors' own caveat is directly transferable to QAPF: "the performance is highly sensitive to the
dating of our regimes. For example, January 1975 was a very negative month for cross-sectional
momentum, and our inflationary regime stops in December 1974. Equally, late 2008 through early 2009 was
catastrophic for momentum, and our inflationary period ends in July 2008." A handful of regime
boundary decisions flip the sign of the headline result.

**Independent corroboration of (b):** AQR's century study (§3) reports that for defensive strategies,
"tail risk, inflation, and business cycle expansions affect defensive strategies negatively" — same
sign as Neville et al. on inflation. But AQR adds that "only sentiment is significant after accounting
for multiple testing."

### 2.3 An important construction caveat

BAB is a **beta-neutral, leveraged long–short** portfolio. A long-only low-volatility *tilt* — which is
what QAPF's `low_volatility` factor is — is a different animal: it retains a large positive market beta
and its regime behaviour is dominated by the market's regime behaviour, not by the low-risk premium.
Evidence about BAB in crises should not be read straight across to "a long-only book tilted toward
low-vol names will do badly in a drawdown." It generally will not; it will simply lose less than the
market. Conversely, a good realised Sharpe from a long-only defensive tilt in a contraction is largely
*market beta timing*, not evidence that the defensive **factor premium** was high.

---

## 3. Growth × inflation quadrant frameworks: not supported as a factor-timing device

### 3.1 The best-powered direct test finds essentially nothing

Antti Ilmanen, Ronen Israel, Rachel Lee, Tobias J. Moskowitz and Ashwin Thapar, "How Do Factor Premia
Vary Over Time? A Century of Evidence," *Journal of Investment Management*, forthcoming (current draft
Jan 2021). [Full text (PDF)](http://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/3/2021/08/HowDoFactorPremiaVaryOverTime_JOIM.pdf) ·
[SSRN 3400998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3400998) ·
[AQR](https://www.aqr.com/Insights/Research/Journal-Article/How-Do-Factor-Premia-Vary-Over-Time-A-Century-of-Evidence)

Four factors (value, momentum, carry, defensive) across six asset classes over ~100 years. Their macro
test is close to a superset of QAPF's regime taxonomy:

> "We use global GDP growth ... and global CPI inflation rate ... To capture business cycle variation,
> we divide periods into positive and negative growth based on annual GDP growth each quarter, and
> define periods into 'accelerating' and 'decelerating' growth ... The intersection of these indicators
> creates four subperiods: contraction, recovery, expansion, and slowdown."

They also test tail-event indicators, geopolitical risk, real-rate level and change, yield-curve level
and change, illiquidity, volatility and sentiment — contemporaneously (Panel A of Table III) and lagged
so the news was actually released before formation (Panel B).

Results, verbatim:

- "**For momentum, nothing is significant.**"
- "Similarly, carry returns have no contemporaneous relation to any of the variables."
- For value: positive loadings on illiquidity risk, sentiment and the slowdown indicator, "however,
  none of these coefficients are statistically significant after accounting for multiple comparisons."
- For defensive: negative on tail risk, inflation and business-cycle expansions, positive on one-year
  real-rate changes; "only sentiment is significant after accounting for multiple testing."
- Lagged (predictive) panel: "The evidence for economic news predicting factor returns is as weak as
  contemporaneous activity, with low R-squares and insignificant coefficients."
- Summary: "**Overall, there is little evidence that the factor returns vary in a meaningful way with
  macroeconomic variables, either contemporaneously or predictively.** Despite our long and broad
  sample providing a rich set of macroeconomic events and added statistical power, we do not find much
  macroeconomic exposure for long-short factors."

They explicitly place this against the prior literature: "The results are broadly consistent with
Griffin, Ji, and Martin (2003) ... and are inconsistent with other studies (Chordia and Shivakumar
(2005), Hodges, Hogan, Peterson, and Ang (2017)) that examine much shorter histories and equity-only
factors."

On using macro variables to *time* factors, they are blunter still: "we showed in Table III that the
in-sample estimated coefficients on the business cycle variables are not significant, **and change sign
across asset classes for a given factor**. Growth and inflation momentum timing similarly show much
weaker performance when parameters are estimated out of sample. The figure highlights the dangers of
using in-sample parameter estimates, especially for theoretically ambiguous variables such as the
macroeconomic measures." Notably, CAPE *does* show predictability while "VIX ... does not deliver any
timing ability for the factors."

What they do find is **regime-dependent correlations**, not regime-dependent returns: value/momentum
correlation is −0.66 in the best market months vs −0.41 in the worst; several pairs diversify better in
recessions. "Overall, we do not find much impact on returns from macroeconomic shocks, but do find some
variation in correlations and risk associated with macroeconomic regimes."

### 3.2 The four-quadrant framework is being used for something it was never claimed to do

Bridgewater Associates, "The All Weather Story."
[Primary document (PDF)](https://www.bridgewater.com/_document/the-all-weather-story?id=00000171-8623-d7de-affd-feaf4ee20000) ·
[landing page](https://www.bridgewater.com/research-and-insights/the-all-weather-story). Related:
Ray Dalio, "Engineering Targeted Returns and Risks," Bridgewater, Aug 2011
([PDF](https://bridgewater.brightspotcdn.com/fa/e3/d09e72bd401a8414c5c0bdaf88bb/bridgewater-associates-engineering-targeted-returns-and-risks-aug-2011.pdf)).

Reading Bridgewater's own account, three things are true of the four boxes that are *not* true of how
QAPF uses them:

1. **The axes are surprises, not levels.** "Markets move based on shifts in conditions relative to the
   conditions that are priced in. This is the definition of a surprise." The boxes describe
   environments "when (1) inflation rises, (2) inflation falls, (3) growth rises, and (4) growth falls
   **relative to expectations**." QAPF's Agent 6 classifies on realised, backward-looking data —
   INDPRO/PAYEMS/UNRATE year-over-year for growth, CPI year-over-year *acceleration* for inflation
   (`backend/agents/macro/regime.py`, ~lines 180–235). Realised-level quadrants and
   surprise-relative-to-discounted quadrants are different objects; only the second has a mechanical
   reason to move prices.
2. **The framework is applied to asset classes, not to cross-sectional equity factors.** "It is
   predicated on the notion that asset classes react in understandable ways based on the relationship
   of their cash flows to the economic environment." Long–short equity factors are largely
   cash-flow-neutral and market-neutral by construction; the mechanism that makes bonds do well in
   disinflationary recession does not obviously transfer to a momentum spread.
3. **The framework's own conclusion is not to tilt.** "The key was to put equal risk on each scenario
   to achieve balance. Investors are always discounting future conditions and they have equal odds of
   being right about any one scenario." All Weather is an argument for *equal risk across quadrants
   because you cannot forecast the quadrant*. Using the same four boxes to concentrate into the quadrant
   you believe you are in inverts the original logic.

**Verdict on sub-question 3:** the growth × inflation quadrant framework is well-founded *as a
risk-balancing device across asset classes under uncertainty about the environment*. As a
factor-timing device for cross-sectional equity factors it is, on the published evidence, narrative.
The only well-powered direct test (Ilmanen et al.) finds coefficients that are insignificant and
sign-flipping; the only significant regime effect anyone reports (Neville et al.'s BAB in inflation,
t = −4.2) points *against* the standard "go defensive when things are bad" prior on the inflation axis.

### 3.3 The honest counterweight

Two lines of work do support regime-based dynamism, and should be stated fairly:

- Mark Kritzman, Sebastien Page and David Turkington, "Regime Shifts: Implications for Dynamic
  Strategies," *FAJ* 68(3), 2012 ([SSRN 2064801](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2064801) ·
  [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2012/regime-shifts-implications-for-dynamic-strategies-corrected))
  apply Markov-switching models to turbulence, inflation and growth and find a dynamic process beat
  static allocation in backtests, "especially for investors who seek to avoid large losses." Note the
  scope: **asset allocation**, not cross-sectional factor weighting, and backtested. (Read from
  published abstract.)
- Christopher Polk, Mo Haghbin and Alessio de Longis, "Time-Series Variation in Factor Premia: The
  Influence of the Business Cycle," *JOIM*, 2020
  ([SSRN 3377677](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3377677)) argue factors have
  heterogeneous macro sensitivities that can motivate dynamic rotation across size, value, quality,
  low-volatility and momentum. I was unable to retrieve the full text (the Invesco-hosted PDF now
  404s), so I am citing it as *existing on the other side of the argument* rather than as verified
  evidence. It is US-equity-only over a much shorter horizon than Ilmanen et al., which is precisely
  the class of study Ilmanen et al. say does not replicate.

---

## 4. Short-term reversal and volume/liquidity: the one factor with a genuinely strong conditional case

Stefan Nagel, "Evaporating Liquidity," *Review of Financial Studies* 25(7), 2012, 2005–2039.
[NBER w17653 (PDF)](https://www.nber.org/system/files/working_papers/w17653/w17653.pdf) ·
[RFS](https://academic.oup.com/rfs/article-abstract/25/7/2005/1602153)

Short-term reversal returns are a proxy for the return to liquidity provision, and they are **the most
predictable conditional premium in this whole literature**:

- Sample Jan 1998 – Dec 2010, daily. Regressing reversal-strategy returns on lagged VIX (Table 2): a
  one-point rise in normalized VIX raises the daily reversal return by **0.22pp** (SE 0.02), with
  **adjusted R² = 0.07 on daily data** — "extremely high for a predictive regression with daily
  returns." At monthly frequency the adjusted R² is **0.56** for transaction-price returns, 0.25 for
  quote-midpoint returns, 0.07 for industry-portfolio reversals.
- VIX beats lagged market return: adding the lagged market return "only has a weak effect, and VIX
  remains a strong predictor." Nagel explicitly notes "the VIX is a much more powerful predictor of
  reversal strategy returns than lagged market returns," improving on Hameed, Kang & Viswanathan (2010).
- Conditional Sharpe ratios rise with VIX, not just expected returns — evidence for binding
  intermediary funding constraints rather than mere volatility compensation. During 2007–09 "expected
  returns of reversal strategies formed with individual stocks rose almost ten-fold from their levels
  in 2006 in close lockstep with a corresponding increase in the VIX index."
- Even *industry-portfolio* reversal, unprofitable unconditionally, earns a fitted ~0.20%/day at
  crisis-level VIX (~60%).
- Reversal returns have **positive** skewness — the opposite of momentum.
- Caveat he states himself: "Fixed costs for high-speed market access and technological requirements
  for successful placement of orders that capture order flow probably play an important role ... After
  accounting for these fixed costs, Sharpe ratios would likely be much less extreme." The paper's
  claim is about *relative time-variation*, not the achievable level.

Alternative liquidity-supply predictors he tests — cross-sectional idiosyncratic volatility, TED
spread, primary-dealer repo growth — all enter with the expected sign, which matters here: **TED spread
predicts reversal returns positively while it predicts BAB returns negatively (Frazzini–Pedersen).**
So a "stress" regime is genuinely good for reversal and genuinely bad for leveraged low-beta. Those two
should not be moved in the same direction by the same regime switch.

I found no comparably strong published result for a stand-alone "volume trend" factor conditional on
macro regimes. Volume/liquidity enters the literature mainly as (a) the reversal/liquidity-provision
channel above, and (b) an interaction with momentum (Lee & Swaminathan, cited in Cooper et al.). Treat
QAPF's `volume_trend` as the least evidence-backed of its four factors.

---

## 5. Factor timing in general: both sides, honestly

### 5.1 The skeptics

- **Clifford S. Asness, "The Siren Song of Factor Timing," *JPM* 42(5), 2016, 1–6**
  ([SSRN 2763956](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2763956) ·
  [AQR version](https://www.aqr.com/-/media/AQR/Documents/Insights/Perspectives/Resisting-the-Siren-Song-of-Factor-Timing.pdf)).
  Timing strategies are "quite weak historically," and what power they have "is too highly correlated
  to the simple value factor itself." He notes the incentive problem explicitly: factor timing
  reintroduces fee-bearing active management into factor investing. His prescription is to identify
  good long-term factors, access them cheaply, diversify, and hold them "with little variance over
  time." (Read from published abstract and AQR's own summary.)
- **Asness, Chandra, Ilmanen & Israel, "Contrarian Factor Timing is Deceptively Difficult," *JPM*
  43(5), 2017, 72–87** ([SSRN 2928945](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2928945)).
  Value spreads carry *some* predictive information for style returns, but implementing value-based
  timing inside a multi-style portfolio that already contains value "delivers weak incremental
  benefits" and can reduce diversification by concentrating implicit value exposure. (Read from
  published abstract.)
- **Ilmanen et al. (2021), §3.1 above**, is the most quantitative skeptic. Their best out-of-sample
  combined timing model reaches an information ratio of **0.31** (0.32 with sign constraints)
  orthogonal to static factors — versus **0.89** using full-sample in-sample coefficients, "which again
  highlights the dangers of using full sample information." Their conclusion: "An optimal timing
  portfolio implementable in real time produces small profits once real-world implementation costs are
  considered. Hence, an investor should be cautious about deviating from a long-term static allocation
  to these factors through tactical factor timing."

### 5.2 The strongest pro-timing paper — and note what it times on

Valentin Haddad, Serhiy Kozak and Shrihari Santosh, "Factor Timing," *RFS* 33(5), 2020, 1980–2018.
[Author copy (PDF)](https://serhiykozak.com/files/papers/04%20-%20Factor%20Timing%20-%20RFS.pdf) ·
[RFS](https://academic.oup.com/rfs/article-abstract/33/5/1980/5753962) ·
[NBER w26708](https://www.nber.org/papers/w26708)

- They reduce ~50 anomaly portfolios to their leading principal components and predict each PC.
  "For the two most predictable components, the first and fourth PCs, their own book-to-market ratios
  predict future monthly returns with an out-of-sample R² around 4%, about 4 times larger than that of
  predicting the aggregate market return." Total OOS monthly R² across anomalies ≈ 1%.
- Table 6, Sharpe ratios: in-sample — factor investing 1.27, market timing 1.23, factor timing 1.19,
  anomaly timing 1.19, pure anomaly timing 0.71; **out-of-sample — 0.76, 0.63, 0.87, 0.96, 0.77.**
  A pure factor-timing portfolio achieves a Sharpe of 0.71 and "the benefits from timing market-neutral
  factors largely outweigh those from timing the aggregate market return."
- **The predictor is a valuation signal, not a macro signal.** "We take a simple stance on this second
  issue by using only the book-to-market ratio of each portfolio to predict its returns." Where macro
  does appear, it is a negative result: "The SDF variance evolves mostly at business cycle frequency
  rather than at longer horizons. **However, it is not always related to recessions.** More broadly,
  macroeconomic variables capturing variations in the price of market risk often have different
  relations with the SDF variance."
- One genuinely relevant cyclicality claim: "the loadings of size and value are procyclical while the
  loading of momentum is **countercyclical**." That is the *opposite* sign to the "momentum in
  expansions" prior, though it is a statement about SDF loadings rather than realised premia.
- Implementation caveat in their own words: performance survives annual rebalancing (Sharpe 0.71 → 0.79),
  so "factor timing strategies might be implementable by actual investors; direct measures of
  transaction costs would be necessary to make this a firm conclusion."

### 5.3 Where the literature actually agrees

Stripping out the disagreement, three propositions have broad support:

1. Conditional factor premia **exist** and vary meaningfully over time (Ilmanen et al., Haddad et al.,
   Daniel & Moskowitz all agree).
2. The conditioning information that survives out-of-sample is **price-based** — valuation spreads,
   trailing market returns, realised/implied volatility — not macroeconomic.
3. The out-of-sample economic gain is **modest relative to in-sample**, roughly a factor of 2–3 decay,
   and can be eaten by turnover. Ilmanen et al. also document decay in the premia *themselves* relative
   to the original discovery samples — a 49% average Sharpe decline for value (p = 0.000) and 18% for
   their multifactor portfolio (p = 0.000) — which they attribute to overfitting in the original studies
   rather than to arbitrage activity. (The widely quoted "~30% drop" is the headline figure from the
   earlier SSRN abstract; the January 2021 draft reports the per-factor numbers above.)

---

## 6. Implications for QAPF's Agent 7

### 6.1 What Agent 7 currently asserts

`backend/agents/alpha/combiner.py` hard-codes:

| Regime | momentum_12_1 | reversal_5d | low_volatility | volume_trend |
|---|---|---|---|---|
| inflationary_expansion | 0.45 | 0.15 | 0.20 | 0.20 |
| disinflationary_growth | **0.50** | 0.15 | 0.20 | 0.15 |
| stagflation | 0.15 | 0.25 | **0.45** | 0.15 |
| deflationary_contraction | 0.10 | 0.30 | **0.45** | 0.15 |

The module docstring states the premise as "trend factors (momentum) do well in expansions and break
down in contractions — momentum crashes cluster in stressed/transitional regimes."

### 6.2 Scoring the premise against the evidence

| Claim embedded in the weights | Verdict |
|---|---|
| Momentum crashes cluster in stressed states | **Supported** — but the state is bear market × high volatility (Daniel & Moskowitz Table 5; Cooper et al.), not a GDP/CPI quadrant |
| Momentum's premium tracks the growth×inflation quadrant | **Not supported.** "For momentum, nothing is significant" (Ilmanen et al., Table III). Contested at best (Chordia–Shivakumar vs Griffin/Cooper) |
| Momentum should be *cut hardest* when inflation is rising (0.15 in stagflation) | **Contradicted, weakly.** Momentum is the best equity factor in inflationary regimes: +8% vs +4% real, though t = 0.6 (Neville et al., Exhibit 13) |
| Low-vol should be *raised hardest* when inflation is rising (0.45 in stagflation) | **Contradicted, strongly.** BAB is −3% vs +8% real in inflationary regimes, hit rate 2/8, **t = −4.2** (Neville et al.); AQR independently finds inflation loads negatively on defensive |
| Low-vol should be raised in deflationary contraction | **Ambiguous.** For a *long-only* tilt, plausible (it's beta reduction). For the low-risk *premium*, BAB earns negative returns when funding constraints tighten (Frazzini–Pedersen) |
| Reversal should be raised in stress (0.25–0.30) | **Supported, and it is the best-evidenced of the four** — but the correct conditioner is VIX / TED / dispersion, not a macro quadrant (Nagel 2012, monthly adj. R² 0.56) |
| volume_trend deserves a stable 0.15–0.20 | **No published regime evidence found either way.** Least defensible line item |

### 6.3 On the Agent 14 validation result (Sharpe +1.16 in deflationary contraction, −0.32 in disinflationary growth)

Four reasons not to treat that as evidence the priors are backwards:

1. **It doesn't say what it looks like it says.** The result is: the regime where the design goes
   defensive did well, and the regime where the design bets on momentum did badly. That is fully
   consistent with the *contraction* prior being right and only the *expansion/momentum* prior being
   wrong. Inverting the table — putting momentum at 0.45–0.50 in contractions — would place the largest
   momentum bet exactly where Daniel & Moskowitz show the momentum premium is ~59 percentage points per
   year lower and the portfolio behaves like a written call on the market. **Inversion is the one
   change the literature rules out.**
2. **It has no statistical power.** Using Lo's asymptotic estimator (Andrew W. Lo, "The Statistics of
   Sharpe Ratios," *FAJ* 58(4), 2002, 36–52,
   [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios)),
   the standard error of an annualized Sharpe from daily IID returns is approximately
   `sqrt((1 + SR²/(2·252)) / T_years)` ≈ `sqrt(1/T_years)`. A regime segment inside a 2018–2020 backtest
   is at most ~1 year, so SE ≈ 1.0 and often worse. The gap of 1.48 Sharpe units carries a standard
   error of roughly √(1.0² + 1.2²) ≈ 1.6 — a t-statistic under 1. *(This is my calculation from Lo's
   estimator applied to plausible segment lengths, not a published figure; the exact day counts are in
   Agent 14's `regime_performance` output and should be substituted before quoting it.)* For scale:
   Neville et al. needed 95 years and 8 episodes and still got t = 0.6 on momentum.
3. **It is confounded by market beta.** Agent 2 is long-only by deliberate design
   (`allocator.py`), so the measured regime Sharpe is dominated by the market's return in that regime,
   not by the factor-weighting decision. Deflationary-contraction labelling in 2020 plausibly spans both
   the COVID crash and the far larger rebound; a +1.16 Sharpe there is mostly "the market went up,"
   with a modest defensive drag. Meanwhile the disinflationary-growth segment covers 2019, which
   contains the September 2019 momentum unwind — one of the largest single-day momentum reversals since
   2009. Two idiosyncratic events, one per regime bucket.
4. **The regime dating is doing the work.** Neville et al.'s caveat applies verbatim: shifting a regime
   boundary by a month flipped their momentum sign. QAPF's quadrant boundary is a *sign test on a mean
   of clamped z-scores* (`regime.py`, `growth_score >= 0`) — maximally sensitive right where most
   observations sit.

### 6.4 Recommendation

**Flatten the macro-conditional weights toward equal weight, and move the conditioning that the
evidence does support onto price-based state variables.** Concretely, in priority order:

1. **Do not invert.** The one directional claim in the current table that the literature backs
   unambiguously is "don't run big momentum into a stressed market." Keep that.

2. **Replace the four-quadrant conditioner with a two-state price conditioner for momentum.**
   Daniel & Moskowitz's instrument is trivially cheap and needs no macro data: `I_B = 1` if the
   trailing 24-month market return is negative, interacted with trailing 126-day realised market
   variance. Scale momentum's weight (or the whole book's gross exposure) by their `μ/σ²` rule rather
   than by a GDP/CPI quadrant. This is a *smaller* change than it sounds — Agent 7 already has a
   `RISK_EXPOSURE_SCALE` seam and Agent 6 already computes a `RiskRegime`; the change is which variable
   feeds it.

3. **Condition reversal on VIX (or a realised-dispersion proxy), not on the quadrant.** This is the
   single highest-conviction conditional relationship in the reviewed literature (Nagel: monthly
   adj. R² = 0.56). It is also the one place where "crank it up in stress" is the *right* action and
   the current table already does roughly the right thing — for the wrong reason and off the wrong
   variable. Note the transaction-cost caveat: at 5-day horizons this is a high-turnover factor, and
   Agent 11's impact model must be in the loop before the weight is raised.

4. **Cut the stagflation low-volatility weight from 0.45 toward the flat 0.25.** This is the one cell
   with a statistically significant published result *against* it (t = −4.2). If anything, the
   stagflation and inflationary-expansion rows should look more alike, with momentum *not* cut to 0.15.

5. **Set volume_trend to a flat weight across all regimes** until there is evidence for it. Varying a
   weight you have no prior about adds variance without adding information.

6. **Keep the weights hand-set and auditable — do not fit them.** The docstring's original reasoning is
   correct and the literature reinforces it: Ilmanen et al. get IR 0.89 in-sample and 0.31
   out-of-sample from exactly this kind of exercise, and their macro coefficients "change sign across
   asset classes for a given factor." A backtest over 2018–2020 has nowhere near the power to fit four
   weights × four regimes (16 free parameters) against ~750 observations.

### 6.5 What evidence would actually settle it

The current validation cannot settle it, at any sample size, because it measures the wrong quantity.
To make this decidable:

- **Measure the factor, not the portfolio.** Compute each of the four factors' own *long–short*
  (or at minimum cross-sectionally demeaned) return series, then bucket by regime. The present test
  measures a long-only book whose Sharpe is dominated by market beta; a regime-conditional weighting
  decision cannot be evaluated through it. This is a change to Agent 14, not to Agent 7.
- **Extend the sample to at least 1990, ideally 1970.** QAPF already runs Qlib's bundled US data for
  execution; the factor return series themselves can come from Ken French's library (momentum,
  short-term reversal) and AQR's public datasets (BAB, QMJ, and the
  [Century of Factor Premia monthly data](https://www.aqr.com/Insights/Datasets/Century-of-Factor-Premia-Monthly)
  released with Ilmanen et al.). Two and a half years is not a sample; eight decades is.
- **Run the horse race explicitly.** Regress each factor's return on (a) the QAPF quadrant dummies and
  (b) Daniel–Moskowitz's `I_B × σ²_m` plus VIX, in the same regression. Ilmanen et al.'s result
  predicts the quadrant dummies go insignificant while the price-based terms survive. If the quadrant
  dummies survive on QAPF's universe, that is a genuine finding worth keeping; if they don't, the
  weights should flatten.
- **Apply a multiple-testing correction and state it.** Sixteen weights across four regimes is sixteen
  implicit hypotheses. Ilmanen et al. found that almost everything they saw died under multiple-testing
  adjustment; that is the standard to hold Agent 7's priors to. Agent 4's Deflated Sharpe Ratio is
  already in the codebase and is the right tool.
- **Pre-register the boundary sensitivity.** Re-run with the growth/inflation sign threshold shifted by
  ±0.25 z-score and with the regime lagged one extra month. If the conclusion flips — as Neville et
  al.'s did — the regime signal is not carrying information, it is carrying dating choices.

---

## Source list

| Source | Type | Verified from |
|---|---|---|
| Daniel & Moskowitz (2016), "Momentum crashes," *JFE* 122(2) 221–247 | Peer-reviewed | Full text |
| Barroso & Santa-Clara (2015), "Momentum has its moments," *JFE* 116(1) 111–120 | Peer-reviewed | Published abstract |
| Cooper, Gutierrez & Hameed (2004), "Market States and Momentum," *JF* 59(3) 1345–1365 | Peer-reviewed | Full text |
| Chordia & Shivakumar (2002), *JF* 57(2) 985–1019 | Peer-reviewed | Published abstract |
| Griffin, Ji & Martin (2003), *JF* 58(6) 2515–2547 | Peer-reviewed | Abstract + citing texts |
| Frazzini & Pedersen (2014), "Betting against beta," *JFE* 111(1) 1–25 | Peer-reviewed | Full text (NBER w16601) |
| Blitz, van Vliet & Baltussen (2020), "The Volatility Effect Revisited," *JPM* 46(2) | Peer-reviewed | Published abstract |
| Neville, Draaisma, Funnell, Harvey & Van Hemert (2021), *JPM* 47(8) 8–37 | Peer-reviewed | Full text |
| Ilmanen, Israel, Lee, Moskowitz & Thapar (2021), *JOIM* forthcoming | Peer-reviewed (fc.) | Full text |
| Haddad, Kozak & Santosh (2020), "Factor Timing," *RFS* 33(5) 1980–2018 | Peer-reviewed | Full text |
| Nagel (2012), "Evaporating Liquidity," *RFS* 25(7) 2005–2039 | Peer-reviewed | Full text (NBER w17653) |
| Asness (2016), "The Siren Song of Factor Timing," *JPM* 42(5) | Peer-reviewed | Published abstract + AQR text |
| Asness, Chandra, Ilmanen & Israel (2017), *JPM* 43(5) 72–87 | Peer-reviewed | Published abstract |
| Kritzman, Page & Turkington (2012), *FAJ* 68(3) | Peer-reviewed | Published abstract |
| Polk, Haghbin & de Longis (2020), *JOIM* | Peer-reviewed | **Abstract only — full text unavailable** |
| Lo (2002), "The Statistics of Sharpe Ratios," *FAJ* 58(4) 36–52 | Peer-reviewed | Published abstract |
| Bridgewater, "The All Weather Story" | Primary practitioner doc | Full text |
| Dalio, "Engineering Targeted Returns and Risks" (2011) | Primary practitioner doc | Cited for framing only |

**Explicitly excluded:** trading blogs, ETF marketing material, and the several practitioner
"growth × inflation quadrant" write-ups that surfaced in search. Where a practitioner source is cited
above (Bridgewater), it is cited as evidence of *what that framework claims about itself*, not as
empirical support.

---

*Written 2026-08-19. Where a paper is marked "published abstract" above, the specific numbers quoted in
the body come from the abstract or from another paper's verbatim characterisation of it, and should be
re-verified against the full text before being relied on for a design decision.*

# F4 — LLM-native and alternative-data edges
Researched: 2026-08-27 | Researcher: subagent

## Bottom line (5 sentences max)

The headline result in this literature (Lopez-Lira & Tang, ChatGPT forecasting returns from
headlines) is real but was almost immediately shown by its own authors and by follow-on work
to be partly a memorization artifact, not pure reasoning — the correct reading is "some
genuine signal, inflated by an unknown but non-trivial amount of look-ahead bias," not "LLMs
predict stocks." The single most load-bearing methodological fact for this whole family is
that a rigorous 2025 study (Gao, Jiang & Yan) built a direct "lookahead propensity" measure
and found it explains roughly a third of the apparent predictive effect, with the contamination
concentrated exactly where the naive strategy looks best (small caps, older/famous headlines).
Filing-based and earnings-call NLP alphas (routine-vs-opportunistic Form 4, evasion/tone
scores) have cleaner out-of-sample pedigrees than headline-sentiment LLM work because they
predate LLMs and were re-validated, not invented, by them — LLMs mainly cut the cost of scoring
them at scale. A solo operator's realistic edge is not "smarter model," it is operating in
liquidity/coverage niches (micro-caps, unusual filings, cross-referencing many small signals)
that are structurally unprofitable for a fund to staff, not technologically inaccessible to one.
Inference cost is not the binding constraint at $1,000 of capital — a full daily universe scan
with a cheap model costs single-digit dollars a month — but building an actually contamination-free
backtest is the hard, slow part, and most of what's published has not done it rigorously.

## The look-ahead contamination problem (and how to design around it)

This is the central trap in the entire literature, and it is worse than ordinary backtest
overfitting because it is invisible from the outside: an LLM can appear to "predict" a 2019
stock move because it read the 2019 outcome (or commentary about it) during pretraining, not
because it inferred anything from the input you gave it at test time. Three things make this
insidious: (1) it doesn't require verbatim memorization of price data — memorizing correlated
text (later analyst commentary, Wikipedia summaries, news retrospectives) is enough; (2) it is
strongest exactly where naive backtests look best — famous, well-covered, heavily-discussed
names and periods, so a strategy that "works great on the S&P 500 back to 2015" is the most
suspect, not the most convincing; (3) larger/newer models with more training data and later
cutoffs are *more* contaminated, so "using a better/bigger model" can make a backtest look
better for exactly the wrong reason.

**Accepted mitigation methods, in order of rigor:**

1. **Strict post-cutoff, point-in-time testing.** Only evaluate on text dated after the specific
   model's training cutoff, using text as it existed at that time (not a later republished or
   corrected version). Lopez-Lira & Tang's own design intent was this — but the cutoff has to be
   *the actual model's* cutoff, not the paper's publication date, and the model must not have
   later been retrained/updated to move the cutoff forward mid-study. [reported]
2. **Membership-inference / "lookahead propensity" (LAP) testing** — directly estimate, per
   example, how likely that specific text sequence was memorized (e.g. by comparing the model's
   completion likelihood/confidence for the actual continuation vs. counterfactuals), then check
   whether predictive accuracy correlates with that likelihood. A positive correlation is direct
   evidence of contamination, and its magnitude tells you how much of your headline Sharpe to
   discount. This is the Gao/Jiang/Yan (2025) design — see T4.1 below. [reported]
3. **Entity-neutering / counterfactual substitution** — strip firm names, dates, and other
   identifying details from the prompt so the model cannot pattern-match to a memorized specific
   event, forcing it to reason from the informational content alone (Engelberg et al., 2025,
   per search summaries). [unverified — could not read primary]
4. **Cross-model disagreement as a contamination flag** — if multiple models with different
   training cutoffs/corpora agree strongly on a "surprising" prediction, that's more likely
   genuine signal; if only the model with training-data overlap gets it right, that's a red flag
   (this is the mechanism behind "MemGuard-Alpha," a 2026 defensive framework). [reported]
5. **Weakest and most common in practice: "we picked an out-of-sample date range."** This is
   necessary but not sufficient — see above, since text about pre-cutoff events can still leak
   forward via retrospective commentary published after the nominal cutoff, and because "cutoff"
   dates are themselves sometimes fuzzy/self-reported by the vendor.

**For our own backtest design, the concrete rule this implies:** never backtest an LLM-scored
signal on any period that materially precedes the *specific* model snapshot's training cutoff,
even by proxy (e.g. testing GPT-4o-class knowledge on 2021 headlines because "the paper did
it" is not a license to do it again on a different model with a different, and probably later,
cutoff). Where possible, prefer open-weight models with a documented, immutable cutoff and
frozen weights over hosted APIs that get silently upgraded, so the "cutoff" doesn't move under
you between backtest and later replication.

## Candidate theses

### T4.1 — LLM headline-sentiment signals carry genuine but heavily overstated predictive power; a lookahead-corrected version has real but much smaller edge than published
- **Evidence for:** Lopez-Lira & Tang (2023, *Journal of Financial Economics*, "Can ChatGPT
  Forecast Stock Price Movements?") analyzed headlines for ~4,100 US stocks Oct 2021–May 2024,
  chosen specifically to postdate GPT's then training cutoff; GPT-4-class scoring of headlines
  as positive/negative/neutral produced a long-short portfolio with statistically significant
  daily returns, and predictive power scaled with model size — GPT-1/2/BERT could not replicate
  it. [reported, multiple independent summaries converge on this]
- **Evidence against / contamination risk:** The same authors (Lopez-Lira, Tang & Zhu, 2025)
  followed up showing LLMs can memorize historical financial data from training sets — a
  self-correction of their own original design's residual risk. More decisively, **Gao, Jiang &
  Yan, "A Test of Lookahead Bias in LLM Forecasts" (SSRN #5985277, 2025)** built a formal
  "Lookahead Propensity" (LAP) statistic — the estimated likelihood a given headline/outcome
  pair was in the training corpus — and applied it to exactly this headline→return task. Result:
  a one-standard-deviation increase in the LLM's prediction signal corresponds to a 0.197%
  higher next-day return on average, but a one-SD increase in LAP *increases the marginal
  effect of that same LLM signal* by 0.077 percentage points — about **37% of the standalone
  effect is attributable to memorization, not inference**. The effect concentrates in small-cap
  stocks, where predictability looked strongest in the original literature, and survives
  controlling for the model's own token-level confidence. [reported — could not reach the SSRN
  or arXiv primary directly, both blocked by this environment's egress proxy; corroborated
  independently by "Summoning the Oracle to Slay It" (2026), which explicitly splits its
  evaluation into an in-sample 2010–2020 window that inflates returns via memorization and an
  out-of-sample 2025–2026 window beyond training cutoffs to quantify the gap — that paper's
  existence is itself evidence the field now treats the original result as partly contaminated
  by default.]
- **Why a solo operator can do this and a fund can't (or admit that they can):** A fund cannot
  publish or trade a headline-sentiment strategy without institutional-grade proof it isn't
  contaminated (compliance, investor due diligence). A solo operator can run the LAP-style
  correction themselves, trade the residual, small edge on a small account, and does not need
  the strategy to be big enough to matter to a fund's AUM — but this is a real edge, not a
  structural moat; any well-resourced desk with the same access to Bloomberg-adjacent tools
  could run the identical corrected pipeline. The actual structural advantage is closer to T4.4
  (universe size) than to any technique unique to a solo shop.
- **Data required (and cost):** Headline feeds (a keyless/cheap source — GDELT, or a scraped
  RSS aggregator — is enough for a pilot; a real-time low-latency feed costs more). LLM scoring
  of ~500–4,000 tickers/day at ~200–400 tokens per headline batch on Claude Haiku 4.5
  ($1/$5 per MTok input/output) costs on the order of **$5–$40/month** for a few-thousand-name
  universe scanned once daily — inference cost is not the binding constraint at this scale.
- **Kill test (runnable in under 1 day):** Take one week of real headlines for ~50 tickers,
  score them with an open-weight model whose training cutoff is *verifiably* before the
  headline dates (e.g. a Llama checkpoint with a documented, frozen cutoff, via Groq), and
  separately with the same model architecture fine-tuned/continued past that date. If accuracy
  on the "clean" pre-cutoff-relative-to-event model is statistically indistinguishable from
  chance, the published edge is mostly contamination for your setup and this thesis is dead for
  a live-capital deployment; if a small residual survives, proceed to T4.4's cost-of-competition
  question before building further.
- **Verdict: marginal.** Real effect, but the published magnitude is not what you'd get live,
  and confirming what fraction survives requires real engineering (a LAP-style test), not a
  weekend script.

### T4.2 — Insider-transaction (Form 4) "opportunistic trader" signals remain a real, LLM-uninvolved edge that an LLM can only help you scale, not create
- **Evidence for:** Cohen, Malloy & Pomorski, "Decoding Inside Information" (*Journal of
  Finance*, 2012; NBER WP 16454). They classify insiders as "routine" (trade in the same
  calendar month every year for several consecutive years) vs. "opportunistic" (everyone else).
  Routine-trader portfolios carry essentially zero abnormal return; **opportunistic-trader
  portfolios generate value-weighted abnormal returns of 82 basis points/month**, concentrated
  among local, non-executive insiders at geographically concentrated, poorly-governed firms.
  This is a pre-LLM, peer-reviewed, widely-replicated result — it is not vulnerable to the
  headline-sentiment contamination problem at all, because it is a rules-based classification on
  structured transaction data, not a language-model judgment call. [reported — NBER PDF host is
  blocked by this environment's proxy, could not read primary directly; the 2012 JF publication
  and its "routine vs. opportunistic" framework are extremely widely cited and cross-confirmed
  across independent secondary sources including Harvard Law's corporate governance blog]
- **Evidence against / contamination risk:** Not an LLM-contamination risk (this predates LLMs
  entirely) but a **crowding/latency risk**: Form 4 has a 2-business-day filing deadline and is
  now indexed within hours by many commercial trackers (secform4.com, alpharesearch.io, etc.),
  so the "routine vs. opportunistic" classification itself is now trivially automatable and
  likely already priced by anyone running the obvious screen. The original paper's alpha was
  measured on data through the 2000s; there is no independently-verified recent (2023–2026)
  replication in what was found here confirming the 82bp/month figure still holds post-crowding.
  [unverified — this recency gap is the key open question, not the original result]
- **Why a solo operator can do this and a fund can't (or admit that they can):** Mostly admit
  it: this is public, structured, cheap data (SEC EDGAR is free) and any fund can build the
  identical routine/opportunistic classifier. The plausible solo-operator angle is not the
  classifier itself but using an LLM to add a *qualitative* layer on top of the quantitative
  filter — e.g. cross-referencing the opportunistic insider's trade against same-week 8-Ks,
  news, and litigation filings to filter out already-known catalysts — a fusion task funds also
  do, but a solo operator can iterate on the exact fusion logic faster and cheaper than a
  committee-governed research process.
- **Data required (and cost):** SEC EDGAR Form 4 bulk data is free. Building the routine/
  opportunistic classifier is pure pandas, no LLM needed. If adding the LLM cross-reference
  layer: same cost order as T4.1, a few dollars to tens of dollars/month for a few hundred
  flagged opportunistic trades/month, since volume is low (not a daily full-universe scan).
- **Kill test (runnable in under 1 day):** Pull 2023–2025 Form 4 data from EDGAR, replicate the
  routine/opportunistic classification exactly as specified in the paper, and measure the
  20-day forward abnormal return of the opportunistic-only long portfolio against a sector-
  matched benchmark. If the spread has collapsed toward zero (plausible, given 15 years of
  crowding since publication), this thesis is dead as a standalone strategy and only survives as
  one input feature among several.
- **Verdict: marginal.** Structurally sound and cheap to test, but recency/crowding is the open
  question and this research pass could not verify a post-2020 replication.

### T4.3 — Earnings-call Q&A "evasiveness" (semantic distance between analyst question and executive answer) predicts returns and survives out-of-sample
- **Evidence for:** "The Language of Evasion: How Semantic Similarity Between Questions and
  Answers Predicts Stock Returns" (2026, *Journal of Investing* or a comparable outlet via
  Taylor & Francis; search-summarized) uses LLM embeddings to measure question/answer semantic
  alignment across earnings-call Q&A. Low-similarity ("evasive") answers were independently
  human-rated as evasive 67% of the time vs. 22% for high-similarity answers (a sanity check the
  measure is capturing something real, not noise), and the resulting long-short strategy on
  semantic alignment reportedly generated **3.9% annualized alpha (t = 3.41)**, described as
  robust to sentiment, firm characteristics, and market factors. Separately, Stanford GSB
  research on ML-scored managerial evasiveness across ~1,800 responses found evasiveness predicts
  future earnings misses and lower returns — an independent research group, independent method,
  same direction of effect. [reported — primary (tandfonline.com) blocked by this environment's
  proxy; could not verify the exact t-stat, sample period, or out-of-sample split firsthand]
- **Evidence against / contamination risk:** Earnings-call transcripts are *exactly* the kind of
  text an LLM is likely to have memorized if it postdates the transcript by any margin — a
  well-known company's Q1 2023 call is trivially findable in training data by 2024/2025. Unlike
  T4.1, no source found in this pass reports a LAP-style contamination test specifically applied
  to this earnings-call evasiveness measure — this is a real, unaddressed gap, and should be
  treated as an open risk, not a cleared one, until independently checked. Additionally, "tone/
  uncertainty in earnings calls predicts returns" is one of the oldest and most re-tested claims
  in accounting/finance NLP (dating to pre-LLM bag-of-words sentiment, e.g. Loughran-McDonald-era
  work) — some of the effect size may already be captured by non-LLM baselines, meaning the
  LLM's marginal contribution over a much cheaper keyword-based score is the real open question.
- **Why a solo operator can do this and a fund can't (or admit that they can):** Plausible edge:
  earnings-call transcripts are abundant but scoring 4,000+ small/mid-cap Q&A transcripts a
  quarter with an LLM is exactly the kind of "too much manual reading, not enough dollars to
  justify a research analyst" work that funds triage by market-cap coverage priority — an LLM
  pipeline lets a solo operator cover the long tail funds don't bother reading closely.
- **Data required (and cost):** Earnings call transcripts — commercial APIs (AlphaSense, Bigdata,
  or scraped investor-relations pages) cost real money for full coverage; free/cheap options
  (SEC's own automated transcripts where filed, some free aggregators) are patchier. LLM cost to
  embed+score ~150 transcripts/quarter (S&P 500-ish) at moderate length (~10-20k tokens each) on
  Haiku 4.5 is on the order of **$5–15/quarter** for the LLM call itself — transcript *access*,
  not inference, is the real cost driver here, plausibly $50-$300+/month depending on vendor.
- **Kill test (runnable in under 1 day, given transcript access):** Score 1 quarter of transcripts
  for ~50 names using both (a) an LLM postdating the transcripts by the shortest possible margin
  and (b) a simple non-LLM lexical-similarity baseline (e.g. TF-IDF cosine between Q and A). If
  the LLM version doesn't beat the cheap baseline out-of-sample, the "LLM-native" framing of this
  thesis is not earning its cost.
- **Verdict: promising**, conditional on running the contamination check this pass could not
  verify was ever done, and confirming the LLM beats a much cheaper lexical baseline.

### T4.4 — A solo operator's real structural edge is universe breadth and latency of iteration in under-covered small/micro-cap names, not model sophistication
- **Evidence for:** More than 17% of micro-caps carry zero sell-side analyst coverage, and 44%
  of the Russell Microcap Index has fewer than 2 analysts, versus ~17 analysts for an average
  large-cap name [reported]. Funds structurally avoid this space regardless of how good their
  models are: a meaningful position in a micro-cap can itself move the market, and the
  capital a large fund would deploy doesn't fit the float — this is a capacity constraint, not
  an information or modeling constraint, so it does not get competed away by funds simply hiring
  more LLM-savvy analysts. [reported, cross-confirmed by asset-manager whitepapers with an
  obvious promotional interest in the claim — discount accordingly, but the capacity-constraint
  mechanism itself is basic and uncontroversial market-structure logic, not a contestable
  empirical claim]
- **Evidence against / contamination risk:** This is a real structural argument, not an LLM
  finding, so "look-ahead bias" doesn't directly apply — but a different failure mode does:
  micro-caps are illiquid, thinly-traded, and prone to manipulation/pump-and-dump patterns, so
  "no analyst coverage" often means "no coverage because trading it isn't viable at any
  meaningful size," not "hidden gem." Survivorship and liquidity-filtering biases are severe in
  any backtest here — a strategy that looks great on illiquid names frequently cannot actually
  be executed at the sizes and slippage assumed. No academic source in this pass quantifies
  *LLM-specific* alpha in this space (as opposed to the general small-cap factor premium, which
  is a much older, heavily-studied — and currently debated/weak — anomaly).
  [unverified for the LLM-specific claim]
- **Why a solo operator can do this and a fund can't (or admit that they can):** This is the
  cleanest genuine structural advantage in this whole research pass: a $1,000–$25,000 account
  can take a position in a name where a $500M fund cannot take a position large enough to matter
  to its returns, even if the fund's research is superior. The edge is capacity, not
  intelligence — a solo operator's LLM pipeline doesn't need to out-think a fund, it needs to
  cover ground (thousands of thinly-covered filings/transcripts/news items) a fund's analyst
  headcount economics won't justify staffing.
- **Data required (and cost):** Same order as T4.1/T4.2 — EDGAR filings are free, small-cap
  news/filings volume is lower than large-cap so LLM scoring cost is if anything cheaper per
  name; total is plausibly **under $20/month** for daily scanning of a few thousand micro/small-
  cap names on Haiku-tier pricing. The real cost is data *engineering* time, not API spend.
- **Kill test (runnable in under 1 day):** Build a liquidity-realistic backtest (actual bid-ask
  and volume-capped position sizing, not close-to-close returns) on any candidate small-cap
  signal from T4.1–T4.3 restricted to the under-covered universe, and compare Sharpe with and
  without realistic slippage/impact assumptions. If the edge only survives at unrealistic fill
  assumptions, this thesis collapses into "small-cap factor investing with extra steps," not an
  LLM-native or structural edge.
- **Verdict: promising** as the meta-level answer to "where can a solo operator actually win,"
  but it is a market-structure thesis that any of T4.1–T4.3's signals should be *run inside*,
  not a standalone strategy of its own.

### T4.5 — 13F-copycat and filing-latency strategies are mostly arbitraged away; any residual edge is in manager selection (which fund to copy), not filing speed
- **Evidence for:** Aiken et al. (2013, per search summary) found copycat portfolios built from
  historically top-performing managers' 13F holdings deliver alpha even after the mandatory
  45-day reporting lag — the edge survives the delay because it's riding manager skill, not
  fresh information. [reported]
- **Evidence against / contamination risk:** The 45-day lag means high-turnover funds' 13F
  snapshots are largely stale noise by the time they're public — the position may already be
  closed. More importantly, popular 13F picks now reportedly see immediate price appreciation
  on disclosure as more participants automate the copy-trade, compressing the window during
  which following the filing itself (as opposed to the underlying manager's ongoing skill) adds
  anything. [reported] This is not an LLM-contamination issue but a crowding-decay issue —
  structurally similar to T4.2's risk.
- **Why a solo operator can do this and a fund can't (or admit that they can):** Weak case for a
  distinct solo advantage here — this is public data anyone can automate, and the "which
  managers are worth copying" judgment call (an LLM could plausibly help synthesize a manager's
  letters/13Ds/interviews to build a qualitative skill prior) is exactly the kind of thing large
  data vendors (Novus, Bigdata) already productize and sell to funds.
- **Data required (and cost):** 13F data is free from EDGAR; commercial aggregation (Whale
  Wisdom-style tools) costs money for convenience but isn't required. LLM cost to synthesize a
  manager's qualitative track record from letters/interviews is a one-time-per-manager cost,
  not a recurring universe scan — negligible, low tens of dollars total for a manager shortlist.
- **Kill test (runnable in under 1 day):** Backtest a simple copy-the-top-decile-13F-managers
  strategy on 2020–2024 data with realistic 45-day-lag entry and reasonable transaction costs;
  compare to a market-cap-matched benchmark. If it doesn't clear the benchmark net of costs on
  recent data (not the original paper's older sample), the thesis is dead as a standalone play.
- **Verdict: marginal**, and the "LLM-native" framing barely applies — this is closer to F1/F2
  factor-investing territory (see other researchers' tracks) than an LLM-specific edge.

## Sources
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788 — Lopez-Lira & Tang, "Can ChatGPT
  Forecast Stock Price Movements?" (blocked by this session's proxy; cited via search summaries
  and cross-confirmed by multiple independent secondary descriptions of the same abstract/dates)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5985277 — Gao, Jiang & Yan, "A Test of
  Lookahead Bias in LLM Forecasts" (blocked by proxy; the Lookahead Propensity result and the
  0.197%/0.077% figures came from search-engine summarization of this paper's abstract/results,
  not a direct read — treat the exact figures as [reported], not [verified])
- https://www.nber.org/system/files/working_papers/w16454/w16454.pdf — Cohen, Malloy & Pomorski,
  "Decoding Inside Information" (blocked by proxy; 82bp/month figure and routine/opportunistic
  definition via search summaries, cross-confirmed against the Journal of Finance publication
  record and Harvard Law corpgov blog coverage)
- https://corpgov.law.harvard.edu/2012/02/03/decoding-inside-information/ — secondary summary of
  the same Cohen/Malloy/Pomorski paper
- https://www.tandfonline.com/doi/full/10.1080/15427560.2026.2657322 — "The Language of Evasion"
  (blocked by proxy; alpha figure and t-stat via search summary only)
- https://www.sec.gov/ — EDGAR (Form 4, 13F, 8-K filing mechanics and full-text search
  capabilities/limits) — accessed indirectly via search-summarized documentation, not a direct
  primary-source browse of EDGAR's own docs
- Anthropic `claude-api` skill (bundled reference, cached 2026-06-24) — authoritative current
  Claude API pricing table (Haiku 4.5 $1/$5, Sonnet 5 $2/$10, Opus 5 $5/$25 per MTok in/out) used
  for the inference-cost estimates in every thesis above [verified — read directly, not via web
  search]
- Search-aggregated Groq API pricing (Llama 3.1 8B ~$0.05/MTok input; Llama 3.3 70B ~$0.59/$0.79
  per MTok in/out; batch pricing ~50% off) — [reported], not independently verified against
  Groq's own pricing page (not fetched directly this pass)
- Search-aggregated microcap analyst-coverage statistics (17%+ zero coverage, 44% <2 analysts in
  Russell Microcap) — [reported], sourced from asset-manager whitepapers with a promotional
  interest in the claim; the underlying capacity-constraint logic is treated as more reliable
  than the specific percentages

**Note on this pass's limitations:** arxiv.org, mdpi.com, and thequantuminsider.com were blocked
per instructions. In addition, this environment's egress proxy also blocked SSRN
(papers.ssrn.com), NBER (nber.org), Wharton's Jacobs Levy Center, Semantic Scholar, ResearchGate,
and Taylor & Francis (tandfonline.com) — meaning **every primary academic source cited above was
read only through search-engine-summarized abstracts, not the actual paper**. This is weaker
verification than the brief's [verified] tag requires and is flagged as [reported] throughout for
that reason. Before committing capital or further engineering to any thesis above, the primary
sources should be obtained directly (e.g. via a university library proxy, Google Scholar cache,
or asking the user to pull the PDF) rather than relying on this pass's search summaries.

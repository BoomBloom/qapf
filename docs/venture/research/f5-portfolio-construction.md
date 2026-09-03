# F5 — Is portfolio construction itself an edge?
Researched: 2026-08-27 | Researcher: subagent

## Bottom line — does combinatorial optimization add out-of-sample Sharpe? (direct answer required)

**No — not the combinatorial part, and not at this account's scale.** Across four decades of
literature the pattern is consistent: the piece of portfolio construction that measurably beats
naive approaches out of sample is **better covariance estimation** (shrinkage), which is a
*statistical* fix, not a *combinatorial* one. The genuinely NP-hard pieces — exact cardinality
selection, integer lot sizing, exact turnover/transaction-cost optimization — are ones where
**cheap classical heuristics already capture ~99%+ of the achievable objective value**, and no
published evidence shows solving them *exactly* (via MIP, QUBO, quantum annealing, or QAOA)
produces a statistically distinguishable out-of-sample Sharpe improvement over a good heuristic.
The strongest single data point is Jagannathan & Ma (2003): imposing a crude, "wrong" constraint
(no short-selling — which is also a *combinatorial*, not continuous, restriction) achieves
**the same out-of-sample risk reduction as sophisticated shrinkage/factor covariance estimators**,
because the constraint itself acts as regularization against estimation error. QAPF's optimizer
is already long-only and already uses Ledoit-Wolf shrinkage — i.e., it already captures the two
interventions the literature can actually defend.

**At $1,000–$100,000 with 5–20 positions, this conclusion gets stronger, not weaker.** The
combinatorial search space at that scale (choose k of ~30–50 liquid candidates) is small enough
to brute-force or greedily solve in milliseconds — there is no "hard problem" for an advanced
solver to be needed for. Meanwhile estimation error — the thing DeMiguel et al. show swamps
optimization sophistication — gets *worse* per-position at small N and short lookback windows,
which is exactly the regime a $1,000 account lives in. So the account size where combinatorial
sophistication would in principle matter most (very large N, hundreds to thousands of assets,
institutional index construction / index tracking) is the opposite end of the spectrum from where
this venture operates.

**Conditions under which the answer would flip to "yes, it can matter":** (1) N in the hundreds+
where exact cardinality selection is genuinely intractable for brute force and heuristics start
measurably degrading; (2) tight, binding turnover/tax-lot constraints across many rebalance
periods where the gap between a myopic single-period policy and the true multi-period optimum
widens; (3) transaction costs large relative to expected edge, where cost-aware sizing (not
cardinality per se) starts to dominate returns. None of these describe a 5–20-name, long-only,
$1,000–$100,000 book. A "quantum-inspired combinatorial optimizer" for this venture would be
solving a problem that is not actually hard at this scale, using more machinery than the problem
needs — decoration, not edge.

---

## The 1/N challenge and what happened to it

**DeMiguel, Garlappi & Uppal (2009), "Optimal Versus Naive Diversification: How Inefficient Is
the 1/N Portfolio Strategy?"** (Review of Financial Studies 22(5)): tested 14 mean-variance-style
optimizing models (sample-based MV and extensions built to reduce estimation error — Bayesian
shrinkage, moment restrictions) against naive equal-weighting, across 7 empirical datasets. **None
of the 14 was consistently better than 1/N** on Sharpe ratio, certainty-equivalent return, or
turnover, out of sample. [reported — consistent across SSRN abstract, Oxford Academic abstract,
and multiple secondary summaries; primary PDF was not directly fetchable, SSRN/NBER/Oxford are
blocked by this session's egress proxy]

Their calibrated estimate of the estimation window needed for a sample-based MV strategy to
reliably beat 1/N: **~3,000 months for a 25-asset universe, ~6,000 months for 50 assets.**
[reported] That is 250–500 years of data — the paper's core point is that estimation error, not
optimization inadequacy, is the binding constraint, and it does not shrink fast enough with more
sophisticated point estimates alone.

**Has this been overturned since?** Partially, and specifically:

- **Yuan & Zhou (2024), "Why Naive 1/N Diversification Is Not So Naive, and How to Beat It?"**
  (JFQA): 1/N is *provably* optimal in a one-factor model with fully diversifiable idiosyncratic
  risk as N grows, regardless of sample size — it isn't naive, it's the correct answer under a
  real structural assumption. Their proposed way to beat it is **combining** 1/N with an
  estimated strategy (shrinking toward 1/N rather than replacing it), which helps when N is small,
  and blending with anomaly/ML-based signals when N is large. [reported] This is a partial
  concession that 1/N is hard to beat *on its own terms*, not a reversal of DeMiguel's finding.
- **Jagannathan & Ma (2003), "Risk Reduction in Large Portfolios: Why Imposing the Wrong
  Constraints Helps"** (Journal of Finance): a non-negativity (no-short) constraint on a plain
  sample-covariance minimum-variance portfolio performs **as well out of sample as** portfolios
  built from factor models, shrinkage estimators, or daily (higher-frequency) covariance data.
  Mechanism: the constraint implicitly shrinks the large off-diagonal covariance terms that drive
  estimation-error-amplified opposite-signed weight pairs. [reported — corroborated across
  multiple independent secondary sources including a published "Note on..." erratum/extension]
  This is arguably the single most important finding for this venture: **a combinatorial-flavored
  restriction (no shorting → binary in/out of the short side) did the same job as continuous
  statistical sophistication.**
- **Constraint-based regularization more broadly**: "Portfolio Constraints: An Empirical Analysis"
  found that constrained strategies derived from equal-weighting (min-variance-with-constraints,
  max-Sharpe-with-constraints) were among the best out-of-sample performers, and that constrained
  vs. unconstrained variance differences were statistically significant. [reported]
- **Hierarchical Risk Parity (López de Prado, 2016)**: avoids matrix inversion entirely, uses
  hierarchical clustering + recursive bisection instead of a covariance-inverse-based optimizer.
  Evidence is genuinely mixed: some studies find HRP produces **lower out-of-sample variance than
  the Critical Line Algorithm** (mean-variance) even on CLA's own home objective (min-variance);
  others find **1/N outperforms HRP across all tested setups**, and HRP is "sub-optimal under
  certain market conditions." [reported, both directions] HRP is not a clean win over 1/N; it is
  a clean win over naive mean-variance in some studies and a wash or loss against 1/N in others.

**Verdict on the 1/N challenge:** not overturned in the strong sense DeMiguel posed it (beat 1/N
reliably with a sophisticated *point-estimate* optimizer). What *has* been shown to work is
**regularization** — shrinkage, constraints, or structure that reduces the effective number of
free parameters being estimated — which is a different lever than "solve the optimization problem
better." Combinatorial sophistication (exact cardinality/integer solving) is not this lever; it
adds parameters (which subset, which integers) rather than removing them.

---

## Where convex solvers genuinely fail (the NP-hard cases)

1. **Cardinality constraints** ("hold exactly k of n assets," `‖w‖₀ ≤ k`): genuinely
   non-convex/combinatorial. Standard formulation requires a mixed-integer quadratic program
   (binary indicator variables). "Efficient algorithms do not exist" in the worst case; this
   motivated decades of heuristic research (genetic algorithms, tabu search, simulated annealing).
   [reported]
2. **Minimum position sizes / semicontinuous constraints** (a position is either 0 or between
   some floor and ceiling): also requires binary/semicontinuous integer variables layered on top
   of cardinality — MATLAB's own portfolio toolbox documents this as a distinct MIP-requiring
   feature. [reported]
3. **Integer share/round-lot constraints**: shown to be **NP-complete** even just to find a
   *feasible* solution once realistic per-share rounding is imposed, let alone an optimal one.
   [reported]
4. **Turnover / transaction-cost penalties in the objective**: convex when costs are linear or
   quadratic in trade size (standard QP/SOCP extensions handle this fine — this is *not* actually
   one of the hard cases on its own). It becomes hard only when *combined* with cardinality/integer
   constraints (i.e., "trade an integer number of round lots of at most k names, minimizing
   quadratic cost") — the hardness comes from the discreteness, not the transaction-cost term
   itself. [reported — inferred from solver documentation describing linear/quadratic
   transaction-cost terms as standard convex QP/SOCP extensions with no MIP backend required;
   not independently run in this session]

**Does solving these exactly beat solving them well heuristically?** The literature answer is
close to "no, not by a measurable amount out of sample":

- On the classic transaction-cost-and-round-lots problem, a well-designed heuristic (solving a
  relaxed subproblem, then rounding) achieved a solution that **"nearly coincides with the exact
  solution"** while using **"about one-thousandth the computational effort,"** and the authors
  concluded the gap to the true global optimum "would only yield a small improvement over the
  heuristic." [reported]
- Comparative studies of metaheuristics for cardinality-constrained efficient frontiers (Hopfield
  networks, genetic algorithms, tabu search, simulated annealing) found **none consistently
  outperformed the others**, i.e., the frontier is not sensitive to which near-optimal method you
  pick. [reported]
- Simulated annealing on a realistic 151-US-stock cardinality/quantity/pre-assignment-constrained
  problem converged to the efficient frontier **in under 10 seconds**. [reported]
- For exact MIP: CVXPY-compatible solvers (Gurobi, SCIP, CP-SAT) do solve these formulations, but
  users report Gurobi failures/instability as constituent count scales up inside CVXPY, and
  benchmark studies of one-cardinality-constraint QPs show **time-to-solution scaling exponentially,
  hitting timeouts around n≈200 on random covariance instances** (real S&P 500-derived instances
  did not hit timeout at tested sizes, i.e., real covariance structure is easier than adversarial
  random instances). [reported]
- Quantum/quantum-inspired specifically: this project's own prior research (§1 of the venture
  research log, and QAPF's Agent 5) already established QAOA/quantum annealing are **beaten by
  classical heuristics within a 60-second budget** on real-world-scale instances, and that Agent
  5's own QAOA run took **~13,000× longer than brute force** on a trivial 6-name problem while
  reaching the identical answer. [verified — our own run] A 2026 benchmark explicitly comparing
  quantum annealing and QAOA against classical MIP, simulated annealing, steepest-descent, and
  tabu search on real-world portfolio instances is consistent with this: quantum methods get
  "close to the exact optimum" but do not establish an advantage, and D-Wave's own strongest 2026
  claims are about quantum *simulation*, not optimization. [reported]

**Conclusion for this section:** the NP-hard constraints are real and convex solvers truly cannot
handle them directly. But the *gap between heuristic and exact* on realistic (non-adversarial)
problem sizes is small enough that no source found here shows it surviving contact with
out-of-sample noise. The hard part of the problem is provably solvable near-exactly, cheaply, by
2003-era classical heuristics; that was never the bottleneck.

---

## Classical baselines that any 'advanced' method must beat

| Method | Problem size handled | Time | Availability |
|---|---|---|---|
| Brute-force / exhaustive enumeration | n≤~20-25 choose k, trivial | milliseconds–seconds | any language, no dependency |
| Greedy / relaxed-then-round heuristic (continuous relaxation, round to integers) | Hundreds of assets | seconds; ~1000x less compute than exact MIP for near-identical quality [reported] | any QP solver |
| Simulated annealing (bespoke, e.g. cardinality+quantity+pre-assignment) | ~150 assets, multiple constraint types | under 10 seconds [reported] | open source (scipy, custom) |
| CVXPY + open-source MIP backend (SCIP, CP-SAT via OR-Tools) | CP-SAT reported to clear 50/50 benchmark instances within 180s where SCIP/BOP/CBC did not; general cardinality-QP instances scale to timeout near n≈200 on adversarial random covariance, larger on real market data [reported] | seconds–minutes | free, `pip install ortools` / `cvxpy[SCIP]` |
| Gurobi (free academic / restricted trial tier) | Institutional-scale MIQP, hundreds–low thousands of assets, subject to license limits | seconds–minutes typical | free for academics; commercial license otherwise |
| Quantum annealing (D-Wave) / QAOA (Qiskit) | Small (tens of variables) before noise/embedding overhead dominates; hybrid solvers claim larger | Comparable-to-slower than classical on real instances; QAOA gate-count blows up with size [verified/reported, per venture log §1] | free tier access exists; **not faster or better in evidence reviewed** |

**Any candidate "quantum-inspired" method for this venture must beat row 2 or row 3** (a
relax-and-round heuristic or a bespoke simulated annealer), not brute force, and not "exact MIP
under an unlimited time budget" — because at $1,000–$100,000 scale (n≈5–20 held positions out of
a candidate universe of maybe 30–100 liquid names), rows 1–3 already run in well under a second
and are not the constraint on strategy performance.

---

## Transaction-cost-aware and multi-period optimization

Boyd, Busseti, Diamond, Kahn, Koh, Nystrup & Speth (2017), "Multi-Period Trading via Convex
Optimization": frames the general multi-period problem as trading off return, risk, transaction
cost, and holding cost, solved via convex optimization at each rebalance using either a full
look-ahead or a practical single-period-with-planning-horizon policy. Their own assessment of the
gap between the (cheaper, myopic) practical policy and the true dynamic-programming optimum:
**"the performance loss is likely very small in practical problems,"** backed by a numerical
bounding method that quantifies it. [reported] This is a documented, credible claim of a real but
*modest* benefit from full multi-period sophistication over well-designed single-period
transaction-cost-aware rebalancing — not a case for needing combinatorial/quantum machinery.

Separately, no-trade-region / tolerance-band rebalancing (act only when drift exceeds a threshold)
is well-established as capturing most of the benefit of continuous rebalancing at a fraction of
the trading cost: the optimal no-trade region width scales with transaction costs and volatility,
and one study found **1.5% annualized return lost to over-frequent rebalancing** versus a
threshold-band approach. [reported] This reinforces the pattern: **being transaction-cost-aware
matters and is cheap to implement (a no-trade band, or a linear/quadratic cost term in a standard
convex QP); solving the *exact* multi-period combinatorial optimum does not add much beyond that.**

---

## The small-account angle

At $1,000, holding 5–20 positions with real per-share pricing and round-lot constraints:

- The **candidate universe** for a retail account is necessarily small (liquid, reasonably priced
  large/mid-caps or ETFs — not the full Russell 3000). A realistic "choose k of n" problem is
  n≈30–100, k≈5–20. This is squarely inside the range brute force and greedy heuristics solve in
  milliseconds (see table above); it is nowhere near the n≈200+ region where reported MIP
  time-to-solution starts to blow up.
- **Estimation error gets worse, not better, at this scale.** DeMiguel's core mechanism —
  optimization gains overwhelmed by parameter noise — is driven by the ratio of assets/parameters
  to usable data. A small, concentrated, frequently-rebalanced retail book has *less* data per
  decision (shorter practical lookback, fewer independent return observations per name) than an
  institutional book with decades of data across hundreds of names. So the paper's central warning
  applies *more* forcefully here, not less.
- **Integer share/lot constraints are a real, binding nuisance at $1,000** — but they are a
  "genuinely hard NP-complete-to-find-feasible" problem only in the worst case; in practice, at
  n≈5–20 positions with a fixed budget, a greedy fill-largest-then-adjust heuristic is exact or
  within a rounding error's worth of exact, checkable by brute force in the same breath.
  Fractional-share brokers (increasingly standard) remove this constraint almost entirely, further
  shrinking any role for a combinatorial solver.
- **Net read:** cardinality/integer constraints are *more visibly binding* at $1,000 (you can
  literally see the account has too few dollars to hold 20 full-lot names) but *less
  computationally hard* to actually solve at this n — the two effects point in opposite
  directions, and the computational-hardness one is what would justify quantum/quantum-inspired
  machinery. It doesn't, at this n.

---

## Candidate theses

### T5.1 — Long-only + shrinkage already captures the regularization benefit; adding exact cardinality solving on top adds no further measurable Sharpe
- Evidence for: Jagannathan & Ma (2003) — no-short constraint alone matches shrinkage/factor-model
  performance [reported]. QAPF's allocator is already long-only + Ledoit-Wolf shrunk.
- Evidence against: Jagannathan-Ma's result is about a *continuous* constraint (weights ≥ 0), not
  a cardinality constraint (exactly k nonzero); it is suggestive, not identical evidence.
- Does it matter more or less at $1k–$100k scale? Matters less — the marginal regularization from
  *exact* cardinality solving vs. a greedy top-k-by-signal selection is unlikely to be
  distinguishable from noise at n≈5–20.
- Kill test (runnable in under 1 day): Using QAPF's existing Agent 6→7→2 pipeline and Agent 9's
  backtest harness, run three variants over the same 2018–2020 window: (a) current Ledoit-Wolf +
  long-only allocator, (b) same but with top-k signal names pre-selected greedily then optimized,
  (c) same universe with a MIP-exact cardinality solve (OR-Tools CP-SAT, free). Compare DSR-adjusted
  Sharpe across the three. If (b) and (c) are statistically indistinguishable, thesis confirmed.
- Verdict: promising as a *negative* result to confirm (i.e., promising evidence *against* building
  a combinatorial optimizer) — this is the highest-value cheap test to run before any quantum work.

### T5.2 — Covariance shrinkage is the one lever with a real, replicable out-of-sample Sharpe gain, and QAPF already has it
- Evidence for: Ledoit-Wolf shrinkage measurably reduces realized out-of-sample volatility vs.
  sample covariance [reported]; nonlinear shrinkage adds a further ~10–15% Sharpe improvement over
  linear shrinkage specifically when N is much smaller than T [reported].
- Evidence against: nonlinear shrinkage's biggest gains are shown when N ≪ T (many years of daily
  data relative to few assets) — at $1,000 scale with n≈5–20 and realistic lookbacks, N is already
  small relative to T, so QAPF may already be near the regime where linear shrinkage captures most
  of the available gain and nonlinear adds little extra. [unverified — needs a direct backtest]
- Does it matter more or less at $1k–$100k scale? Matters, but with diminishing extra room — the
  jump from *no* shrinkage to Ledoit-Wolf (already done) is the big win; the jump from linear to
  nonlinear shrinkage is a second-order refinement.
- Kill test (runnable in under 1 day): Swap Agent 2's Ledoit-Wolf covariance for `sklearn`'s
  nonlinear shrinkage (or Ledoit-Wolf's own published analytical nonlinear estimator) in an
  otherwise identical backtest; compare realized out-of-sample volatility and DSR. A gain under
  ~0.05 Sharpe is not worth the added complexity at this N.
- Verdict: marginal upside on top of what's already built — worth a cheap test, not a rebuild.

### T5.3 — Exact/quantum combinatorial solving of cardinality+lot+turnover constraints does not beat classical heuristics by a measurable out-of-sample margin at any tested scale
- Evidence for: heuristic-vs-exact gap on realistic transaction-cost-and-lots problems is "about
  one-thousandth the computational effort" for "nearly coincid[ing]" quality [reported]; no
  metaheuristic consistently beats others [reported]; QAOA/quantum annealing beaten by classical
  heuristics within realistic time budgets on real-world instances [reported, corroborated by
  QAPF's own Agent 5 run — verified].
- Evidence against (strongest counter-evidence): time-to-solution for exact cardinality-QP
  formulations is reported to scale exponentially and can hit timeouts near n≈200 on adversarial
  random-covariance instances [reported] — so there *does* exist a regime (large n, adversarial
  correlation structure) where exact solving becomes genuinely hard and a heuristic's gap to
  optimal could plausibly widen. This venture's n (~5–20 of ~30–100) is far below that regime, but
  the counter-evidence means the thesis is scale-conditional, not universal.
- Does it matter more or less at $1k–$100k scale? Matters much less — this venture's n never
  approaches the regime where the counter-evidence bites.
- Kill test: same as T5.1's kill test, plus timing each solver; if CP-SAT/greedy both return in
  under a second at this venture's realistic n, there is no latency or quality case for anything
  more exotic.
- Verdict: dead, specifically as a claim that combinatorial exactness (let alone quantum) helps at
  this venture's scale. Would need re-litigating only if the strategy ever needs n in the hundreds
  (e.g., a factor-neutral long-short book spanning a broad index) — not on today's roadmap.

### T5.4 — Full multi-period transaction-cost optimization beats no-trade-band + shrinkage-based single-period rebalancing by a modest, not transformative, margin
- Evidence for: no-trade-band rebalancing already captures most of the cost-avoidance benefit
  cheaply [reported]; Boyd et al.'s own paper states the performance loss from their practical
  (myopic) policy vs. the true multi-period optimum is "likely very small in practical problems"
  [reported].
- Evidence against: Boyd et al. only *bound* the loss, they do not claim it is zero, and the bound
  is problem-dependent — a strategy with very high turnover or very tight tax/lot constraints could
  see a larger gap. No source reviewed here quantifies this gap in Sharpe terms for a small
  long-only retail book specifically. [unverified]
- Does it matter more or less at $1k–$100k scale? Likely matters less — a small book has fewer
  independent rebalance decisions and lower absolute transaction costs in dollar terms (though
  higher in *percentage* terms if trading in small, non-round lots), so the multi-period gap has
  less room to compound.
- Kill test: run QAPF's existing pipeline with (a) current single-period rebalance-then-optimize
  vs. (b) a simple no-trade-band overlay vs. (c) a short-horizon (2–3 period) look-ahead convex
  reoptimization; compare net-of-cost Sharpe over the same backtest window.
- Verdict: marginal — worth the cheap no-trade-band version (b), not worth building a full
  multi-period solver (c) without first seeing (b) leave a measurable gap.

### T5.5 — Cardinality binds harder at $1,000 in a *visible* sense (can't afford 20 full lots) but is *computationally trivial* to solve at this n, so the binding constraint at this account size argues against, not for, combinatorial sophistication
- Evidence for: candidate universe + target k at retail scale (n≈30–100, k≈5–20) is well inside
  brute-force/greedy territory (table above); DeMiguel's estimation-error problem gets worse, not
  better, at small N and short lookback [reported, extrapolated from the mechanism].
- Evidence against: if this venture later trades from a much larger candidate universe (e.g.
  screening hundreds of small-caps for a stat-arb basket) while still holding only 5–20 positions,
  the *selection* problem (choose k of n) could scale into the harder regime even though the
  *held* portfolio stays small. That case is not tested here.
- Does it matter more or less at $1k–$100k scale? Less, under the current architecture (Agent 7's
  candidate universe is not in the hundreds).
- Kill test: check Agent 7/Agent 2's actual current candidate-universe size; if n stays under ~50,
  this thesis is confirmed by construction and needs no further backtest.
- Verdict: promising as a scoping decision (tells us *not* to build combinatorial machinery yet),
  contingent on candidate-universe size staying small — cheap to verify by reading the code, not
  even a backtest.

---

## Sources
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1376199 — DeMiguel, Garlappi & Uppal (2009), "Optimal Versus Naive Diversification" — 14 models vs 1/N, none consistently better out of sample; estimation-window-to-beat-1/N figures (blocked by proxy, summary via search only)
- https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901 — same paper, RFS publication record
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3991279 — Yuan & Zhou, "Why Naive 1/N Diversification Is Not So Naive, and How to Beat It?" (JFQA) — 1/N optimality under one-factor model; combination strategies to beat it
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=310469 — Jagannathan & Ma (2003), "Risk Reduction in Large Portfolios: Why Imposing the Wrong Constraints Helps" — no-short constraint matches shrinkage/factor-model performance
- https://afajof.org/wp-content/uploads/Risk-reduction-Jagannathan-erratum.pdf — corroborating note on the Jagannathan-Ma result
- http://www.ledoit.net/Goldilocks_RFS_2017.pdf — Ledoit & Wolf, nonlinear shrinkage for Markowitz portfolio selection
- http://www.ledoit.net/Review_Paper_2020_JFEc.pdf — Ledoit & Wolf, "The Power of (Non-)Linear Shrinking" review
- https://www.mdpi.com/2227-7072/10/1/9 / https://www.researchgate.net/publication/357996709_Portfolio_Constraints_An_Empirical_Analysis — "Portfolio Constraints: An Empirical Analysis" — constrained strategies derived from 1/N perform best out of sample
- https://www.researchgate.net/publication/305747867_Building_Diversified_Portfolios_that_Outperform_Out_of_Sample — López de Prado, HRP outperforms CLA/min-variance out of sample
- https://en.wikipedia.org/wiki/Hierarchical_Risk_Parity — HRP background and mixed-evidence summary (some studies: 1/N beats HRP)
- https://gurobi-finance.readthedocs.io/en/latest/literature.html — Gurobi's own cardinality-constrained portfolio literature/background
- https://github.com/cvxpy/cvxpy/issues/1247 — reported Gurobi/CVXPY scaling failure on larger constituent counts
- https://link.springer.com/article/10.1023/A:1019279918596 — "Selecting Portfolios with Fixed Costs and Minimum Transaction Lots" — heuristic ~1000x cheaper, near-exact quality
- https://faculty.washington.edu/mfazel/portfolio-final.pdf / https://web.stanford.edu/~boyd/papers/pdf/portfolio_submitted.pdf — Boyd et al., portfolio optimization with linear/fixed transaction costs
- https://web.stanford.edu/~boyd/papers/pdf/dyn_port_opt.pdf — Boyd, Skaf et al., multi-period portfolio optimization with constraints and transaction costs; myopic-vs-optimal loss "likely very small"
- https://arxiv.org/abs/1705.00109 (title/abstract only, arxiv.org PDF blocked) — Boyd, Busseti, Diamond et al., "Multi-Period Trading via Convex Optimization"
- https://www.aqr.com/-/media/AQR/Documents/Whitepapers/AQR_Portfolio-Rebalancing_Common-Misconceptions.pdf — no-trade-band vs periodic rebalancing tradeoffs
- QAPF venture research log §1 (`docs/venture/10-research-log.md`) and `backend/agents/quantum/` (Agent 5) — this project's own verified run: QAOA found the correct cardinality-constrained subset but took ~13,000x longer than brute force on a 6-name problem; independent confirmation of the classical-heuristic-wins pattern
- https://d-krupke.github.io/cpsat-primer/ — OR-Tools CP-SAT solver capability/benchmark context
- Note: this session's egress proxy denies essentially every primary research host by policy
  (confirmed elsewhere in the venture research log, §0 of `10-research-log.md`) — arxiv.org,
  mdpi.com, thequantuminsider.com per task instructions, plus in practice SSRN, NBER,
  ScienceDirect, ResearchGate, Oxford Academic, and Springer. Every finding above that is not
  QAPF's own code/run is therefore `[reported]` — a WebSearch-synthesized summary of a primary
  source, not a directly fetched and read primary text. **Re-verify against primaries from a
  session with open network access before any thesis here drives architecture decisions.**

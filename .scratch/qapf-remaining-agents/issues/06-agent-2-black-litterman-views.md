# 06 — Agent 2 (cont.): Black-Litterman views from Agent 7 signals

**What to build:** A principled way to turn Agent 7's signals into an expected-return vector, instead of
feeding raw signal scores into the optimizer as if they were returns. Black-Litterman starts from
market-implied equilibrium returns and tilts them by the strength and confidence of stated views — which
maps unusually well onto what Agent 7 already emits, since every `AlphaSignal` carries both a `signal`
and a `confidence` (factor agreement). Confidence becomes view uncertainty; the signal becomes the view.

Why this is worth doing rather than skipping: a rank-normalized signal in `[-1, +1]` is not an expected
return, and treating it as one silently makes the optimizer's risk/return tradeoff meaningless. Ticket 05
gets allocation working; this ticket makes the inputs to it defensible.

Split from ticket 05 deliberately — 05 is demoable without this, and Black-Litterman has enough surface
of its own (equilibrium returns, the view matrix, the uncertainty scalar) to deserve its own verification
pass.

**Blocked by:** 05 — Agent 2 core allocation.

**Status:** ready-for-agent

- [ ] Builds the view matrix from Agent 7's `SignalBundle`, using `confidence` to set view uncertainty
      rather than treating all views as equally certain.
- [ ] Derives equilibrium returns from market-cap or an explicitly documented alternative, with the
      choice justified rather than defaulted.
- [ ] Verified directionally: posterior expected returns move toward the views that were stated, and
      a stronger/more confident view moves them further. Assert this rather than assuming it.
- [ ] Verified degenerately: with no views (or zero confidence everywhere), the posterior collapses back
      to the equilibrium prior. This is the cleanest correctness check available and should be a
      permanent assertion.
- [ ] Feeds into ticket 05's optimizer without either component needing to know about the other's
      internals.

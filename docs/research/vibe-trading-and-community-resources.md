# Vibe-Trading, awesome-systematic-trading, OpenBB — checked 2026-08-19

Investigated directly (WebFetch + GitHub API + raw file reads), not via the `research` skill subagent
(both background research slots were failing on session limit at the time). Same standard applied:
verify claims against the actual repo, not its README's marketing copy.

## OpenBB — already answered, not re-checked

Already investigated in `docs/research/data-and-modelling-tooling.md` (2026-08-19). **Rejected** as a
point-in-time/survivorship-bias data fix: no delisted-security data found anywhere in 2,710 files
searched, sells no data of its own (bring-your-own-keys), and is **AGPL-3.0** — a real license conflict
with this project's Apache-2.0/MIT posture. The useful byproduct of that investigation was finding
`reference/qlib`'s own free point-in-time constituents builder while checking it.

## HKUDS/Vibe-Trading

**Verified via GitHub API** (not trusting the WebFetch page-summary's specific numbers, which came from
the repo's own marketing copy): real repo, 31,276 stars, 5,073 forks, MIT license, created 2026-04-01,
last push 2026-08-19 (actively maintained), 2,610 files. The star count and activity are real; a
"Vibe-Trading" name from an AI-recommender-systems lab is exactly the kind of claim worth checking rather
than trusting, and it checked out as a genuine, substantial codebase — not a shell repo riding a name.

### What it actually has (verified by reading real files, not the README)

- **A registry-based, systematic look-ahead test** (`agent/tests/factors/test_lookahead.py`): builds one
  synthetic panel, corrupts every column after a probe row, and asserts every registered alpha's value at
  the probe row is unchanged — run once across the *entire* factor registry (~450 alphas), not once per
  factor. **This is a better-engineered version of what Agent 7 already does** — QAPF writes one
  look-ahead test per factor; this pattern makes it one test that automatically covers every factor ever
  registered, present or future.
- **A first-class `survivorship_bias` flag** threaded through their S&P 500 loader's result metadata,
  disclosed to both the CLI/HTML report and the SSE/frontend path (the test found was literally a
  regression test for a case where that disclosure was being silently dropped in one code path). Notably,
  this is a *disclosure* mechanism, not a *fix* — it tells the user survivorship bias is present, it
  doesn't correct for it. That maps directly onto ticket 10's "accept and document" option, which this
  independently validates as a real, precedented approach rather than a corner-cutting one.
- **IC/IR-based factor evaluation** (`ic_mean`, `ic_std`, `ir`, `ic_positive_ratio` in the alpha-bench
  output; default zoo is `alpha101`, i.e. WorldQuant's well-known 101 Formulaic Alphas). Information
  Coefficient (rank correlation of factor value vs. forward return) is a standard, respected
  cross-sectional factor-quality metric. **Agent 7 currently computes none of this** — it rank-normalizes
  factors and combines them, but never measures whether each individual factor's rank actually predicts
  forward returns before including it.

### What it does NOT have (checked specifically, all zero hits)

Searched the full file tree for: `deflated`, `sharpe` (as a module), `purge`, `overfit`, `significance`,
`p_value`, `monte_carlo`, `bootstrap`. **All zero.** Despite 2,610 files and a claimed 460+ factors, there
is no Deflated Sharpe Ratio, no purged cross-validation, no Monte Carlo significance testing, and nothing
resembling Agent 14's independent decay/regime-coverage/concentration challenge.

### The honest read

Vibe-Trading's rigor lives at the **individual-factor** level (does this one alpha leak the future, is
its IC good) — genuinely well-engineered there, better than what QAPF has for that specific concern.
QAPF's rigor lives at the **strategy/portfolio overfitting-correction** level (how many things were
tried, does the aggregate result survive multiple-testing correction, is it independently challenged).
These are complementary, not overlapping, and QAPF is stronger exactly where this much larger, far more
popular project is weaker — which is worth knowing, not something to be intimidated by.

**Two concrete, low-risk adoptions worth doing, neither urgent relative to ticket 07:**
1. Refactor Agent 7's per-factor look-ahead tests into the registry pattern once a 5th factor is ever
   added — right now, at 4 hand-written factors, the current per-factor tests are not yet painful enough
   to justify the refactor.
2. Add IC/IR as a diagnostic Agent 4 or Agent 7 reports per factor, alongside (not instead of) the DSR —
   this would have given an earlier, cheaper signal that the four original factors were weak, before
   spending a full backtest cycle finding out.

Everything else in the repo (13 broker connectors, 9 backtest market engines, 16 messaging channels,
options analytics) is real but out of scope for a pre-real-capital, single-$1,000-account, single-asset
project — noted, not adopted.

## paperswithbacktest/awesome-systematic-trading

Verified via GitHub API: real, 13,510 stars, 1,637 forks, unlicensed (a curated list, not code — no
license needed), created 2022, **last pushed 2025-01-22** — roughly 7 months stale relative to this
project's current date. A legitimate, long-running curated index (97+ libraries, 40+ strategy write-ups,
55+ books, categorized by asset class), not itself a source of new findings. Best used as a **pointer**
when a specific need arises (e.g. "what backtesting libraries exist besides Qlib") rather than read
cover-to-cover — its own emphasis is implementation tooling over statistical validation rigor, so it
would not have surfaced anything ticket 02's validation bar needs.

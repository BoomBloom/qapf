# 08 — Does the strategy survive realistic execution costs at the intended account size?

**Type:** `wayfinder:task`
**Blocked by:** 03 (data-past-2020)
**Status:** open · unclaimed

## Question

Does the strategy survive realistic execution costs at the intended account size?

Statistical significance and net profitability are different questions, and a strategy can pass the first
while failing the second.

Agent 11 estimates 2.24bp for the current portfolio at $1M notional — but the backtest's returns do not
include Agent 11's costs at all; Qlib's own commission model is separate and simpler. At $1,000, fixed
per-trade costs and whole-share rounding dominate in a way they never do at $1M: the current allocation
includes a 0.04% WMT position that would be a fractional share.

Determine whether the strategy is profitable net of realistic costs at the size actually intended, and
whether the $1,000 stage is even mechanically executable.

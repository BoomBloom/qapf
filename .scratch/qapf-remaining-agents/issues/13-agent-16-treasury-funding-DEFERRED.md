# 13 — Agent 16: Treasury & Funding (DEFERRED)

**What to build:** Management of the firm's own cash and financing — margin, collateral, funding costs,
and currency hedging of firm capital. Distinct from Agent 2, which allocates strategy capital across
positions but does not manage the cash and broker relationships underneath it.

**Deliberately deferred — this ticket exists to keep the roster auditable, not to be worked.** Reasons,
recorded so the decision doesn't get silently re-litigated:

- The function is real in an institutional prop firm with multiple prime-broker relationships, financing
  lines, and multi-currency exposure. None of those exist for a single-operator, paper-trading system.
- Everything currently runs simulated with a single notional account and no financing. There is no margin
  to manage and no funding cost to optimize.

**Un-defer when** the system moves to live capital, uses leverage or margin, or trades in more than one
currency — at which point this stops being theoretical and starts being a real source of cost and risk.

**Blocked by:** Not blocked — deferred by policy.

**Status:** deferred

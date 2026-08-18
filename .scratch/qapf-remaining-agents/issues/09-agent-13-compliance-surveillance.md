# 09 — Agent 13: Compliance & Regulatory Surveillance

**What to build:** Surveillance over the order flow, checking conduct rather than risk. The CRO (Agent 10,
built) asks "is our capital-at-risk within limits?" This asks a structurally different question: "did our
trading behave in a way that would be a problem if someone audited it?" — wash-trading-shaped patterns,
position-limit breaches, restricted-list violations, and a defensible audit trail of what was traded and
why.

Worth building even in a single-operator paper-trading system, for two reasons: the patterns it looks for
(a strategy repeatedly buying and selling the same name intraday, position concentration creeping past a
stated cap) are also *bug signatures*, not just conduct violations — a signal oscillating every rebalance
looks exactly like wash trading. And the audit trail is far cheaper to build alongside the execution
layer than to retrofit later.

Kept structurally separate from the CRO's risk log deliberately, so "was a rule broken?" and "was risk too
high?" stay independently answerable.

**Blocked by:** 07 — Agent 11 (Execution). There is no order flow to surveil until orders exist.

**Status:** ready-for-agent

- [ ] Screens simulated order flow for wash-trading-shaped patterns (offsetting buys/sells in the same
      name over a short window).
- [ ] Enforces position-limit and concentration checks against explicitly stated limits.
- [ ] Supports a restricted list — names that must not be traded regardless of signal.
- [ ] Produces an audit trail that is separate from, and does not depend on, the CRO's risk log.
- [ ] Verified against real data: run it over Agent 9's real backtest order flow and report what it finds.
      A clean result is only meaningful if the detector is also shown to fire on a deliberately
      constructed violating case — test both.

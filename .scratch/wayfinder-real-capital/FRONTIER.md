# Frontier — what is takeable right now

Updated 2026-08-19 after resolving ticket 07 (attempt 1 — FAILED the bar, 4 attempts remain).

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | YES (evidence appended, not yet decided) |
| 02 | What must the strategy prove? | grilling | — | CLOSED |
| 03 | Equity data past 2020 (final holdout) | research | — | YES (off critical path) |
| 04 | Which prop firms permit automation? | research | — | CLOSED |
| 05 | Literature on regime factor weighting | research | — | CLOSED |
| 06 | Keep / invert / flatten the weights | grilling | — | CLOSED |
| 07 | Does the strategy clear the bar? | task | — | **CLOSED — FAILED, attempt 1/5** |
| 08 | Does it survive costs at $1,000? | task | — | YES (07's attempt-1 already previews this via condition 3, which passed) |
| 09 | Which broker and platform? | grilling (HITL) | — | YES (04 closed; nautilus_trader + IBKR now real evidence) |
| 10 | Universe survivorship bias | grilling (HITL) | — | YES (evidence appended: Qlib's free PIT builder) |
| 11 | Intraday equity vs daily closes | grilling (HITL) | — | YES |
| 12 | Wire kill-switch enforcement | task | — | YES |

**The critical path has moved.** Ticket 07's attempt 1 is a clean, informative failure: the signal is
statistically real (DSR 0.9636) and profitable, but doesn't beat naive buy-and-hold risk-adjusted — the
factor set is the binding constraint, not costs (fixed) or regime-weighting (already flattened, ticket
06). **Recommended next: turn `docs/research/viable-alpha-families.md`'s shortlist into a concrete
attempt-2 plan for ticket 07**, in a fresh session per wayfinder's one-ticket-per-session rule.

Tickets 01, 09, 10 and 11 are HITL and need the operator. Tickets 03, 08 and 12 are AFK.

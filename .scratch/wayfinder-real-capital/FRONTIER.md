# Frontier — what is takeable right now

Updated 2026-08-19 after resolving ticket 07 (attempt 1 — FAILED the bar, 4 attempts remain).

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | **CLOSED — 0.20/0.06, set live** |
| 02 | What must the strategy prove? | grilling | — | CLOSED |
| 03 | Equity data past 2020 (final holdout) | research | — | YES (off critical path) |
| 04 | Which prop firms permit automation? | research | — | CLOSED |
| 05 | Literature on regime factor weighting | research | — | CLOSED |
| 06 | Keep / invert / flatten the weights | grilling | — | CLOSED |
| 07 | Does the strategy clear the bar? | task | — | **CLOSED — FAILED, attempt 1/5** |
| 08 | Does it survive costs at $1,000? | task | — | YES (07's attempt-1 already previews this via condition 3, which passed) |
| 09 | Which broker and platform? | grilling (HITL) | — | YES (04 closed; nautilus_trader + IBKR now real evidence) |
| 10 | Universe survivorship bias | grilling (HITL) | — | **CLOSED — fix it properly, before 07 attempt 2** |
| 11 | Intraday equity vs daily closes | grilling (HITL) | — | YES |
| 12 | Wire kill-switch enforcement | task | — | YES |
| 13 | Build the point-in-time universe | task | — | YES — prerequisite for 07's attempt 2 |

**The critical path has moved again.** Ticket 07's attempt 2 is now blocked on ticket 13 (build the real
point-in-time universe) landing first — ticket 10 decided the current hand-picked universe inflates every
result and must be fixed, not just disclosed, before spending another attempt. **Recommended next: ticket
13**, then fold in ticket 01's fewer/cheaper-names constraint and `docs/research/viable-alpha-families.md`'s
shortlist into one concrete attempt-2 plan.

Tickets 09 and 11 are HITL and need the operator. Tickets 03, 08, 12 and 13 are AFK.

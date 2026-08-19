# Frontier — what is takeable right now

Updated 2026-08-19 after resolving tickets 02, 04, 05, 06.

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | **YES** |
| 02 | What must the strategy prove? | grilling | — | CLOSED |
| 03 | Equity data past 2020 (final holdout) | research | — | YES (off critical path) |
| 04 | Which prop firms permit automation? | research | — | CLOSED |
| 05 | Literature on regime factor weighting | research | — | CLOSED |
| 06 | Keep / invert / flatten the weights | grilling | — | CLOSED |
| 07 | **Does the strategy clear the bar?** | task | — | **YES — the destination ticket** |
| 08 | Does it survive costs at $1,000? | task | — | YES (03 no longer blocks it) |
| 09 | Which broker and platform? | grilling (HITL) | — | YES (04 closed) |
| 10 | Universe survivorship bias | grilling (HITL) | — | YES |
| 11 | Intraday equity vs daily closes | grilling (HITL) | — | YES |

**The critical path is clear.** Ticket 07 has no remaining blockers and is where the destination is
reached or not. Everything else is either a caveat on how much 07's answer can be trusted (10, 11), a
downstream consequence (08, 09), or the final holdout (03).

**Recommended next: 07**, in a FRESH session — it is the most consequential code in the project and
wayfinder's one-ticket-per-session rule exists precisely to stop it being written at the end of a long
context.

Tickets 01, 09, 10 and 11 are HITL and need the operator. Tickets 03, 07 and 08 are AFK.

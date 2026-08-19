# Frontier — what is takeable right now

Derived from the blocking edges in `tickets/`. A ticket is takeable when every ticket blocking it is
closed. Regenerate by reading the "Blocked by" line of each ticket.

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | **YES** |
| 02 | What must the strategy prove before real money? | grilling (HITL) | — | **YES** |
| 03 | How do we get equity data past 2020-11-10? | research (AFK) | — | **YES** |
| 04 | Which prop firms permit automated trading? | research (AFK) | — | in progress |
| 05 | Does literature support regime factor weighting? | research (AFK) | — | in progress |
| 06 | Keep, invert, or flatten the regime weights? | grilling (HITL) | 05 | no |
| 07 | Does the strategy clear the bar? | task | 02, 03, 06 | no |
| 08 | Does it survive costs at $1,000? | task | 03 | no |
| 09 | Which broker and platform? | grilling (HITL) | 04 | no |

**Takeable now: 01, 02, 03.** Tickets 04 and 05 are running as research subagents.

Tickets 01 and 02 are HITL — they need the operator, and an agent must not answer them on their behalf.
Ticket 03 is AFK and can be dispatched without waiting.

**The critical path runs 02 -> 07.** Ticket 07 is where the destination is actually reached or not, and
it cannot start until the bar is defined (02), longer data exists (03), and the regime weights are
settled (06). Nothing else on this map shortens that path — which is why finishing Agents 1 and 8 was
ruled out of scope.

## One-ticket-per-session rule

Wayfinder allows resolving only ONE ticket per session (research tickets excepted). Charting is itself
one session's work and resolves nothing — that is why every ticket above is still open.

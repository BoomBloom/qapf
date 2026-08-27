# Venture Charter — the next project

**Status:** thesis undecided. This file is the single source of truth for what has been
DECIDED vs. what is still OPEN. Update it when a decision is made; never restate open
questions as if they were settled.

Last updated: 2026-08-27

---

## Decided

| # | Decision | Made on | Rationale |
|---|----------|---------|-----------|
| D1 | Primary goal is **a real, verifiable edge** — a strategy that survives adversarial out-of-sample testing and could trade real money. | 2026-08-27 | User's stated objective. Portfolio-piece and research value are welcome side effects, not the target. |
| D2 | Long-term intent is **income from trading**. See "The capital constraint" below — this reframes the near-term goal without abandoning the long-term one. | 2026-08-27 | User's stated objective. |
| D3 | **Deep research precedes any code.** No architecture, no repo layout, no agents until a falsifiable edge hypothesis exists with evidence behind it. | 2026-08-27 | User's explicit instruction, and the failure mode QAPF already demonstrates (16 working agents, no proven edge). |
| D4 | Session context is maintained in **markdown in-repo**, not in conversation history. | 2026-08-27 | Cost discipline — see `.claude/skills/venture-prime/SKILL.md`. |

## Open — blocking

| # | Question | Why it blocks | Status |
|---|----------|---------------|--------|
| O1 | What does "quantum" mean here: quantum-inspired classical, literal QPU, plain quant, or hybrid? | Determines the entire technical identity and which research questions are even worth asking. | Awaiting user, briefed 2026-08-27 (see `10-research-log.md` §1) |
| O2 | New repo, evolve QAPF, or harvest QAPF's proven parts? | Determines what we inherit and what we rebuild. | Deferred — answerable only once O1 and the edge thesis are settled. Do not guess. |
| O3 | Which market and horizon? | Data cost, feedback-loop speed, and where an edge is even plausible. | Deferred to the research phase, by user's choice. |

## Open — non-blocking

- O4: Project name. Placeholder is "venture"; rename the skill and docs when a name exists.
- O5: Whether QAPF's `reference/` forks should be pushed to GitHub as real backups (currently they are untouched mirrors — see the fork audit).

---

## Hard constraints (facts, not preferences)

### The capital constraint

QAPF's own Agent 16 established the live account is **$1,000** and found cash yield at that
size is genuinely $0. That number sets the near-term ceiling and must not be wished away:

| Capital | 25%/yr (excellent, sustained) | 50%/yr (exceptional, rarely sustained) |
|---------|------------------------------|----------------------------------------|
| $1,000 | $250/yr | $500/yr |
| $25,000 | $6,250/yr | $12,500/yr |
| $150,000 | $37,500/yr | $75,000/yr |

Living-wage income from trading requires roughly $150k–$250k of capital at defensible return
rates. The gap between $1,000 and that is **capital, not strategy** — no algorithm closes it.

**Consequence for this project:** the near-term deliverable is a *verified edge with an
auditable track record*, because that is the prerequisite for every route to income:
1. Compounding own capital (slow; requires outside income meanwhile)
2. Managing others' capital (requires track record + regulatory registration)
3. Selling the skill or the technology (quant role, or a product)

Optimizing for "income this year" from $1,000 produces overleveraged, blown-up accounts.
Optimizing for "provable edge" keeps all three routes open. This is a reframing of D2, not
a rejection of it.

### Regulatory / structural

- US pattern-day-trader rule: sub-$25k accounts are capped at 3 day trades per 5 business
  days in a margin account. Constrains intraday equity strategies at current size.
- QAPF's Agent 2 is long-only because Qlib's optimizer hard-codes no-shorting and
  margin/borrow are unmodeled. Any short-side thesis needs new machinery.

---

## Anti-goals

- Building agents, dashboards, or orchestration before an edge is proven. QAPF already
  demonstrates that a complete, working system and a profitable one are different things.
- Adopting "quantum" as branding without a benchmark that proves it beats the classical
  baseline on the same problem.
- Any backtest result accepted without a Deflated Sharpe Ratio and an out-of-sample split
  chosen *before* the strategy was fitted.

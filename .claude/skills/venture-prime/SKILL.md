---
name: venture-prime
description: Orients Claude on the NEW trading venture (thesis not yet chosen) at the start of any session that touches project direction, edge research, thesis selection, or the decision to build on QAPF vs. start fresh. Loads the charter (what's decided vs. open), the append-only research log (so no question gets researched twice), and the session protocol that keeps token spend low. Run this FIRST in any session about the new project — before planning, before research, before code. Trigger on mentions of the venture, the new project, the edge thesis, the quantum decision, or "what were we doing".
---

# Venture Prime

Cheap re-orientation for the new trading venture. The whole point is that resuming work costs
a few hundred tokens of file reads instead of re-deriving context from a long conversation.

## Step 1 — Load state (always, in this order)

1. `docs/venture/00-charter.md` — what is DECIDED, what is OPEN, and the hard constraints.
2. `docs/venture/10-research-log.md` — every research question already answered, with sources
   and a confidence rating.
3. `docs/venture/20-decision-log.md` — if it exists; the ADR trail for reversals.

Read the files. Do not rely on a summary of them from earlier in a conversation — they are
updated as decisions land, and a stale summary is how a settled question gets re-litigated.

## Step 2 — Respect the decided/open boundary

- Anything in the charter's **Decided** table is settled. Do not re-open it, do not re-argue
  it, do not ask the user about it again.
- Anything in **Open — blocking** must NOT be guessed. If the task depends on a blocking
  open question, say so and ask; do not pick a plausible answer and build on it.
- Anything in **Open — non-blocking** can be assumed with a stated assumption.

## Step 3 — Check the research log before researching

Search `10-research-log.md` for the question first. If there is an entry:
- **verified** → use it.
- **reported** → usable, but say it's second-hand if the decision is expensive.
- **unverified** → check it before it carries any weight.

Re-running research that is already logged is the single most expensive avoidable mistake in
this project. If an entry is thin, *extend* it rather than starting over.

## Step 4 — Know the anti-goals

From the charter, the three failure modes this project is explicitly avoiding:
- Building infrastructure before an edge is proven (QAPF's lesson: 16 working agents ≠ edge).
- "Quantum" as branding with no benchmark against the classical baseline.
- Any backtest without a Deflated Sharpe Ratio and a pre-committed out-of-sample split.

## Step 5 — Close the loop before the session ends

Whatever the session produced, write it down before finishing:
- New finding → append to `10-research-log.md` with date, source, confidence.
- Decision made → move the row from **Open** to **Decided** in `00-charter.md`, with the date
  and the reason.
- Direction reversed → add an entry to `20-decision-log.md` saying what changed and why.

A session whose findings live only in the transcript has to be paid for twice.

## Related

- `qapf-prime` — use that one instead for work inside the existing QAPF codebase.
- The fork audit of the 32 trading repos is prior art worth mining, not inventory to maintain.

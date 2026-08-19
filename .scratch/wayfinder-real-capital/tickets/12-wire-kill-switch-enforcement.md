# 12 — Wire the CRO's kill switch to actually block trading

**Type:** `wayfinder:task`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

## Question

Found while resolving ticket 01's research: `backend/risk/monitor.py` computes `kill_switch_triggered`
correctly, but grep confirms **nothing in the codebase consumes it to prevent an order being placed.**
The CRO reports; it does not enforce.

This is not a decision — it's a gap. A real-capital deployment cannot responsibly depend on a risk check
that has no execution-blocking effect. Deliberately NOT deferred to Agent 1 (Lead Orchestrator), which
is explicitly out of scope for this map: the destination requires an enforced kill switch regardless of
whether the full LangGraph orchestrator ever gets built, so a minimal hook — e.g. Agent 11's
`ExecutionPlanner` or whatever assembles the final order list checks Agent 10's verdict first and
refuses to emit orders when triggered — should exist independent of Agent 1.

**Ticket 01 closed 2026-08-19** — `max_drawdown_pct=0.20`, `max_daily_loss_pct=0.06` are now real values
in `backend/risk/__main__.py`, not placeholders. This ticket is fully unblocked.

**Resume policy, decided alongside ticket 01's threshold grill:** a kill-switch halt requires
**re-validation against the ticket 02 bar on fresh data**, not just a human flipping a switch back on. The
enforcement built here should reflect that — the choke point should refuse to emit orders and record
*why* in a way that makes "has this been re-validated since the last breach" a checkable fact, not just
log a generic halt message. Exact mechanism (a flag file, a status field Agent 10 exposes, something else)
is implementation detail for whoever takes this ticket, not decided here.

## What to build

- [ ] Identify the single narrowest choke point all order flow passes through (likely Agent 11's
      `ExecutionPlanner.plan()`, since every real trade goes through it).
- [ ] That choke point calls Agent 10, and refuses to emit any order when `kill_switch_triggered` is
      true — fails closed, not open.
- [ ] Verified with a real test: construct a return series known to breach the limit (Agent 9's real
      2020-02-27 COVID-crash date is the obvious real-data anchor), confirm zero orders are emitted for
      that date, and confirm normal dates still produce orders.
- [ ] The block is auditable — logged with the reason, not a silent no-op.

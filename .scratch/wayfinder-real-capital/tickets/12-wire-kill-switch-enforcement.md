# 12 — Wire the CRO's kill switch to actually block trading

**Type:** `wayfinder:task`
**Blocked by:** None — can start immediately.
**Status:** CLOSED — enforced, with one noted residual gap, 2026-08-19

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

- [x] Identify the single narrowest choke point all order flow passes through (likely Agent 11's
      `ExecutionPlanner.plan()`, since every real trade goes through it).
- [x] That choke point calls Agent 10, and refuses to emit any order when `kill_switch_triggered` is
      true — fails closed, not open.
- [x] Verified with a real test: construct a return series known to breach the limit (Agent 9's real
      2020-02-27 COVID-crash date is the obvious real-data anchor), confirm zero orders are emitted for
      that date, and confirm normal dates still produce orders.
- [x] The block is auditable — logged with the reason, not a silent no-op.

## Resolution (2026-08-19)

Built as part of Agent 1 (Lead Orchestrator), when the operator asked to build the two remaining
buildable agents. **This is a deliberate deviation from this ticket's original plan**, worth stating
plainly rather than glossing over: the ticket text above explicitly said the hook should be built
"independent of Agent 1" so enforcement didn't depend on the orchestrator ever getting built. Agent 1
got built first, and its `state_graph.py` turned out to be a better choke point than
`ExecutionPlanner.plan()` — gating at the graph level keeps `ExecutionPlanner` itself simple and
independently testable (Agent 9's backtests must keep executing through drawdowns to measure them; a
check baked into the planner itself would fight that), while a real orchestrated run still fails closed.

**Mechanism:** `backend/core/state_graph.py`'s `risk_gate` node calls `RiskMonitor` with the ticket 01
limits (0.20/0.06), and a conditional edge (`route_after_risk_gate`) sends a halted state straight to
`cio_synthesis`, skipping `execution` and `compliance` entirely — zero orders are ever constructed for a
halted run, not just zero orders sent. The halt reason states the ticket-01 resume policy explicitly
(re-validation required, not operator override) so it's auditable, not a generic message.

**Verified live** (`backend/core/__main__.py`'s `test_kill_switch_enforcement`): reused Agent 9's real
2018-2020 backtest returns (spans the COVID crash), found the actual first breach date via
`RiskMonitor.assess_history` (2020-03-09, not assumed), confirmed a run truncated through that date halts
with zero orders, and a run truncated to strictly-before that date does not halt and produces real orders.

**Residual gap, honestly noted, not hidden:** enforcement lives in the orchestrator's graph, not inside
`ExecutionPlanner.plan()` itself. Any future code path that calls `ExecutionPlanner` directly — bypassing
`backend/core/state_graph.py` — would NOT be blocked by the kill switch. Acceptable for now because the
orchestrator is meant to be the sole live entry point, but worth remembering if a second call site to
`ExecutionPlanner` is ever added (e.g. a future API route) without going through the graph.

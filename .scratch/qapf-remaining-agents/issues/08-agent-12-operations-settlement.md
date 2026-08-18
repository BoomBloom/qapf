# 08 — Agent 12: Operations & Settlement

**What to build:** The back-office reconciliation: given what Agent 2 intended to hold and what Agent 11
actually filled, report the difference — and attribute PnL to where it actually came from. This is the
agent that answers "we thought we were running this portfolio; what were we actually running, and what
did the gap cost?" Silent drift between intended and executed allocation is exactly the kind of error
that never announces itself, which is the failure mode this project keeps running into.

Qlib's `qlib/workflow/recorder.py` (MLflow-backed) provides experiment tracking and artifact logging as a
starting point, so run history and PnL attribution don't need a storage layer built from scratch.

**Blocked by:** 05 (Agent 2 — intended positions) and 07 (Agent 11 — actual fills). Reconciliation needs
both sides; with only one it has nothing to compare against.

**Status:** ready-for-agent

- [ ] Reconciles filled positions against target positions and reports the drift explicitly, per name and
      in aggregate.
- [ ] Attributes PnL across its real sources — signal/alpha, execution cost, and drift — rather than
      reporting one blended number.
- [ ] Produces a durable run record (date, targets, fills, costs, resulting PnL) that can be audited
      after the fact.
- [ ] Verified against real data: attributed components reconcile back to total PnL within a stated
      tolerance. This is a genuine arithmetic check and should fail loudly if the attribution is
      incomplete.
- [ ] Distinguishes drift caused by execution constraints (a limit, insufficient liquidity) from drift
      caused by a bug — they need different responses.

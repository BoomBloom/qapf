# 12 — Agent 5: Quantum & Advanced Optimization (DEFERRED)

**What to build:** QUBO / QAOA formulations of portfolio selection via Qiskit or Pennylane simulators, for
combinatorial problems where conventional optimization stalls.

**Deliberately deferred — this ticket exists to keep the roster auditable, not to be worked.** Reasons,
recorded so the decision doesn't get silently re-litigated:

- Agent 2 (tickets 05/06) covers portfolio optimization with methods that are proven, fast, and already
  present in Qlib. There is no measured problem that those methods fail to solve, so there is currently
  nothing for a quantum-inspired approach to improve on.
- The realistic universe here is ~15 tickers. Quantum-inspired combinatorial optimization is motivated by
  search spaces vastly larger than that; at this scale it is a solution without a problem.
- `README.md`'s Scope Warning already flags this as the lowest-priority item in the roster.

**Un-defer only when** there is a *measured* optimization problem that Agent 2's classical methods
demonstrably fail on — not because the technique is interesting.

**Blocked by:** Not blocked — deferred by policy.

**Status:** deferred

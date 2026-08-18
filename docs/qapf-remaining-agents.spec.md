# Spec: QAPF Remaining Agents (1, 2, 5, 8, 10–16)

Synthesized from the project's existing thread — `README.md`, `CLAUDE.md`, and the conversation that
built and verified Agents 3, 4, 6, 7, and 9 — not a fresh interview. Status and prior art below reflect
the actual state of the repo as of this spec's writing, not aspiration.

## Problem Statement

QAPF's 16-agent roster is documented (`README.md`'s Agent Roster → Build Strategy table), and five agents
are built and verified against live data (research, stats, macro, alpha, backtest). The remaining eleven
have been built one at a time by picking whichever seemed natural in conversation ("Agent 4", "Agent 6",
...). That's worked so far because the agents built happened to be mostly independent. It stops working
once dependency order matters — and it already does: Agent 1 (Orchestrator) is specified to route around
Agent 10 (CRO)'s kill-switch authority, which means building the Orchestrator before the CRO exists means
either inventing a stand-in for that boundary or leaving it as a TODO that's easy to forget. There is
currently no artifact that makes these dependencies visible before someone starts coding into them.

## Solution

Formalize the remaining eleven agents as scoped units of work with explicit blocking edges, so the build
order is a decision made once, here, rather than re-derived (or missed) each time a "what's next" question
comes up. Each unit keeps the pattern already proven five times over: one module, live-verified against
real data (not mocks), with the result reported honestly even when it's unflattering (Agent 9's backtest
underperforming its own benchmark, reported as-is, is the reference case for what "verified" means here).

## Dependency Graph (the actual point of this spec)

Derived from what each agent structurally needs to exist first, not from priority alone:

- **Ready now, no blockers:** Agent 2 (Portfolio Manager — consumes Agent 7's signals, already built),
  Agent 8 (Software Engineering — consumes Agent 3's research output, already built), Agent 10 (CRO — can
  compute real VaR/drawdown against Agent 9's already-existing backtest position history), Agent 14 (Model
  Risk — exists specifically to independently critique Agent 9's already-existing result), Agent 15 (Data
  Infrastructure — monitors feeds already wired into Agents 3/4/6/7/9).
- **Blocked on Agent 2:** Agent 11 (Execution needs real position sizes, not Agent 9's simplified top-k
  selection, to have anything meaningful to execute).
- **Blocked on Agents 2 and 11:** Agent 12 (Operations reconciles fills against target positions — needs
  both to exist), Agent 13 (Compliance surveils real order activity — nothing to surveil without Agent 11).
- **Blocked on most of the above existing:** Agent 1 (Orchestrator wires other agents into a graph and
  routes around Agent 10's kill-switch — needs Agent 10 at minimum, and is more useful the more of the
  roster it has to actually orchestrate).
- **Deferred by policy, not blocked:** Agent 5 (Quantum/Optimization — lowest priority per README's Scope
  Warning), Agent 16 (Treasury — structurally wants multiple prime-broker relationships that don't exist
  for a single-operator system).

Suggested order following the graph: **10 → 14 → 15 → 2 → 11 → 8 → (12, 13) → 1**, with 5 and 16 deferred
indefinitely. This is a recommendation the graph supports, not the only valid ordering — 8, 14, and 15
have no dependency relationship to each other or to 10, so any interleaving of that group is equally
valid.

## User Stories

1. As the operator of QAPF, I want the Portfolio Manager (Agent 2) to turn Agent 7's per-ticker signals
   into real position sizes, so that a backtest reflects deliberate portfolio construction instead of
   Agent 9's simplified top-k/drop-bottom selection.
2. As the operator, I want Black-Litterman view construction from Agent 7's signal + confidence, so that
   qualitative alpha views become a formal expected-return vector Qlib's existing optimizer can consume.
3. As the operator, I want to choose between Qlib's existing gmv/mvo/rp/inv methods per regime, so that
   allocation logic isn't hard-coded to one risk posture across every market condition.
4. As the operator, I want the CRO (Agent 10) to compute real-time VaR, CVaR, and drawdown against actual
   position history, so that risk limits are enforced against real numbers, not aspirational ones.
5. As the operator, I want the CRO's kill-switch authority to be architecturally un-bypassable, so that no
   future orchestrator change can silently route around a risk breach.
6. As the operator, I want the CRO's import boundary (`backend/risk/` never importing `backend/core/` or
   LangGraph) enforced by a repeatable check, not just a documented convention, so that drift is caught
   automatically rather than discovered in an incident.
7. As the operator, I want Model Risk (Agent 14) to independently challenge Agent 9's backtest result, so
   that "the backtest looks fine" and "the model is actually trustworthy" stay two different questions
   answered by two different code paths.
8. As the operator, I want Model Risk to test for regime-shift blindness and out-of-distribution inputs
   specifically, so that a strategy validated in one historical regime isn't silently assumed to hold in
   an unseen one.
9. As the operator, I want Data Infrastructure (Agent 15) to watch every upstream feed (FRED, yfinance,
   arXiv, GitHub, Qlib's data store) for staleness and schema drift, so that the next silent data bug is
   caught automatically instead of requiring another live-test discovery like the last four.
10. As the operator, I want Data Infrastructure's checks expressed as the same kind of regression check
    already used in Agent 6's `__main__.py` (the CPI-gap check), so that this agent extends an established
    pattern rather than inventing a new one.
11. As the operator, I want Execution (Agent 11) to simulate order placement against Qlib's
    exchange/executor primitives using Agent 2's real position sizes, so that slippage and market impact
    are estimated against a realistic trade list, not a hypothetical one.
12. As the operator, I want Operations (Agent 12) to reconcile Agent 11's simulated fills against Agent 2's
    target positions, so that discrepancies between intended and executed allocation are visible rather
    than assumed away.
13. As the operator, I want Compliance (Agent 13) to screen Agent 11's simulated order activity for
    wash-trading/spoofing-shaped patterns, so that conduct risk is checked even in a single-operator
    system where it might otherwise seem unnecessary.
14. As the operator, I want Compliance's audit trail to be structurally separate from the CRO's risk log,
    so that "was a rule broken" and "was risk too high" remain independently answerable.
15. As the operator, I want Software Engineering (Agent 8) to convert Agent 3's structured research output
    into runnable Python, so that a promising paper doesn't stop being useful the moment its math needs
    implementing.
16. As the operator, I want Agent 8's generated code to run through the same live-verification pattern as
    every other agent, so that generated code is trusted only after it's actually been proven against real
    data, the same bar every hand-written agent has already cleared.
17. As the operator, I want the Orchestrator (Agent 1) to fork `TradingAgentsGraph`'s LangGraph wiring
    rather than invent a second orchestration mechanism, so the project has one graph, not two competing
    ones.
18. As the operator, I want the Orchestrator to treat the CRO as outside its own decision loop (reading its
    state, never overriding its kill-switch), so that the isolation rule holds in the orchestration layer,
    not just in `backend/risk/`'s import graph.
19. As the operator, I want each remaining agent's build order to follow the dependency graph above rather
    than conversational convenience, so that no agent gets built against a stub that later needs rework
    once its real dependency exists.
20. As the operator, I want Agent 5 (Quantum/Optimization) and Agent 16 (Treasury) to stay explicitly
    named and deferred rather than silently dropped, so the roster's completeness is auditable even for
    the parts not being built yet.

## Implementation Decisions

- **Primary seam, reused from precedent:** `backend/agents/<name>/` — one folder per agent, a schemas
  module (Pydantic v2), a core-logic module, and a `__main__.py` live-verification runner. This is the
  proven pattern for Agents 3, 4, 6, 7, 9 and is the default for Agents 2, 5, 8, 12, 13, 14, 15, 16.
- **Two necessary deviations from that default, both already anticipated in `CLAUDE.md`:**
  - Agent 1 (Orchestrator) is not a standalone leaf agent — its natural seam is
    `backend/core/state_graph.py`, extending `reference/TradingAgents/tradingagents/graph/setup.py`'s
    `GraphSetup` node/edge pattern, not a `backend/agents/orchestrator/` folder in the same sense as the
    others.
  - Agent 10 (CRO) uses the standard agent-folder seam *plus* one additional, non-negotiable seam: the
    import boundary. `backend/risk/` must never import `backend/core/` or any LangGraph module. This needs
    an automated check (e.g. a test that greps for forbidden imports), not just documentation, per
    `CLAUDE.md`'s existing ground rule.
- **Open question, not yet resolved — flagging rather than silently picking one:** `CLAUDE.md`'s "Where
  new code goes" section says a new Qlib-backed capability should go in `backend/services/`, wrapping the
  relevant `qlib` module rather than reimplementing it. In practice, Agent 9 (also Qlib-backed) was built
  directly inside `backend/agents/backtest/`, importing `qlib` itself, and `backend/services/` doesn't
  exist. Agents 2, 11, and 12 are all "Extend/Adapt Qlib" per the roster and will hit this same choice.
  Decide before starting Agent 2: keep following Agent 9's actual precedent (Qlib usage lives directly in
  the agent's own module), or start honoring the original `backend/services/` split now. Whichever is
  chosen should be applied consistently across 2, 11, and 12, not decided per-agent.
- **CRO kill-switch authority** must be enforced at the architecture level: Agent 1's orchestration graph
  reads CRO state but cannot override it. This is a repeat of an existing `CLAUDE.md` ground rule, restated
  here because Agent 1 is the first agent where violating it becomes possible.
- **Qlib gotchas apply to Agents 2, 11, 12** (all Qlib-touching): re-read
  `.claude/references/qlib-known-issues.md` before writing code. In particular, `PortfolioOptimizer`
  operates on caller-supplied covariance/return arrays, not Qlib's expression engine, so it should be
  unaffected by the `Ref()` bug — verify this assumption against the actual call, don't inherit it as
  settled. Any Qlib-importing script run directly still needs the `if __name__ == "__main__":` guard.

## Testing Decisions

- **What "tested" means in this project, established by precedent, not invented for this spec:** each
  agent's `__main__.py` runs against real external data (yfinance, FRED, arXiv, GitHub, Qlib's bundled
  dataset) and asserts specific, falsifiable correctness properties — not generic smoke tests. Prior art:
  - Agent 7's look-ahead bias test (corrupt future data, assert past signals unchanged) and
    factor-direction test (recompute the underlying quantity independently, assert the factor's sign
    agrees with it).
  - Agent 9's composition-level look-ahead test (the same idea, applied to the new glue code stitching
    Agents 6 and 7 together, not just the sub-agents individually).
  - Agent 6's point-in-time regression check and the CPI-gap YoY regression check.
  - Agent 4's Deflated-Sharpe sanity check (assert DSR decreases as the assumed trial count increases).
- **Modules to test this way going forward:** Agent 2's Black-Litterman view construction (assert
  posterior returns move in the direction the input views imply), Agent 10's VaR/CVaR calculations
  (assert against a known-distribution synthetic case where the answer is analytically known, since real
  drawdown events are the thing being predicted, not something to wait for), Agent 15's staleness/drift
  detection (assert it actually flags the historical bugs already found — the CPI gap, the stale Qlib
  calendar — as a regression suite of "should have caught this" cases).
- **No conventional test framework (pytest, etc.) exists yet** and this spec does not propose adding one —
  the live-verification-runner pattern has caught every real bug found so far. Revisit only if a future
  agent's correctness genuinely can't be checked against real data (e.g. a pure combinatorial algorithm
  with no external data source to verify against, which may be true of Agent 5 if it's ever un-deferred).

## Out of Scope

- The frontend/dashboard (Phase 1+ in `README.md`'s roadmap; nothing started).
- Postgres/Redis (Phase 1+; not stood up).
- Live broker/exchange connectivity — everything remains simulated/paper, matching Agent 9's and Agent
  11's Qlib-based simulation approach.
- Actually implementing Agent 5 (Quantum/Optimization) or Agent 16 (Treasury & Funding) — both stay
  deferred per README's existing Scope Warning; this spec only keeps them named in the dependency graph.
- Re-litigating any already-verified decision from Agents 3/4/6/7/9 (e.g., re-checking whether Qlib's
  expression engine is broken — it is, that's settled and documented).

## Further Notes

- No issue tracker is configured for this project (confirmed 2026-08-18 — local git only, no Jira/Linear/
  GitHub Issues wiring). This spec is written to `docs/` rather than published to a tracker; running
  `/setup-matt-pocock-skills` first would be required before a `/to-tickets` pass could create real tracked
  issues instead of local files.
- Three AI-generated blueprint docs (DeepSeek, Qwen, a Gemini master-prompt doc) were reviewed earlier in
  this project and found to restate the same 12-agent design with no new verification — noted in
  `README.md`. They contributed nothing to this spec beyond a directory-layout detail already merged
  (`backend/core` / `api` / `models` / `services` split) — treat any future AI-authored doc the same way:
  a hypothesis to verify, not an input to this spec.
- The roster grew from 12 to 16 agents (13–16 added) specifically because the original 12 mirrored a
  generic prop-firm blueprint rather than one built by checking what real prop-firm org charts cover —
  see `README.md`'s "Why Agent 15 exists" section for the concrete evidence (four real bugs this project
  already hit) behind that expansion.

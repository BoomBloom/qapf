# 11 — Agent 1: Lead Orchestrator (Synthetic CIO)

**What to build:** The thing that runs the firm: a graph that invokes the other agents in order, passes
state between them, and produces an end-to-end decision without a human calling each `python -m agents.X`
by hand. Today every agent is a working island, and the "workforce" is a person running six commands and
reading six outputs.

Fork `TradingAgentsGraph` / `GraphSetup` from `reference/TradingAgents` rather than inventing a second
orchestration mechanism — its LangGraph `StateGraph` wiring, typed `AgentState`, and SqliteSaver
checkpoint/resume are directly reusable, and `CLAUDE.md` explicitly forbids a competing mechanism
alongside it.

**The CRO boundary is the hard constraint.** Agent 10 is built and enforces its own isolation (verified by
an AST import scan). The orchestrator may *read* CRO state; it must never override, retry around, or
route past a kill-switch verdict. This is the first ticket where violating that is even possible, which
is exactly why it's called out here rather than assumed.

Sequenced last deliberately: an orchestrator is only as useful as the agents it has to orchestrate, and
wiring it before Agents 2/11/12/13 exist means building against stubs and reworking it afterward.

**Blocked by:** 01 (interface drift — the graph needs one call shape, not six) and 02 (LLM key + verified
TradingAgents graph). Should also wait on 05, 07, 08, 09 for the orchestrator to be worth building; it is
technically implementable before those, but would be orchestrating a mostly-empty roster.

**Status:** ready-for-agent (after 01 and 02)

- [ ] Forks `TradingAgentsGraph`/`GraphSetup` into `backend/core/state_graph.py`, following its existing
      node/edge pattern; no second orchestration mechanism introduced.
- [ ] Invokes the built agents through the uniform interface settled in ticket 01.
- [ ] Reads CRO state and halts on a kill-switch verdict; has no code path that overrides or retries past
      it. Verify this the way ticket 01's isolation was verified — a test, not a comment.
- [ ] Checkpoint/resume works: an interrupted run resumes rather than restarting from scratch.
- [ ] Produces one end-to-end decision from macro regime through to target positions, demonstrably, on
      real data.
- [ ] Per-run LLM cost is reported, building on ticket 02's measurement.

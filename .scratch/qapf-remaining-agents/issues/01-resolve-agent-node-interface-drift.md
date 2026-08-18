# 01 — Resolve the agent-node interface drift (prefactor)

**What to build:** One consistent answer to "how does an agent get called," so the Lead Orchestrator can
wire agents into a graph without discovering six different call shapes. Today `CLAUDE.md`'s "Where new
code goes" seam says every agent exposes `run(state) -> state` matching the LangGraph node signature —
and not one of the six built agents actually does. They expose `run(topics, ...)`, `assess(...)`,
`generate(...)`, `run(prices, volumes, ...)`, and a toolkit of bare methods. Either the rule is
aspirational and the doc should be corrected, or the rule stands and thin adapters are needed. Decide,
then make the code and the doc agree.

Prefactor, not a feature: this exists so ticket 11 (Orchestrator) is a small ticket built on a true
premise instead of a large one that starts by discovering the drift. Doing it now also means each
adapter can be verified against its own already-working agent, one at a time, rather than all six at
once inside the orchestrator's own ticket.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] A decision is recorded (in `CLAUDE.md`, and as a note in the spec) on whether `run(state) -> state`
      is the real contract or the doc was aspirational.
- [ ] `CLAUDE.md`'s seam description matches what the code actually does — no rule left standing that
      zero agents follow.
- [ ] If adapters are the chosen answer: every built agent (3, 4, 6, 7, 9, 10) is reachable through the
      uniform shape, and each one's existing `__main__.py` verification still passes unchanged.
- [ ] If doc-correction is the chosen answer: the reason the LangGraph signature doesn't apply is written
      down, so ticket 11 doesn't re-litigate it.

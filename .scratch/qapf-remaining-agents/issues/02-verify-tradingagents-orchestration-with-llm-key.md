# 02 — Verify TradingAgents orchestration end-to-end with a real LLM key

**What to build:** Proof that the LLM half of this project actually runs, and what it costs per decision.
Phase 0 verified the Qlib half thoroughly (data layer, backtest engine, optimizer — all confirmed
working, with a real expression-engine bug found). The TradingAgents half has only ever been *read*, never
run: nobody has executed its LangGraph pipeline end to end, so "the agents debate and reach a decision"
is still an unverified claim about someone else's code. Run it on one ticker, capture what a single
decision actually costs in tokens and wall-clock time, and record whether the graph completes at all.

This is human-gated, not code-gated: **no LLM API key is currently configured** (no `.env`, no
`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in the environment — verified). Somebody has to supply one before
this can run, which is why it blocks two tickets that otherwise look independent.

The cost number is the point, not a nice-to-have. `README.md` already flags per-decision LLM cost as an
open scope risk for a multi-agent debate graph; this ticket is what turns that from a worry into a
measured number, before Agents 1 and 8 are built on the assumption it's affordable.

**Blocked by:** None in code — but requires an LLM API key to be provided.

**Status:** ready-for-agent (blocked on a human providing credentials)

- [ ] An API key is configured in a way that is gitignored and never committed.
- [ ] `reference/TradingAgents` runs its graph end to end on at least one ticker without erroring.
- [ ] Measured and written down: tokens consumed and wall-clock time for one complete decision.
- [ ] A judgement is recorded on whether that per-decision cost is acceptable at the intended run
      frequency — including "no" if the honest answer is no.
- [ ] Any surprises about how the graph actually behaves (vs. how its source reads) are noted, the same
      way Qlib's real behaviour was recorded in `.claude/references/qlib-known-issues.md`.

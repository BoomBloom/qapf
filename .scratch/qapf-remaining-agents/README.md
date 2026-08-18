# QAPF — remaining agents, as tickets

Generated from `docs/qapf-remaining-agents.spec.md` via the `to-tickets` flow. One file per ticket in
`issues/`, numbered in dependency order (blockers first).

No issue tracker is configured for this project (local git only), so these are local files rather than
tracked issues. If a real tracker is wired up later, these map 1:1 onto issues with native blocking links.

## The frontier — what can be worked right now

A ticket is grabbable when every ticket it's blocked by is done.

| # | Ticket | Blocked by | Grabbable now? |
|---|--------|-----------|----------------|
| 01 | Resolve agent-node interface drift (prefactor) | — | **yes** |
| 02 | Verify TradingAgents orchestration with an LLM key | — (needs a human to supply a key) | **yes, if a key is provided** |
| 03 | Agent 15 — Data Infrastructure & Reliability | — | **yes** |
| 04 | Agent 14 — Model Risk & Independent Validation | — | **yes** |
| 05 | Agent 2 — Portfolio Manager, core allocation | — | **DONE (2026-08-19)** |
| 06 | Agent 2 — Black-Litterman views | 05 ✅ | **yes — now unblocked** |
| 07 | Agent 11 — Execution & Microstructure | 05 ✅ | **yes — now unblocked** |
| 08 | Agent 12 — Operations & Settlement | 05 ✅, 07 | no |
| 09 | Agent 13 — Compliance & Surveillance | 07 | no |
| 10 | Agent 8 — Quant Software Engineering (code-gen) | 02 | no |
| 11 | Agent 1 — Lead Orchestrator | 01, 02 (+ ideally 05, 07, 08, 09) | no |
| 12 | Agent 5 — Quantum & Optimization | — | **deferred by policy** |
| 13 | Agent 16 — Treasury & Funding | — | **deferred by policy** |

Grabbable now: **01, 03, 04, 06, 07**. Ticket 05 is done (2026-08-19), which unblocked 06 and 07.
Ticket 02 is in progress — keys are configured and partially verified, but blocked on external
provider capacity (see its findings section).

## Two blocking edges the spec's prose graph missed

Both were found by checking the repo rather than re-reading the spec, and both are recorded here because
they change what's actually workable:

1. **No LLM API key is configured** — no `.env`, no `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` in the
   environment. Agent 8 (code generation) and Agent 1 (which forks TradingAgents' LLM-driven graph) are
   blocked on *credentials*, not code. The spec's graph modelled only code dependencies, so this was
   invisible in it. Ticket 02 is where the key gets configured and its real per-decision cost measured.

2. **The agent-node interface is documented but not implemented.** `CLAUDE.md` states every agent exposes
   `run(state) -> state` matching the LangGraph node signature. None of the six built agents do — they
   expose `run(topics, ...)`, `assess(...)`, `generate(...)`, `run(prices, volumes, ...)`, and a toolkit
   of bare methods. Agent 1 cannot wire six different call shapes into one `StateGraph`, so ticket 01
   resolves the drift before ticket 11 is built on a false premise.

## Already built (not ticketed)

Agents 2 (portfolio), 3 (research), 4 (stats), 6 (macro), 7 (alpha), 9 (backtest), and 10 (CRO) are built and verified
against live data. See `CLAUDE.md`'s architecture map for what's built vs. deliberately deferred inside
each.

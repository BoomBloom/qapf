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
| 02 | Verify TradingAgents orchestration with an LLM key | — | **DONE (2026-08-19)** — ~$0.68/decision |
| 03 | Agent 15 — Data Infrastructure & Reliability | — | **DONE (2026-08-19)** |
| 04 | Agent 14 — Model Risk & Independent Validation | — | **DONE (2026-08-19)** |
| 05 | Agent 2 — Portfolio Manager, core allocation | — | **DONE (2026-08-19)** |
| 06 | Agent 2 — Black-Litterman views | 05 ✅ | **yes — now unblocked** |
| 07 | Agent 11 — Execution & Microstructure | 05 ✅ | **DONE (2026-08-19)** |
| 08 | Agent 12 — Operations & Settlement | 05 ✅, 07 ✅ | **DONE (2026-08-19)** |
| 09 | Agent 13 — Compliance & Surveillance | 07 ✅ | **DONE (2026-08-19)** |
| 10 | Agent 8 — Quant Software Engineering (code-gen) | 02 (key now funded) | **yes** |
| 11 | Agent 1 — Lead Orchestrator | 01, 02 (key now funded) | **yes, after 01** |
| 12 | Agent 5 — Quantum & Optimization | — | **deferred by policy** |
| 13 | Agent 16 — Treasury & Funding | — | **deferred by policy** |

**Done so far: 03, 04, 05, 07, 08, 09** — Agents 15, 14, 2, 11, 12, 13 are built and verified.

Grabbable now: **01** (interface prefactor), **06** (Black-Litterman), **10** (Agent 8), **11** (Agent 1,
after 01). A funded Anthropic key now exists, so 10 and 11 are no longer credential-blocked — the free-tier
finding in ticket 02 stands as a permanent record of why they were.

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

12 of 16 agents are built: 2 (portfolio), 3 (research), 4 (stats), 6 (macro), 7 (alpha), 9 (backtest),
10 (CRO), 11 (execution), 12 (operations), 13 (compliance), 14 (model risk), 15 (data infra). All are
verified against live data. See `CLAUDE.md`'s architecture map for what's built vs. deliberately deferred inside
each.

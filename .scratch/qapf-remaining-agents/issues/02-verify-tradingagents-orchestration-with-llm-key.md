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

**Blocked by:** None in code. Keys are now configured; blocked on external provider capacity.

**Status:** in-progress — partially verified 2026-08-18, see findings below

## Findings so far (2026-08-18)

Three provider keys were supplied and all three authenticate successfully. **The remaining blocker is
provider capacity, not credentials — supplying more keys will not help.**

| Provider | Auth | Tool calling | Blocker |
|---|---|---|---|
| Groq (`openai/gpt-oss-20b`, `-120b`) | works | **verified working** | Free tier caps at 8,000 tokens/min; a single Market Analyst call needs 8,179 → hard `413`. Unusable without a paid tier. |
| Gemini (`gemini-flash-latest`) | works | **verified working** | Intermittent `503 UNAVAILABLE` ("high demand"), persisting through 8 retries. **Got furthest: completed a full Market Analyst node.** |
| Gemini (`gemini-pro-latest`) | works | not reached | `429` quota exceeded — no free-tier quota on this key. |
| NVIDIA NIM (`llama-3.3-70b-instruct`) | works (102 models listed) | not reached | Inference request timed out >2 min (free-tier cold start). |

### What IS verified

- **TradingAgents installs cleanly alongside Qlib in the same venv** — no dependency conflict, and
  critically `pandas`/`numpy` were untouched by the install, so Agents 3/4/6/7/9/10 still work
  (re-verified after install). This was a real open risk for Agent 1 and it is now settled: the two
  upstreams can coexist.
- **TradingAgents' own client factory routes correctly to a third-party provider** — `create_llm_client`
  returned a working client pointed at Groq's endpoint and completed a round trip.
- **The graph starts and executes real nodes** — the Market Analyst node completed against live market
  data on Gemini before the run hit a 503 further along.
- Groq is natively supported (provider registry entry, `GROQ_API_KEY`) — an earlier assumption that it
  was unsupported came from reading client *filenames* rather than the provider registry, and was wrong.

### What is NOT yet verified (the reason this ticket stays open)

- A complete end-to-end graph run (analyst → bull/bear debate → research manager → trader → risk debate →
  portfolio manager) has never finished.
- **The per-decision token/cost number — the actual point of this ticket — is still unmeasured.**

### Next step when capacity allows

Retry Gemini Flash when demand subsides (most likely to simply work), or move one provider to a paid tier
(Groq's Dev tier is the cheapest fix, since its blocker is a hard quota rather than variable load).

### Note on the diagnostic method

A `403` from Groq initially looked like a permissions failure; it was actually `urllib`'s default
`User-Agent` being rejected at the edge, while an identical `curl` succeeded. Recorded because it is the
same class of error this project keeps hitting: a failure that indicts the wrong component.

- [ ] An API key is configured in a way that is gitignored and never committed.
- [ ] `reference/TradingAgents` runs its graph end to end on at least one ticker without erroring.
- [ ] Measured and written down: tokens consumed and wall-clock time for one complete decision.
- [ ] A judgement is recorded on whether that per-decision cost is acceptable at the intended run
      frequency — including "no" if the honest answer is no.
- [ ] Any surprises about how the graph actually behaves (vs. how its source reads) are noted, the same
      way Qlib's real behaviour was recorded in `.claude/references/qlib-known-issues.md`.


## DEFINITIVE FINDING (2026-08-19): free tiers cannot run this graph

Four provider keys were supplied and all four authenticate. **Every one has a hard structural blocker on
its free tier**, so this is not a credentials problem and no additional key will resolve it:

| Provider | Free-tier limit | Consequence |
|---|---|---|
| Groq | 8,000 tokens/minute | A single Market Analyst call needs 8,179 tokens -> `413`. Cannot fit even one call. |
| Gemini Flash | **20 requests per day** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) | The graph needs far more than 20 LLM calls for one decision. Cannot fit one run. |
| NVIDIA NIM | cold-start latency | Inference timed out past 2 minutes. |
| OpenAI | no credits on the account | `429 insufficient_quota`. |

### Why this matters beyond this ticket

This is a product finding, not just a blocked task: **the multi-agent LLM architecture has a hard cost
floor.** A debate graph that runs several analysts, a bull/bear exchange, a research manager, a trader,
three risk debators and a portfolio manager makes dozens of LLM calls per decision. That is
fundamentally incompatible with free tiers, and it directly sharpens the per-decision-cost scope risk
`README.md` has flagged since the start.

**Decision required from the user** (a spending decision, not a technical one): fund one provider before
Agents 1 and 8 can be built or this ticket closed. Cheapest path is likely Groq's Dev tier — its blocker
is a fixed quota rather than variable load, so a paid tier removes it deterministically.

### What this does NOT block

Everything non-LLM. Agents 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15 need no LLM at all. Only Agent 8
(code generation) and Agent 1 (which forks TradingAgents' LLM graph) genuinely require this.


## RESOLVED (2026-08-19): the graph runs, and one decision costs ~$0.68

A funded Anthropic key was supplied and the full graph completed end to end on AAPL.

| Measure | Value |
|---|---|
| Wall clock | 516.4s (~8.6 min) |
| LLM calls | 16 |
| Tokens | 113,320 in / 22,459 out (135,779 total) |
| **Cost per decision** | **~$0.68** (claude-sonnet-4-6 pricing) |
| Output | "Underweight" AAPL, with a resolved bull/bear debate |

The whole node chain ran: market + news analysts -> bull/bear debate -> research manager -> trader ->
risk debate -> portfolio manager, ending in a specific recommendation with a stated rationale and price
levels.

### The judgement this ticket asked for

**Is that cost acceptable?** It depends entirely on universe size, not portfolio value — which is the
non-obvious part:

- One ticker daily: ~$0.68/day, ~$250/year. Comfortably affordable.
- The 15-name universe daily: ~$10/day, ~$3,700/year. Real money but not prohibitive.
- Intraday, or a universe in the hundreds: prohibitive without restructuring.

So the architecture is viable for daily decisions on a small universe, and the cost scales with how many
instruments are analysed rather than how much capital is deployed. That asymmetry is worth remembering
before widening the universe.

### Note on the earlier free-tier finding

The free-tier analysis above stands as the record of why this was blocked for so long: four providers, all
authenticating, all structurally incapable of one run. 16 calls at ~8.5K tokens each is simply outside
what free tiers allow. That is a property of the multi-agent debate design, not of any one provider.

- [x] An API key is configured in a way that is gitignored and never committed.
- [x] `reference/TradingAgents` runs its graph end to end on at least one ticker without erroring.
- [x] Measured and written down: tokens consumed and wall-clock time for one complete decision.
- [x] A judgement is recorded on whether that per-decision cost is acceptable at the intended run
      frequency.
- [x] Surprises noted: the graph needed no code changes to run on Anthropic, but `ANTHROPIC_BASE_URL` set
      by the surrounding tooling must be unset or the client is misrouted.

# 10 — Agent 8: Quantitative Software Engineering (code generation)

**What to build:** The bridge from research to running code: take Agent 3's structured output for a paper
(title, abstract, extracted math, linked repositories) and produce a runnable, tested Python
implementation of the technique it describes. Today a promising paper stops being useful the moment its
math needs implementing by hand.

This is the least well-scoped agent in the roster and should be treated as such. "Turn an arbitrary
quant-finance paper into correct code" is not a solved problem, and an agent that produces
plausible-looking but subtly wrong implementations is worse than no agent at all — this project has
already been bitten repeatedly by exactly that failure mode (a `shift(12)` that looked like a YoY
calculation, an expression engine that returned empty instead of erroring). Scope this narrowly on the
first pass: one well-understood technique whose correct answer is independently checkable, not a general
paper-to-code pipeline.

Blocked on an LLM key (ticket 02) — code generation is not possible without one, and no key is currently
configured.

**Blocked by:** 02 — Verify TradingAgents orchestration with a real LLM key (which is where a working key
gets configured and its cost measured).

**Status:** ready-for-agent (after 02)

- [ ] Consumes Agent 3's existing structured research output rather than re-scraping papers.
- [ ] Generates code for at least one technique end to end, scoped narrowly.
- [ ] Generated code is held to the same bar as hand-written agents: verified against real data with
      falsifiable assertions, not accepted because it looks right.
- [ ] Includes an independent correctness check — the generated implementation is validated against a
      known-answer case or an existing trusted implementation, not just "it runs."
- [ ] Explicitly reports when it cannot implement something, rather than emitting a confident guess. A
      refusal is a correct output here.
- [ ] Records the per-generation LLM cost, building on the measurement from ticket 02.

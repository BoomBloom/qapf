# 07 — Agent 11: Execution & Market Microstructure

**What to build:** Turn target positions into a simulated order schedule, and estimate what actually
getting there costs. Agent 2 says "hold 8% of AAPL"; this agent answers "we currently hold 3%, so buy 5%
— split across the day this way, at roughly this slippage and market-impact cost." Without it, every
performance number in the system implicitly assumes trades fill instantly at the close with no impact,
which is the single most flattering assumption a backtest can make.

Qlib supplies the primitives: `qlib/backtest/exchange.py` and `executor.py` already model order handling,
trading limits, and per-trade costs, and Agent 9 already drives them successfully. This ticket is about
using them deliberately — TWAP/VWAP-style scheduling and an explicit slippage/impact estimate — rather
than accepting the default fill behaviour.

Blocked on ticket 05 for a real reason, not a bureaucratic one: executing Agent 9's `TopkDropoutStrategy`
top-k selection would mean building an execution engine against a placeholder allocation, then reworking
it once real position sizes exist.

**Blocked by:** 05 — Agent 2 core allocation.

**Status:** ready-for-agent

- [ ] Consumes target weights from Agent 2 and current holdings, and emits the resulting order list
      (deltas, not target states).
- [ ] Implements at least one real execution schedule (TWAP or VWAP) rather than assuming a single
      instantaneous fill.
- [ ] Produces an explicit slippage and market-impact estimate per order, with the cost model documented.
- [ ] Verified against real data: total estimated execution cost is a plausible fraction of turnover, and
      a larger order in a less liquid name costs more than a smaller one in a liquid name — assert the
      relationship, don't assume it.
- [ ] Everything stays simulated; no live broker connectivity in this ticket.
- [ ] `if __name__ == "__main__":` guard on the runner, since this touches Qlib.

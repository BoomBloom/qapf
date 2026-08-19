# 04 — Which prop-firm funding programmes, if any, permit automated multi-asset trading?

**Type:** `wayfinder:research`
**Blocked by:** None — in progress.
**Status:** CLOSED 2026-08-19 · research complete

## Question

Which prop-firm funding programmes, if any, permit automated multi-asset trading?

FIRED 2026-08-19 — a research subagent is investigating against primary sources; findings land in
`docs/research/prop-firm-rules.md`.

Why it matters even though funding is out of scope: the answer can invalidate part of the operator's
staged path. Several funding firms restrict or ban Expert Advisors and API trading outright, most are
FX/futures oriented rather than cash equities, and drawdown caps near 10% may be structurally
incompatible with any equity strategy of this risk profile.

Specifically needed: whether drawdown is static or trailing (trailing is much harder for a systematic
strategy), whether algorithmic trading is permitted at all, whether overnight and weekend holding is
allowed, and whether real cash equities are offered or only CFDs.

---

## Resolution (2026-08-19) — findings in `docs/research/prop-firm-rules.md` (firm-owned sources only)

**The drawdown problem is industry-wide, not FTMO-specific.** The loosest total-loss cap in the entire
retail prop industry is FundingPips at 12% (static); typical is 6-10%. QAPF's -36.68% is roughly **3x the
most permissive cap that exists**. FTMO is not an outlier — it is the norm.

**The binding constraint is a RATIO, not the cap.** Derived test: the strategy's return / max-drawdown
must beat the firm's profit-target / max-loss. Best available ratios: FundedNext 2-Step (0.80) and
FundingPips 2 Step Flex (0.83). Worst: Trade The Pool Swing at 2.14 (15% target against a 7% cap).

**Automation policy is where firms genuinely differ, and marketing does not predict it:**

- **Apex bans automation outright** — "AI, Autobots, algorithms, fully automated trading systems".
  Unconditionally ruled out. (Caveat: both Apex domains geo-block this location, so that section is
  unverified-by-extract rather than read directly.)
- **FundingPips explicitly permits full automation of your own EA and accepts GIT HISTORY as proof of
  ownership** — this repository literally is that proof. But MT5-only, no equities, VPS/VPN banned.
- **Topstep** has a documented REST API ($29/mo) but bans VPS/VPN and forces flat by 3:10 PM CT — no
  overnight holding, which most systematic equity strategies require.
- **FTMO** has the clearest pro-algo policy; only quantified limit is 2,000 server requests/day.
- **The5ers** requires you own the EA source (fine for self-built).

**Only Trade The Pool trades real US cash shares.** FTMO offers stock CFDs; FundedNext, The5ers and
FundingPips offer no stocks at all; Topstep and Apex are futures-only.

**Surviving candidates:** FundingPips 2 Step Flex, and FTMO 2-Step (Swing account mandatory on the funded
stage — the 1-Step must be avoided because its 10% max loss TRAILS end-of-day).

### The finding that reaches back into the codebase

**Every firm evaluates its daily limit on intraday equity including unrealised P&L. Agent 9 backtests on
daily closes.** So the -36.68% figure is itself optimistic: true intraday drawdown is worse, and any
backtested "pass" against a prop-firm rule would be measuring the wrong quantity. Ticketed as 11.

### Effect on the map

Does **not** invalidate the destination — it confirms prop funding is far off, which is why it was scoped
out. It does sharpen the operator's stated path: **prop funding works for FX/futures on MT5, and
essentially not for cash equities.** So equities-first is a personal-capital route, and the FX ambition
is what would eventually make prop funding reachable. Those are two destinations, not one path.

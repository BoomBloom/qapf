# 03 — Agent 15: Data Infrastructure & Reliability

**What to build:** A watchdog over every upstream feed this system depends on — FRED, yfinance, arXiv,
GitHub, and Qlib's bundled data store — that reports staleness, gaps, and schema drift *before* they
corrupt a downstream calculation. Running it should answer "is the data under my agents currently
trustworthy?" without anyone having to run five other agents and eyeball their output.

This agent is justified by evidence, not speculation. Four real data defects have already hit this
project, and every one was found only because a human happened to run an agent live and notice:

- FRED's `CPIAUCSL` silently missing a monthly observation, turning a `shift(12)` "YoY" into a 13-month
  change (3.54% reported vs. 3.30% true).
- Qlib's bundled sample dataset having a calendar that stops at 2020-11-10.
- Qlib's expression engine returning empty results for rolling-window operators with no error raised.
- PyGithub's `PaginatedList` raising `IndexError` when sliced past its actual result count.

The strongest acceptance criterion below is therefore a regression suite: point this agent at those four
known-bad conditions and confirm it actually flags them. An agent that can't catch the bugs we already
know about won't catch the fifth one.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Reports per-feed freshness (latest observation date vs. today) for every external source Agents 3,
      4, 6, 7, and 9 rely on.
- [ ] Detects gaps in a series where a regular cadence is expected, rather than assuming contiguity —
      the CPI failure mode.
- [ ] Detects schema/shape drift (a column or field that changed name, type, or disappeared).
- [ ] Regression suite: flags all four historical defects listed above when pointed at the conditions
      that produced them.
- [ ] Distinguishes "this feed is stale" from "this feed is down" — they need different responses.
- [ ] Follows the established verification pattern: a `__main__.py` runner asserting falsifiable
      properties against real feeds, not mocks.

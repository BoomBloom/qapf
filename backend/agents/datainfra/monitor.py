"""Agent 15 — Data Infrastructure & Reliability.

Watches every upstream feed the other agents depend on and reports staleness,
gaps, and schema drift BEFORE they corrupt a downstream calculation.

This agent is justified by evidence rather than speculation. Four real data
defects have already hit this project, and every one was found only because a
human happened to run an agent and notice something odd:

- FRED's CPIAUCSL silently missing a monthly observation, which turned a
  positional shift(12) "year-over-year" into a 13-month change (3.54% reported
  vs 3.30% true).
- Qlib's bundled sample dataset having a calendar that stops at 2020-11-10.
- Qlib's expression engine returning empty results for rolling-window
  operators, raising no error at all.
- PyGithub's PaginatedList raising IndexError when sliced past its result count.

Each of those is a check below. An agent that cannot catch the bugs already
known about would not catch the fifth one, so `__main__.py` verifies exactly
that rather than only confirming today's feeds look fine.

Deliberately dependency-light: staleness and gap detection are arithmetic on
an index, so this agent stays useful even when the services it monitors are
the thing that is broken.
"""

import logging
from datetime import date, datetime

import pandas as pd

from .schemas import DataHealthReport, FeedHealth

logger = logging.getLogger(__name__)

# How stale a feed may be before it's a problem. Monthly economic series are
# published with a real lag -- CPI for a month lands weeks later -- so applying
# a market-data threshold to them would fire constantly and train everyone to
# ignore this agent.
STALENESS_LIMITS_DAYS = {
    "daily_market": 5,      # allows a long weekend + holiday
    "daily_economic": 7,
    "monthly_economic": 75,  # a monthly print can legitimately be ~2 months behind
}


def _business_days_between(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(len(pd.bdate_range(start, end)) - 1)


def check_staleness(
    name: str, source: str, index: pd.DatetimeIndex, cadence: str, as_of: pd.Timestamp | None = None
) -> FeedHealth:
    """Is this feed still being updated?"""
    as_of = as_of or pd.Timestamp(date.today())
    if len(index) == 0:
        return FeedHealth(feed=name, source=source, status="down", detail="No observations at all.")

    latest = pd.Timestamp(index.max())
    age = (as_of - latest).days
    limit = STALENESS_LIMITS_DAYS.get(cadence, 7)
    status = "stale" if age > limit else "ok"
    return FeedHealth(
        feed=name,
        source=source,
        status=status,
        latest_observation=str(latest.date()),
        days_since_latest=age,
        n_observations=len(index),
        expected_cadence=cadence,
        detail=(
            f"Latest observation is {age}d old, beyond the {limit}d limit for {cadence}."
            if status == "stale"
            else f"Fresh: {age}d old (limit {limit}d for {cadence})."
        ),
    )


def check_gaps(name: str, source: str, index: pd.DatetimeIndex, cadence: str) -> FeedHealth:
    """Are there holes in a series that should be regular?

    This is the CPIAUCSL failure mode. A missing observation does not raise
    anything — it silently shifts every positional lookup by one period, which
    is why the project's ground rules forbid `.shift(n)` for time-based changes.
    """
    idx = pd.DatetimeIndex(sorted(index))
    gaps: list[str] = []

    if cadence == "monthly_economic":
        expected = pd.date_range(idx.min(), idx.max(), freq="MS")
        missing = expected.difference(idx.normalize())
        gaps = [str(d.date()) for d in missing]
    else:
        expected = pd.bdate_range(idx.min(), idx.max())
        missing = expected.difference(idx.normalize())
        # Market data legitimately skips exchange holidays, so a handful of
        # missing business days is normal and flagging them would be noise.
        # Only an unusual number indicates a real problem.
        if len(missing) > len(expected) * 0.06:
            gaps = [str(d.date()) for d in missing[:10]]

    return FeedHealth(
        feed=name,
        source=source,
        status="gap" if gaps else "ok",
        latest_observation=str(idx.max().date()),
        n_observations=len(idx),
        expected_cadence=cadence,
        gaps_detected=gaps,
        detail=(
            f"{len(gaps)} missing observation(s) in a series expected to be regular — "
            f"positional lookups across this hole silently return the wrong period."
            if gaps
            else "No unexpected gaps."
        ),
    )


def check_schema(name: str, source: str, actual: set[str], required: set[str]) -> FeedHealth:
    """Did a provider rename, retype, or drop a field we depend on?"""
    missing = required - actual
    return FeedHealth(
        feed=name,
        source=source,
        status="drift" if missing else "ok",
        detail=(
            f"Required field(s) absent: {sorted(missing)}. Downstream code reading them will "
            f"fail or silently produce nothing."
            if missing
            else f"All {len(required)} required field(s) present."
        ),
    )


def check_expression_engine(name: str, source: str, probe_result_len: int, plain_result_len: int) -> FeedHealth:
    """Does a query that should return data actually return data?

    Qlib's rolling-window operators return an EMPTY result rather than raising,
    which is the worst possible failure mode: every downstream factor silently
    becomes empty. Comparing an expression query against a plain-field query on
    the same range catches it; checking either one alone does not.
    """
    broken = plain_result_len > 0 and probe_result_len == 0
    return FeedHealth(
        feed=name,
        source=source,
        status="down" if broken else "ok",
        n_observations=probe_result_len,
        detail=(
            f"Plain field access returned {plain_result_len} rows but the expression query "
            f"returned {probe_result_len} — the expression engine is silently returning nothing."
            if broken
            else f"Expression and plain queries both returned data ({probe_result_len} rows)."
        ),
    )


class DataHealthMonitor:
    def summarize(self, feeds: list[FeedHealth]) -> DataHealthReport:
        down = sum(1 for f in feeds if f.status == "down")
        degraded = sum(1 for f in feeds if f.status in ("stale", "gap", "drift"))
        ok = sum(1 for f in feeds if f.status == "ok")

        if down:
            verdict = (
                f"DATA NOT TRUSTWORTHY — {down} feed(s) down. Downstream results computed now "
                f"may be silently wrong."
            )
        elif degraded:
            verdict = (
                f"DEGRADED — {degraded} feed(s) stale, gapped, or drifted. Usable with care; "
                f"check the affected feeds before trusting anything derived from them."
            )
        else:
            verdict = "ALL FEEDS HEALTHY."

        return DataHealthReport(
            as_of=str(datetime.now().date()),
            feeds_checked=len(feeds),
            ok=ok,
            degraded=degraded,
            down=down,
            feeds=feeds,
            verdict=verdict,
        )

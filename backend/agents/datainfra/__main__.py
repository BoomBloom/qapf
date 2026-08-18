"""Manual verification runner: python -m agents.datainfra

The acceptance test for this agent is NOT "today's feeds look fine" — it's
"does it catch the four data defects this project already hit?" Those are
replayed below as a regression suite, then the live feeds are checked.
"""

import logging

import pandas as pd
import yfinance as yf

from agents.macro.fred_client import FredClient

from .monitor import (
    DataHealthMonitor,
    check_expression_engine,
    check_gaps,
    check_schema,
    check_staleness,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def regression_cpi_gap():
    """DEFECT 1: FRED's CPIAUCSL was missing 2025-10-01. A positional shift(12)
    across that hole reported a 13-month change as "year-over-year"."""
    idx = pd.date_range("2024-01-01", "2026-01-01", freq="MS")
    holed = idx.delete(list(idx).index(pd.Timestamp("2025-10-01")))
    health = check_gaps("cpi", "FRED", pd.DatetimeIndex(holed), "monthly_economic")
    assert health.status == "gap", "did NOT detect the known CPI gap"
    assert "2025-10-01" in health.gaps_detected, f"wrong gap found: {health.gaps_detected}"
    print(f"  [1/4] CPI gap        DETECTED — flagged {health.gaps_detected}")


def regression_stale_qlib_calendar():
    """DEFECT 2: Qlib's bundled dataset calendar stops at 2020-11-10, but a
    backtest asking for later dates fails confusingly rather than saying the
    data is old."""
    idx = pd.bdate_range("2020-01-01", "2020-11-10")
    health = check_staleness("qlib_us_bundle", "qlib", idx, "daily_market",
                             as_of=pd.Timestamp("2026-08-19"))
    assert health.status == "stale", "did NOT detect the stale Qlib calendar"
    print(f"  [2/4] Stale calendar DETECTED — {health.days_since_latest}d old "
          f"(latest {health.latest_observation})")


def regression_qlib_expression_engine():
    """DEFECT 3: Qlib's Ref()/Mean()/Std() return an EMPTY result with no
    exception, so every factor built on them silently becomes nothing."""
    health = check_expression_engine("qlib_expressions", "qlib",
                                     probe_result_len=0, plain_result_len=240)
    assert health.status == "down", "did NOT detect the silent expression-engine failure"
    print(f"  [3/4] Silent empties DETECTED — {health.detail[:76]}...")


def regression_schema_drift():
    """DEFECT 4 (generalized): a provider dropping or renaming a field we read.
    PyGithub's pagination break was this shape — code depending on a provider
    contract that changed underneath it."""
    health = check_schema("yfinance_ohlcv", "yfinance",
                          actual={"Open", "High", "Low", "Close"},  # Volume dropped
                          required={"Open", "High", "Low", "Close", "Volume"})
    assert health.status == "drift", "did NOT detect the missing required field"
    print(f"  [4/4] Schema drift   DETECTED — {health.detail[:76]}...")


def test_healthy_feed_not_flagged():
    """A fresh, complete feed must come back clean, or the agent is just noise."""
    idx = pd.bdate_range(end=pd.Timestamp.today(), periods=200)
    stale = check_staleness("test", "test", idx, "daily_market")
    gaps = check_gaps("test", "test", idx, "daily_market")
    schema = check_schema("test", "test", {"a", "b"}, {"a"})
    assert all(h.status == "ok" for h in (stale, gaps, schema)), (
        f"clean feed wrongly flagged: {[(h.feed, h.status) for h in (stale, gaps, schema)]}"
    )
    print("  [--]  Healthy feed    correctly NOT flagged (no false positive)")


def main():
    print("=== Agent 15 — Data Infrastructure & Reliability ===\n")
    print("Regression suite: the four data defects this project actually hit.")
    print("(An agent that can't catch known bugs won't catch the next one.)\n")
    regression_cpi_gap()
    regression_stale_qlib_calendar()
    regression_qlib_expression_engine()
    regression_schema_drift()
    test_healthy_feed_not_flagged()
    print("\nAll 4 known defects re-detected; healthy feed not flagged.\n")

    print("=== Live feed health ===\n")
    feeds = []
    client = FredClient()
    for alias, cadence in [
        ("cpi", "monthly_economic"),
        ("core_cpi", "monthly_economic"),
        ("industrial_production", "monthly_economic"),
        ("unemployment_rate", "monthly_economic"),
        ("yield_curve", "daily_economic"),
        ("vix", "daily_economic"),
    ]:
        try:
            s = client.fetch_series(alias, start_date="2015-01-01")
            feeds.append(check_staleness(alias, "FRED", s.index, cadence))
            feeds.append(check_gaps(alias, "FRED", s.index, cadence))
        except Exception as e:
            feeds.append(check_staleness(alias, "FRED", pd.DatetimeIndex([]), cadence))
            logger.warning("%s failed: %s", alias, e)

    try:
        data = yf.download(["AAPL", "MSFT"], period="6mo", interval="1d",
                           progress=False, auto_adjust=True)
        px = data["Close"].dropna(how="all")
        feeds.append(check_staleness("yfinance_prices", "yfinance", px.index, "daily_market"))
        feeds.append(check_gaps("yfinance_prices", "yfinance", px.index, "daily_market"))
        feeds.append(check_schema("yfinance_ohlcv", "yfinance",
                                  set(data.columns.get_level_values(0)),
                                  {"Open", "High", "Low", "Close", "Volume"}))
    except Exception as e:
        logger.warning("yfinance failed: %s", e)

    report = DataHealthMonitor().summarize(feeds)
    print(f"{'Feed':<26}{'Source':<10}{'Status':<9}{'Latest':<13}Detail")
    for f in report.feeds:
        print(f"{f.feed:<26}{f.source:<10}{f.status:<9}{(f.latest_observation or '-'):<13}"
              f"{f.detail[:58]}")

    print(f"\nChecked {report.feeds_checked} | ok {report.ok} | degraded {report.degraded} "
          f"| down {report.down}")
    print(f"VERDICT: {report.verdict}")


if __name__ == "__main__":
    main()

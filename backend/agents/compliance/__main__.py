"""Manual verification runner: python -m agents.compliance

A detector that never fires proves nothing, so every rule is tested BOTH ways:
it must fire on a constructed violation and stay quiet on clean activity.
"""

import logging

import pandas as pd
import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.execution.planner import ExecutionPlanner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator

from .surveillance import ComplianceSurveillance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "JPM", "V", "WMT",
            "KO", "PEP", "XOM", "CVX", "JNJ", "PG", "HD"]

SECTORS = {
    "AAPL": "tech", "MSFT": "tech", "GOOGL": "tech", "AMZN": "tech", "NVDA": "tech",
    "JPM": "financials", "V": "financials",
    "WMT": "staples", "KO": "staples", "PEP": "staples", "PG": "staples",
    "XOM": "energy", "CVX": "energy",
    "JNJ": "healthcare", "HD": "discretionary",
}


def test_catches_restricted_list():
    orders = pd.DataFrame([{"date": "2026-08-10", "ticker": "AAPL", "side": "buy", "notional": 1e5}])
    r = ComplianceSurveillance(restricted_list={"AAPL"}).review(orders, {"AAPL": 0.1})
    assert any(a.rule == "restricted_list" and a.severity == "violation" for a in r.alerts)
    print("  Restricted list  : FIRES on a restricted trade")


def test_catches_position_limit():
    orders = pd.DataFrame(columns=["date", "ticker", "side", "notional"])
    r = ComplianceSurveillance(max_position_pct=0.35).review(orders, {"NVDA": 0.50})
    assert any(a.rule == "position_limit" and a.severity == "violation" for a in r.alerts)
    print("  Position limit   : FIRES on a 50% position against a 35% cap")


def test_catches_wash_pattern():
    """Buy then sell the same name two days apart — the wash signature, and
    equally the signature of a signal flip-flopping between rebalances."""
    orders = pd.DataFrame([
        {"date": "2026-08-10", "ticker": "KO", "side": "buy", "notional": 5e4},
        {"date": "2026-08-12", "ticker": "KO", "side": "sell", "notional": 5e4},
    ])
    r = ComplianceSurveillance().review(orders, {"KO": 0.0})
    assert any(a.rule == "wash_trading" for a in r.alerts), "wash pattern NOT detected"
    print("  Wash trading     : FIRES on buy-then-sell within 2 days")


def test_catches_sector_concentration():
    orders = pd.DataFrame(columns=["date", "ticker", "side", "notional"])
    weights = {"AAPL": 0.25, "MSFT": 0.25, "GOOGL": 0.25}  # 75% tech
    r = ComplianceSurveillance(max_sector_pct=0.60).review(orders, weights, sectors=SECTORS)
    assert any(a.rule == "sector_concentration" for a in r.alerts)
    print("  Sector limit     : FIRES on 75% tech against a 60% guideline")


def test_clean_activity_is_clean():
    """The critical negative case: normal trading must produce no alerts, or
    the agent is noise and will be ignored."""
    orders = pd.DataFrame([
        {"date": "2026-08-01", "ticker": "KO", "side": "buy", "notional": 5e4},
        {"date": "2026-08-02", "ticker": "PG", "side": "buy", "notional": 5e4},
    ])
    weights = {"KO": 0.2, "PG": 0.2, "JPM": 0.2, "JNJ": 0.2}
    r = ComplianceSurveillance(restricted_list={"TSLA"}).review(orders, weights, sectors=SECTORS)
    assert r.clean, f"clean activity wrongly flagged: {[a.detail for a in r.alerts]}"
    print("  Clean activity   : correctly SILENT (no false positives)")


def main():
    print("=== Agent 13 — Compliance & Regulatory Surveillance ===\n")
    print("Every rule tested in both directions (must fire on a violation, stay quiet when clean):")
    test_catches_restricted_list()
    test_catches_position_limit()
    test_catches_wash_pattern()
    test_catches_sector_concentration()
    test_clean_activity_is_clean()

    print("\n=== Surveilling the real pipeline's order flow ===")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices, volumes = data["Close"].dropna(how="all"), data["Volume"].dropna(how="all")

    assessment = MacroRegimeClassifier().assess()
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    alloc = PortfolioAllocator().allocate(bundle, prices, assessment.regime, assessment.risk_regime)
    plan = ExecutionPlanner(algo="vwap").plan(alloc, prices, volumes, 1_000_000)

    orders = pd.DataFrame([
        {"date": alloc.as_of, "ticker": o.ticker, "side": o.side, "notional": o.notional}
        for o in plan.orders
    ])
    weights = {p.ticker: p.weight for p in alloc.positions}

    report = ComplianceSurveillance(
        max_position_pct=0.35, max_sector_pct=0.60, restricted_list=set(),
    ).review(orders, weights, sectors=SECTORS, as_of=alloc.as_of)

    print(f"\nOrders reviewed: {report.orders_reviewed} | rules: {', '.join(report.rules_checked)}")
    print(f"Violations: {report.violations} | Warnings: {report.warnings}")
    if report.alerts:
        print("\nAlerts:")
        for a in report.alerts:
            print(f"  [{a.severity.upper():<9}] ({a.rule}) {a.detail}")
    else:
        print("\nNo alerts — order flow is clean against all rules.")

    print("\nAudit trail:")
    for line in report.audit_trail:
        print(f"  - {line}")


if __name__ == "__main__":
    main()

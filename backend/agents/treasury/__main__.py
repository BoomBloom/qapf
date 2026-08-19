"""Manual verification runner: python -m agents.treasury

Chains into a real Agent 2 allocation (which itself pulls live Agent 6/7
output) for the cash-yield check, so the account numbers being taxed aren't
synthetic. Margin-call logic is checked against a deliberately synthetic
over-leveraged case, clearly labeled as such -- QAPF's real Agent 2 output
is long-only/cash-account and should never actually trigger one.
"""

import logging

import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator

from .manager import TreasuryManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]


def test_cash_yield_boundaries(manager: TreasuryManager):
    """Independently-computable boundary checks, not just a live-data demo."""
    below_threshold = manager.assess_cash_yield(nav=250_000, cash_balance=5_000)
    assert below_threshold.annual_interest == 0.0, "cash below the uncompensated threshold must earn $0"
    print("Uncompensated-threshold check PASSED: $5,000 cash (below $10k) earns $0.")

    half_tier = manager.assess_cash_yield(nav=50_000, cash_balance=60_000)
    assert abs(half_tier.proration_factor - 0.5) < 1e-9, f"NAV=$50k should prorate to exactly 0.5, got {half_tier.proration_factor}"
    print("Proration check PASSED: NAV=$50,000 (half of the $100k top tier) prorates to exactly 50%.")

    full_tier = manager.assess_cash_yield(nav=250_000, cash_balance=60_000)
    assert full_tier.proration_factor == 1.0, "NAV above the top tier must cap at 1.0, not exceed it"
    print("Full-tier cap check PASSED: NAV=$250,000 (above the $100k top tier) caps at 100%, doesn't exceed it.")


def test_margin_call_logic(manager: TreasuryManager):
    """Synthetic stress case -- QAPF's real Agent 2 output is long-only/
    cash-account and gross_position_value should never exceed nav in
    practice, so a real call can't be demonstrated from live output."""
    calm = manager.assess_margin_requirement(gross_position_value=80_000, nav=100_000)
    assert not calm.margin_call, "80% gross on $100k NAV is well within Reg T/FINRA limits"

    stressed = manager.assess_margin_requirement(gross_position_value=95_000, nav=20_000)
    assert stressed.margin_call, "95% of NAV in maintenance terms on a $20k NAV account should call"
    assert stressed.excess_liquidity < 0

    print("Margin-call logic PASSED: calm case (80% gross / $100k NAV) has no call; "
          f"synthetic stressed case has a real call (${abs(stressed.excess_liquidity):,.2f} short).")


def main():
    manager = TreasuryManager()

    print("=== Boundary checks (independently computable, no live data needed) ===")
    test_cash_yield_boundaries(manager)
    test_margin_call_logic(manager)

    print("\n=== Live check: cash yield on a real Agent 2 allocation ===")
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")

    assessment = MacroRegimeClassifier().assess()
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    allocation = PortfolioAllocator().allocate(bundle, prices, assessment.regime, assessment.risk_regime)

    for portfolio_value in (1_000.0, 250_000.0):
        cash_balance = allocation.cash_weight * portfolio_value
        yield_result = manager.assess_cash_yield(nav=portfolio_value, cash_balance=cash_balance)
        print(f"\n  Account ${portfolio_value:,.0f} | cash_weight={allocation.cash_weight:.1%} "
              f"| cash_balance=${cash_balance:,.2f}")
        for line in yield_result.reasoning:
            print(f"    - {line}")

    print("\n=== Live check: margin requirement on the real allocation (informational only) ===")
    gross_value = allocation.gross_exposure * 250_000.0
    margin = manager.assess_margin_requirement(gross_position_value=gross_value, nav=250_000.0)
    for line in margin.reasoning:
        print(f"  - {line}")

    print("\nAll checks PASSED.")


if __name__ == "__main__":
    main()

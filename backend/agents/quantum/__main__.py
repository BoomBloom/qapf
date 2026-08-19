"""Manual verification runner: python -m agents.quantum

Pulls REAL live signals (Agent 7) and a REAL covariance estimate (Agent 2's
own Ledoit-Wolf shrinkage estimator) — not synthetic data — and runs the
cardinality-constrained subset-selection comparison described in
optimizer.py's module docstring.

The correctness bar this script actually enforces: `exact_qubo` (the QUBO's
true ground state, computed exactly via NumPyMinimumEigensolver) MUST match
`brute_force` (an independent enumeration of the real constrained objective,
with no QUBO or penalty involved at all). If those two disagree, the QUBO
encoding or penalty size has a real bug -- unlike QAOA not matching, which
README's own Scope warning already predicts and this script only reports,
never asserts against.
"""

import logging

import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator

from .optimizer import QuantumPortfolioOptimizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]

K = 3
RISK_AVERSION = 0.5
MAX_CANDIDATES = 6  # kept modest deliberately -- see optimizer.py's module docstring on why
REPS = 1
MAXITER = 50


def main():
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")

    print("\n=== Pulling live signals from Agent 7 (via Agent 6's regime) ===")
    assessment = MacroRegimeClassifier().assess()
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    signals = {s.ticker: s.signal for s in bundle.signals}
    print(f"  {len(signals)} live signals, regime={assessment.regime.value}")

    print("\n=== Estimating covariance via Agent 2's shrinkage estimator ===")
    allocator = PortfolioAllocator()
    covariance = allocator.estimate_covariance(prices, UNIVERSE)

    print(f"\n=== Solving: select {K} of {len(UNIVERSE)} names, risk_aversion={RISK_AVERSION} ===")
    optimizer = QuantumPortfolioOptimizer(max_candidates=MAX_CANDIDATES, reps=REPS, maxiter=MAXITER)
    result = optimizer.select_subset(signals, covariance, k=K, risk_aversion=RISK_AVERSION)

    print(f"\nCandidate pool ({len(result.universe)}): {result.universe}\n")
    for label, r in [("Brute force (ground truth)", result.brute_force),
                      ("Exact QUBO (NumPyMinimumEigensolver)", result.exact_qubo),
                      ("QAOA", result.qaoa)]:
        print(f"{label}:")
        print(f"  selected={r.selected}  objective={r.objective_value:.6f}  "
              f"feasible={r.feasible}  time={r.wall_clock_seconds:.4f}s")

    print("\n=== Reasoning ===")
    for line in result.reasoning:
        print(f"- {line}")

    print(f"\nQAOA matched brute-force optimum: {result.qaoa_matches_brute_force}")
    print(f"QAOA matched exact QUBO ground state: {result.qaoa_matches_exact_qubo}")
    print(f"QAOA objective gap vs true optimum: {result.qaoa_objective_gap_pct:+.2f}%")

    print("\n=== Correctness check (the one this script actually enforces) ===")
    assert set(result.exact_qubo.selected) == set(result.brute_force.selected), (
        f"QUBO ENCODING BUG: the QUBO's own exact ground state {result.exact_qubo.selected} "
        f"disagrees with the independently brute-forced true optimum {result.brute_force.selected}. "
        f"Unlike QAOA approximating imperfectly (expected), this means the QUBO/penalty is wrong."
    )
    print("PASSED: the QUBO's exact ground state matches the independently brute-forced true "
          "optimum -- the encoding itself is correct, whatever QAOA did with it.")

    print(f"\n=== Verdict ===")
    if result.qaoa_matches_brute_force:
        speedup = result.qaoa.wall_clock_seconds / max(result.brute_force.wall_clock_seconds, 1e-9)
        print(f"QAOA found the correct answer this run -- but took {speedup:,.0f}x longer than brute "
              f"force to get there ({result.qaoa.wall_clock_seconds:.4f}s vs "
              f"{result.brute_force.wall_clock_seconds:.4f}s) on a problem small enough that brute force "
              f"is instant. This IS README's Scope warning, not a contradiction of it: matching the "
              f"classical answer at orders-of-magnitude more cost is exactly 'does not beat classical "
              f"solvers... a research curiosity, not a critical path item.' Agent 2's classical "
              f"cvxpy-based optimizer remains what QAPF actually uses for portfolio construction.")
    else:
        print("QAOA did NOT find the true optimum -- consistent with README's Scope warning "
              "('QAOA/QUBO on today's simulators does not beat classical solvers... keep it as a "
              "research curiosity, not a critical path item'). This is confirmation, not a failure "
              "of this agent -- Agent 2's classical cvxpy-based optimizer remains what QAPF actually "
              "uses for portfolio construction.")


if __name__ == "__main__":
    main()

"""Manual verification runner: python -m agents.stats

Uses real market data (via yfinance) rather than synthetic series. KO/PEP is
often cited as a textbook cointegration candidate and XOM as an unrelated
control, but cointegration is a property of a specific sample window, not a
permanent fact about a pair -- so this script reports whatever the tests
actually find for the current window rather than asserting an outcome.
"""

import numpy as np
import yfinance as yf

from .toolkit import ProbabilityStatisticsToolkit


def main():
    toolkit = ProbabilityStatisticsToolkit()

    print("Downloading KO, PEP, XOM (2 years, daily)...")
    data = yf.download(["KO", "PEP", "XOM"], period="2y", interval="1d", progress=False)
    close = data["Close"].dropna()

    print("\n=== Stationarity: KO price level (expect NON-stationary) ===")
    result = toolkit.test_stationarity(close["KO"], name="KO price")
    print(result.model_dump_json(indent=2))

    print("\n=== Stationarity: KO log returns (expect stationary) ===")
    ko_log_returns = np.log(close["KO"]).diff()
    result = toolkit.test_stationarity(ko_log_returns, name="KO log returns")
    print(result.model_dump_json(indent=2))

    print("\n=== Cointegration (Engle-Granger): KO vs PEP ===")
    result = toolkit.test_cointegration_engle_granger(close["KO"], close["PEP"], "KO", "PEP")
    print(result.model_dump_json(indent=2))

    print("\n=== Cointegration (Engle-Granger): KO vs XOM (unrelated-sector control) ===")
    result = toolkit.test_cointegration_engle_granger(close["KO"], close["XOM"], "KO", "XOM")
    print(result.model_dump_json(indent=2))

    print("\n=== Johansen test: KO, PEP, XOM jointly ===")
    result = toolkit.test_cointegration_johansen(close[["KO", "PEP", "XOM"]])
    print(result.model_dump_json(indent=2))

    print("\n=== Deflated Sharpe Ratio: KO daily returns, n_trials=1 vs n_trials=100 ===")
    ko_returns = close["KO"].pct_change().dropna()
    dsr_1 = toolkit.deflated_sharpe_ratio(ko_returns, n_trials=1)
    dsr_100 = toolkit.deflated_sharpe_ratio(ko_returns, n_trials=100)
    print("n_trials=1:  ", dsr_1.model_dump_json(indent=2))
    print("n_trials=100:", dsr_100.model_dump_json(indent=2))
    assert dsr_100.deflated_sharpe_ratio <= dsr_1.deflated_sharpe_ratio, (
        "DSR should decrease (or stay equal) as the number of trials increases "
        "-- more multiple-testing should make the same result LESS convincing."
    )
    print("\nSanity check passed: DSR correctly decreases as n_trials increases.")


if __name__ == "__main__":
    main()

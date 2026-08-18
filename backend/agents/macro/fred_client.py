"""Keyless FRED (Federal Reserve Economic Data) client.

The ``MACRO_SERIES`` alias map below is adapted from TradingAgents
(Apache-2.0, reference/TradingAgents/tradingagents/dataflows/fred.py) — that
curated alias->series-ID mapping is genuinely useful domain knowledge and is
reused with attribution per its license.

The fetch mechanism, however, is deliberately different. TradingAgents uses
FRED's JSON API, which requires a free ``FRED_API_KEY``. This client uses
FRED's public CSV endpoint (``fredgraph.csv``) instead, which needs no key at
all — verified working 2026-08-18. That keeps Agent 6 runnable with zero API
keys. Trade-off: the CSV endpoint returns only observations (no series title,
units, or frequency metadata), which the JSON API does provide. If that
metadata is ever needed, add an optional keyed path rather than replacing this
one.
"""

import io
import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
REQUEST_TIMEOUT = 30

# Adapted from TradingAgents (Apache-2.0) — see module docstring.
MACRO_SERIES = {
    # Policy rate & Treasury yields
    "fed_funds_rate": "FEDFUNDS",
    "2y_treasury": "DGS2",
    "10y_treasury": "DGS10",
    "30y_treasury": "DGS30",
    "10y_2y_spread": "T10Y2Y",
    "yield_curve": "T10Y2Y",
    # Inflation
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "pce": "PCEPI",
    "core_pce": "PCEPILFE",
    "inflation_expectations": "T10YIE",
    # Growth & output
    "real_gdp": "GDPC1",
    "industrial_production": "INDPRO",
    # Labor
    "unemployment_rate": "UNRATE",
    "nonfarm_payrolls": "PAYEMS",
    "initial_claims": "ICSA",
    # Money & markets
    "m2": "M2SL",
    "vix": "VIXCLS",
    "dollar_index": "DTWEXBGS",
    # Sentiment & housing
    "consumer_sentiment": "UMCSENT",
    "housing_starts": "HOUST",
    "retail_sales": "RSAFS",
}


class FredClient:
    """Fetches FRED series as pandas Series, without needing an API key."""

    def resolve_series_id(self, indicator: str) -> str:
        key = indicator.strip().lower().replace(" ", "_").replace("-", "_")
        if key in MACRO_SERIES:
            return MACRO_SERIES[key]
        candidate = indicator.strip().upper()
        if not candidate or len(candidate) > 30 or any(c.isspace() for c in candidate):
            raise ValueError(
                f"'{indicator}' is not a known macro alias or a valid FRED series ID. "
                f"Use an alias (e.g. 'cpi', 'unemployment_rate', '10y_treasury') or a "
                f"raw FRED series ID (e.g. 'CPIAUCSL')."
            )
        return candidate

    def fetch_series(self, indicator: str, start_date: str | None = None) -> pd.Series:
        """Fetch one series as a date-indexed float Series with missing values dropped.

        FRED encodes missing observations as ".", which becomes NaN via
        ``pd.to_numeric(errors="coerce")`` and is then dropped.
        """
        series_id = self.resolve_series_id(indicator)
        params = {"id": series_id}
        if start_date:
            params["cosd"] = start_date

        response = requests.get(FRED_CSV_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))
        if df.shape[1] < 2:
            raise ValueError(f"Unexpected FRED CSV shape for {series_id}: {list(df.columns)}")

        # FRED's date column has been named both "DATE" and "observation_date";
        # take it positionally so a future rename doesn't break this.
        date_col, value_col = df.columns[0], df.columns[1]
        df[date_col] = pd.to_datetime(df[date_col])
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        series = df.set_index(date_col)[value_col].dropna()
        series.name = series_id

        if series.empty:
            raise ValueError(f"FRED returned no usable observations for {series_id}.")

        logger.info("Fetched %s: %d observations, latest %s", series_id, len(series), series.index[-1].date())
        return series

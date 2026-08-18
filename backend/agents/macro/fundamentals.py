"""Company fundamentals ingestion via yfinance (keyless).

TradingAgents routes fundamentals through either yfinance or Alpha Vantage
(the latter needs a key). This keeps to the keyless yfinance path so Agent 6
runs with no credentials; add an Alpha Vantage path later if per-field
coverage proves insufficient.
"""

import logging

import yfinance as yf

from .schemas import FundamentalSnapshot

logger = logging.getLogger(__name__)


def _get_float(info: dict, key: str) -> float | None:
    """yfinance omits keys entirely for unavailable fields, and occasionally
    returns non-numeric placeholders — treat both as missing rather than
    coercing them into a misleading 0.0."""
    value = info.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class FundamentalsIngestor:
    def fetch(self, ticker: str) -> FundamentalSnapshot:
        info = yf.Ticker(ticker).info
        if not info or info.get("quoteType") is None:
            raise ValueError(f"No fundamental data returned for '{ticker}'.")

        logger.info("Fetched fundamentals for %s (%s)", ticker, info.get("shortName"))
        return FundamentalSnapshot(
            ticker=ticker.upper(),
            company_name=info.get("shortName") or info.get("longName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=_get_float(info, "marketCap"),
            trailing_pe=_get_float(info, "trailingPE"),
            forward_pe=_get_float(info, "forwardPE"),
            price_to_book=_get_float(info, "priceToBook"),
            profit_margin=_get_float(info, "profitMargins"),
            return_on_equity=_get_float(info, "returnOnEquity"),
            revenue_growth=_get_float(info, "revenueGrowth"),
            earnings_growth=_get_float(info, "earningsGrowth"),
            debt_to_equity=_get_float(info, "debtToEquity"),
            free_cashflow=_get_float(info, "freeCashflow"),
            dividend_yield=_get_float(info, "dividendYield"),
            beta=_get_float(info, "beta"),
        )

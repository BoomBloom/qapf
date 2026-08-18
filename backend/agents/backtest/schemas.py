from pydantic import BaseModel


class RebalanceRecord(BaseModel):
    """One walk-forward rebalance: the regime/signal state that was actually
    live at that date, kept for audit — a backtest result should always be
    traceable back to what the agents believed at each decision point."""

    date: str
    regime: str
    risk_regime: str
    longs: list[str]
    shorts: list[str]


class BacktestReport(BaseModel):
    universe: list[str]
    start: str
    end: str
    n_rebalances: int
    initial_account: float
    final_account: float
    total_return: float
    benchmark_return: float
    annualized_sharpe: float
    max_drawdown: float
    # From Agent 4 (Probability & Statistics) — the DSR corrects the Sharpe for
    # how many effective factor "trials" produced this result, so a good-looking
    # backtest can be checked against overfitting rather than taken at face value.
    deflated_sharpe_ratio: float
    deflated_sharpe_n_trials: int
    rebalance_log: list[RebalanceRecord]

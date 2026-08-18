from pydantic import BaseModel


class StationarityResult(BaseModel):
    series_name: str
    adf_statistic: float
    adf_pvalue: float
    adf_is_stationary: bool  # ADF null hypothesis is a unit root: p < 0.05 rejects it
    kpss_statistic: float
    kpss_pvalue: float
    kpss_is_stationary: bool  # KPSS null hypothesis is stationarity: p > 0.05 fails to reject it
    agree: bool  # both tests reaching the same conclusion is the standard robustness check


class CointegrationResult(BaseModel):
    series_a: str
    series_b: str
    method: str
    test_statistic: float
    pvalue: float
    is_cointegrated: bool
    hedge_ratio: float


class JohansenResult(BaseModel):
    series_names: list[str]
    trace_statistics: list[float]
    critical_values_95: list[float]
    cointegrating_rank: int


class DeflatedSharpeResult(BaseModel):
    observed_sharpe: float
    n_trials: int
    n_observations: int
    skewness: float
    kurtosis: float
    expected_max_sharpe: float
    deflated_sharpe_ratio: float
    is_significant: bool

"""Agent 14 — Model Risk & Independent Validation.

Deliberately independent of Agent 9. Agent 9 runs the backtest and reports how
it did; this agent assumes that result is *suspect* and looks for the ways a
good-looking backtest can still be wrong. In a real institution these are
separate teams on purpose — the people who built the model shouldn't be its
only graders.

Three failure modes it checks, each chosen because a single aggregate Sharpe
ratio hides it completely:

1. DECAY — an edge that worked in 2018 and died in 2020 produces the same
   headline Sharpe as one that worked steadily throughout. Splitting into
   sub-periods separates them.
2. REGIME BLINDNESS — a strategy validated only in expansions tells you
   nothing about how it behaves in a contraction. Agent 6 labels every
   historical date with a regime, so coverage is directly checkable: which
   regimes did this strategy never actually trade through?
3. RETURN CONCENTRATION — if removing the best 5 days turns the result
   negative, the "edge" is a handful of lucky days, not a repeatable process.
   This is the check that most often reframes a promising backtest.

None of these require an LLM or any external service: they are arithmetic on
the return series Agent 9 already produces.
"""

import logging

import numpy as np
import pandas as pd

from agents.macro.schemas import MacroRegime

from .schemas import (
    ModelRiskFinding,
    ModelRiskReport,
    RegimePerformance,
    SubPeriodPerformance,
)

logger = logging.getLogger(__name__)

TRADING_DAYS = 252


def _sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(TRADING_DAYS))


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns.dropna()).cumprod()
    return float(((equity - equity.cummax()) / equity.cummax()).min())


class ModelRiskValidator:
    def __init__(self, n_sub_periods: int = 3, null_simulations: int = 500, seed: int = 42):
        self.n_sub_periods = n_sub_periods
        self.null_simulations = null_simulations
        self.seed = seed

    def _null_top5_share(self, returns: pd.Series) -> float:
        """95th percentile of the top-5-days share for random series of
        comparable scale — the bar real concentration must clear.

        Uses a ROBUST volatility estimate (MAD-based), not the sample standard
        deviation. Using the sample std poisons the null with the very outliers
        being tested for: a handful of huge days inflates sigma, the simulated
        null inherits that inflated sigma, and it then "expects" extreme days —
        so genuine concentration passes unflagged. (Verified: a planted series
        with 99.7% of returns in 5 days went undetected under sample-std, and
        is caught under MAD.) The 1.4826 factor makes MAD a consistent
        estimator of sigma for normal data, so the null is unchanged for clean
        series.

        Seeded so a verdict is reproducible: an unstable "is this model
        trustworthy" answer would be worse than none.
        """
        r = returns.dropna()
        n = len(r)
        if n < 10:
            return float("nan")
        med = float(r.median())
        mad = float((r - med).abs().median())
        sigma = 1.4826 * mad
        if sigma <= 0:
            sigma = float(r.std(ddof=1))  # degenerate case: >50% identical values
        if sigma <= 0:
            return float("nan")

        rng = np.random.default_rng(self.seed)
        shares = []
        for _ in range(self.null_simulations):
            sim = rng.normal(med, sigma, n)
            gross = np.abs(sim).sum()
            if gross == 0:
                continue
            shares.append(np.sort(sim)[-5:].sum() / gross)
        return float(np.percentile(shares, 95)) if shares else float("nan")

    def validate(
        self,
        daily_returns: pd.Series,
        regime_by_date: dict[pd.Timestamp, str] | None = None,
    ) -> ModelRiskReport:
        r = daily_returns.dropna()
        if len(r) < self.n_sub_periods * 2:
            raise ValueError(f"Need at least {self.n_sub_periods * 2} observations to validate.")

        findings: list[ModelRiskFinding] = []
        headline = _sharpe(r)

        # --- 1. Decay across sub-periods -----------------------------------
        chunks = np.array_split(np.arange(len(r)), self.n_sub_periods)
        sub_periods = []
        for i, idx in enumerate(chunks, start=1):
            seg = r.iloc[idx]
            sub_periods.append(
                SubPeriodPerformance(
                    label=f"P{i}",
                    start=str(seg.index[0].date()),
                    end=str(seg.index[-1].date()),
                    n_days=len(seg),
                    total_return=float((1 + seg).prod() - 1),
                    annualized_sharpe=_sharpe(seg),
                    max_drawdown=_max_drawdown(seg),
                )
            )
        sharpes = [sp.annualized_sharpe for sp in sub_periods]
        dispersion = float(np.std(sharpes, ddof=1)) if len(sharpes) > 1 else 0.0

        # A Sharpe estimated from a short window is extremely noisy: its
        # standard error is ~sqrt(TRADING_DAYS / n). With ~100 days per
        # sub-period that is ~1.6, so sub-period Sharpes routinely differ by
        # several points on a perfectly stable strategy. Comparing dispersion
        # to the headline Sharpe (the obvious-looking test) therefore flags
        # almost everything -- it condemned a clean random series in testing.
        # Flag only when dispersion clearly exceeds what sampling noise alone
        # explains.
        avg_n = float(np.mean([sp.n_days for sp in sub_periods]))
        expected_noise = float(np.sqrt(TRADING_DAYS / avg_n)) if avg_n > 0 else 0.0
        if dispersion > 2.0 * expected_noise and expected_noise > 0:
            findings.append(ModelRiskFinding(
                severity="critical",
                category="decay",
                finding=(
                    f"Sub-period Sharpes vary far more than sampling noise explains "
                    f"(dispersion {dispersion:.2f} vs ~{expected_noise:.2f} expected from "
                    f"{avg_n:.0f}-day windows). The aggregate number is not describing a "
                    f"stable edge."
                ),
            ))
        if len(sharpes) >= 2 and sharpes[0] > 0 > sharpes[-1]:
            findings.append(ModelRiskFinding(
                severity="critical",
                category="decay",
                finding=(
                    f"Performance flipped from positive ({sharpes[0]:.2f}) in the first period to "
                    f"negative ({sharpes[-1]:.2f}) in the last — consistent with an edge that has "
                    f"decayed rather than one that persists."
                ),
            ))

        # --- 2. Regime coverage --------------------------------------------
        regime_perf: list[RegimePerformance] = []
        never_tested: list[str] = []
        if regime_by_date:
            labels = pd.Series(
                {d: regime_by_date.get(d) for d in r.index}, index=r.index, dtype="object"
            ).ffill()
            for regime, seg in r.groupby(labels):
                if not regime:
                    continue
                regime_perf.append(RegimePerformance(
                    regime=str(regime),
                    n_days=len(seg),
                    total_return=float((1 + seg).prod() - 1),
                    annualized_sharpe=_sharpe(seg),
                ))
            seen = {rp.regime for rp in regime_perf}
            never_tested = sorted({m.value for m in MacroRegime} - seen)
            if never_tested:
                findings.append(ModelRiskFinding(
                    severity="warning",
                    category="regime_blindness",
                    finding=(
                        f"Never traded through: {', '.join(never_tested)}. Behaviour in "
                        f"{'these regimes is' if len(never_tested) > 1 else 'this regime is'} "
                        f"unknown, not validated — the backtest cannot speak to it."
                    ),
                ))
            thin = [rp for rp in regime_perf if rp.n_days < 30]
            if thin:
                findings.append(ModelRiskFinding(
                    severity="warning",
                    category="regime_blindness",
                    finding=(
                        "Thin regime coverage: "
                        + "; ".join(f"{rp.regime} only {rp.n_days} days" for rp in thin)
                        + ". Too few observations to conclude anything about these."
                    ),
                ))

        # --- 3. Return concentration ---------------------------------------
        top5 = r.nlargest(5)
        total_return = float((1 + r).prod() - 1)
        without_top5 = float((1 + r.drop(top5.index)).prod() - 1)
        # Denominator is TOTAL ABSOLUTE MOVEMENT, not net return. Net return
        # approaches zero for a near-driftless series, which makes the ratio
        # explode (a null calibration returned 516% before this fix) and can
        # even flip its sign. Gross movement is always positive, so the share
        # stays bounded and comparable across strategies.
        gross_movement = float(r.abs().sum())
        top5_share = float(top5.sum() / gross_movement) if gross_movement > 0 else float("nan")

        # "Miss the 5 best days and your return vanishes" is TRUE of almost any
        # positive-drift series -- it is a well-known misleading statistic, not
        # evidence of luck. Testing it directly reproduces the fallacy (it fired
        # on a clean random series in testing). Instead compare against a null:
        # simulate series with the SAME mean and volatility and ask whether this
        # one's concentration is genuinely unusual.
        null_share = self._null_top5_share(r)
        # Severity is WARNING, not critical, and deliberately so. The null is
        # Gaussian, but real financial returns are fat-tailed -- this project
        # measured this very strategy's kurtosis at 11.36 against a normal
        # distribution's 3.0. Concentration therefore exceeds a Gaussian null
        # for almost every real strategy, so treating that as damning would
        # condemn everything and carry no information. It is reported as a
        # characteristic to be aware of, not a verdict.
        if np.isfinite(top5_share) and np.isfinite(null_share) and top5_share > null_share:
            findings.append(ModelRiskFinding(
                severity="warning",
                category="concentration",
                finding=(
                    f"The 5 best days carry {top5_share:.0%} of total absolute movement, "
                    f"beyond the {null_share:.0%} that comparable random series reach 95% of the "
                    f"time. Note the null is Gaussian while real returns are fat-tailed, so "
                    f"some exceedance is expected -- treat as a characteristic, not a defect."
                ),
            ))

        if total_return > 0 and without_top5 <= 0:
            findings.append(ModelRiskFinding(
                severity="info",
                category="concentration",
                finding=(
                    f"For context (not itself a red flag): removing the 5 best days moves the "
                    f"result from {total_return:+.2%} to {without_top5:+.2%}. This is true of most "
                    f"positive-return series and is reported to pre-empt the misreading, not to "
                    f"support it."
                ),
            ))

        if not findings:
            findings.append(ModelRiskFinding(
                severity="info",
                category="none",
                finding="No decay, regime-coverage, or concentration problems detected.",
            ))

        criticals = sum(1 for f in findings if f.severity == "critical")
        warnings_ = sum(1 for f in findings if f.severity == "warning")
        if criticals:
            verdict = (
                f"NOT TRUSTWORTHY — {criticals} critical finding(s). The backtest result should not "
                f"be treated as evidence of a repeatable edge."
            )
        elif warnings_:
            verdict = (
                f"QUALIFIED — {warnings_} warning(s). Usable, but its claims do not extend beyond "
                f"the conditions actually tested."
            )
        else:
            verdict = "NO OBJECTION — none of the tested failure modes are present."

        return ModelRiskReport(
            as_of=str(r.index[-1].date()),
            n_observations=len(r),
            headline_sharpe=headline,
            sub_periods=sub_periods,
            sharpe_dispersion=dispersion,
            regime_performance=sorted(regime_perf, key=lambda x: x.n_days, reverse=True),
            regimes_never_tested=never_tested,
            top_5_days_pct_of_return=top5_share,
            return_without_top_5_days=without_top5,
            findings=findings,
            verdict=verdict,
        )

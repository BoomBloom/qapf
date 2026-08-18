"""Agent 11 — Execution & Market Microstructure.

Turns Agent 2's target weights into an order schedule and estimates what
reaching those targets actually costs. Without this, every performance number
in the system silently assumes trades fill instantly at the close with zero
market impact — the single most flattering assumption a backtest can make.

COST MODEL. Two components, deliberately kept separate because they behave
differently:

1. SPREAD — half the bid/ask spread, paid on every trade regardless of size.
   Modelled as a fixed per-name rate, since real quote data isn't available
   here (Qlib's bundled dataset is daily OHLCV, no book).

2. MARKET IMPACT — the square-root law: impact ~ sigma * sqrt(Q / V), where Q
   is order size, V is daily volume, and sigma is daily volatility. This is the
   standard empirical model (Almgren et al.), and its key property is that
   impact grows with the SQUARE ROOT of size, not linearly: doubling an order
   less than doubles its impact, which is why splitting a large order across
   time reduces total cost at all. A linear model would make scheduling
   pointless, so the shape matters more than the constant.

The impact coefficient is a documented assumption, not a fitted value — real
calibration needs execution data this project does not have. It is surfaced in
the output rather than buried.
"""

import logging

import numpy as np
import pandas as pd

from agents.portfolio.schemas import PortfolioAllocation

from .schemas import ExecutionPlan, ExecutionSlice, Order

logger = logging.getLogger(__name__)

# Half-spread in basis points. Large-cap US equities sit around 1-2bp; this is
# a stated assumption, not a measurement.
HALF_SPREAD_BPS = 1.5

# Square-root-law coefficient. Empirical estimates cluster around 0.5-1.0;
# 0.6 is a mid-range choice. Documented as an assumption -- calibrating it
# properly requires real fill data.
IMPACT_COEFFICIENT = 0.6

# The trading day, in 5-minute buckets (6.5 hours). This matters more than it
# looks: participation rate must be measured against the volume available in
# the WINDOW an order actually trades through, not the whole day. Without it,
# splitting an order into N slices divides both the shares and the volume by N,
# leaving participation -- and therefore impact -- exactly unchanged, so
# scheduling would save nothing. (That was a real bug here: TWAP and immediate
# came out identical to the basis point.) Immediate execution consumes one
# bucket of liquidity; a scheduled order spreads across the whole session.
BUCKETS_PER_DAY = 78


class ExecutionPlanner:
    def __init__(
        self,
        algo: str = "twap",
        n_slices: int = 6,
        half_spread_bps: float = HALF_SPREAD_BPS,
        impact_coefficient: float = IMPACT_COEFFICIENT,
    ):
        if algo not in ("twap", "vwap", "immediate"):
            raise ValueError(f"unknown algo {algo!r}")
        self.algo = algo
        self.n_slices = n_slices
        self.half_spread_bps = half_spread_bps
        self.impact_coefficient = impact_coefficient

    def _slice_weights(self, volume_profile: np.ndarray | None) -> np.ndarray:
        """How the parent order is split across the day.

        TWAP spreads evenly over time. VWAP follows the volume profile, trading
        more when the market is more liquid — which lowers participation rate
        (and therefore impact) at every point. `immediate` is the no-scheduling
        baseline used to demonstrate what scheduling actually saves.
        """
        if self.algo == "immediate":
            return np.array([1.0])
        if self.algo == "twap" or volume_profile is None:
            return np.full(self.n_slices, 1.0 / self.n_slices)
        prof = np.asarray(volume_profile, dtype=float)
        return prof / prof.sum()

    def plan(
        self,
        allocation: PortfolioAllocation,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        portfolio_value: float,
        current_weights: dict[str, float] | None = None,
    ) -> ExecutionPlan:
        current = current_weights or {}
        reasoning: list[str] = []
        as_of = allocation.as_of

        latest_prices = prices.iloc[-1]
        # 20-day average volume: a single day's volume is too noisy to size
        # against, and one unusual session would distort every estimate.
        avg_volume = volumes.iloc[-20:].mean()
        daily_vol = prices.pct_change().iloc[-60:].std()

        targets = {p.ticker: p.weight for p in allocation.positions}
        universe = sorted(set(targets) | set(current))

        orders: list[Order] = []
        for ticker in universe:
            tgt = targets.get(ticker, 0.0)
            cur = current.get(ticker, 0.0)
            delta = tgt - cur
            if abs(delta) < 1e-6 or ticker not in latest_prices.index:
                continue
            px = float(latest_prices[ticker])
            if not np.isfinite(px) or px <= 0:
                continue
            notional = abs(delta) * portfolio_value
            orders.append(Order(
                ticker=ticker,
                side="buy" if delta > 0 else "sell",
                target_weight=tgt,
                current_weight=cur,
                delta_weight=delta,
                notional=notional,
                shares=notional / px,
                reference_price=px,
            ))

        if not orders:
            reasoning.append("No orders — the portfolio already matches its targets.")
            return ExecutionPlan(
                as_of=as_of, algo=self.algo, n_orders=0, gross_notional=0.0, turnover=0.0,
                total_spread_cost=0.0, total_impact_cost=0.0, total_cost=0.0, cost_bps=0.0,
                orders=[], slices=[], reasoning=reasoning,
            )

        # A realistic intraday U-shape: heavy at the open and close, light at
        # midday. VWAP exploits this; TWAP ignores it. Using a real-shaped
        # profile rather than a flat one is what makes the two algos differ.
        u_shape = np.array([0.25, 0.15, 0.10, 0.10, 0.15, 0.25])
        profile = u_shape[: self.n_slices] if self.algo == "vwap" else None
        weights = self._slice_weights(profile)

        slices: list[ExecutionSlice] = []
        total_spread = total_impact = 0.0
        for order in orders:
            v_daily = float(avg_volume.get(order.ticker, np.nan))
            sigma = float(daily_vol.get(order.ticker, np.nan))
            if not np.isfinite(v_daily) or v_daily <= 0 or not np.isfinite(sigma):
                reasoning.append(f"{order.ticker}: no volume/volatility data — cost not estimated.")
                continue

            # Buckets of liquidity each child order trades through. An
            # immediate order takes one bucket; a scheduled order divides the
            # session between its slices.
            buckets_per_slice = (
                1.0 if self.algo == "immediate" else BUCKETS_PER_DAY / len(weights)
            )
            for i, w in enumerate(weights):
                child_shares = order.shares * float(w)
                interval_volume = v_daily * (buckets_per_slice / BUCKETS_PER_DAY)
                participation = child_shares / interval_volume if interval_volume > 0 else 0.0

                child_notional = child_shares * order.reference_price
                spread_cost = child_notional * self.half_spread_bps / 1e4
                # Square-root law: impact per unit traded scales with
                # sqrt(participation), so the cost of this slice is
                # notional * coef * sigma * sqrt(participation).
                impact_cost = (
                    child_notional * self.impact_coefficient * sigma * np.sqrt(max(participation, 0.0))
                )
                total_spread += spread_cost
                total_impact += impact_cost
                slices.append(ExecutionSlice(
                    ticker=order.ticker,
                    slice_index=i + 1,
                    n_slices=len(weights),
                    shares=child_shares,
                    participation_rate=participation,
                    spread_cost=spread_cost,
                    impact_cost=impact_cost,
                    total_cost=spread_cost + impact_cost,
                ))

        gross = float(sum(o.notional for o in orders))
        total = total_spread + total_impact
        reasoning.append(
            f"{self.algo.upper()} across {len(weights)} slice(s); impact via square-root law "
            f"(coef {self.impact_coefficient}), half-spread {self.half_spread_bps}bp — both stated "
            f"assumptions, not calibrated from fills."
        )

        return ExecutionPlan(
            as_of=as_of,
            algo=self.algo,
            n_orders=len(orders),
            gross_notional=gross,
            turnover=gross / portfolio_value if portfolio_value > 0 else 0.0,
            total_spread_cost=total_spread,
            total_impact_cost=total_impact,
            total_cost=total,
            cost_bps=(total / gross * 1e4) if gross > 0 else 0.0,
            orders=sorted(orders, key=lambda o: o.notional, reverse=True),
            slices=slices,
            reasoning=reasoning,
        )

"""Agent 13 — Compliance & Regulatory Surveillance.

Watches conduct, not capital. The CRO (Agent 10) asks "is our capital-at-risk
within limits?"; this asks "did our trading behave in a way that would be a
problem if someone audited it?" — and keeps its own audit trail, separate from
the CRO's risk log, so "was a rule broken" and "was risk too high" stay
independently answerable.

Worth building even for a single-operator paper system, for a reason beyond
regulation: the patterns it looks for are also BUG SIGNATURES. A signal that
oscillates every rebalance produces exactly the same footprint as wash trading;
a position quietly creeping past its cap looks the same whether it came from
misconduct or a broken constraint. So this doubles as a detector for the kind
of silent logic error this project keeps finding.
"""

import logging
from collections import defaultdict

import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComplianceAlert(BaseModel):
    severity: str = Field(description="'violation' | 'warning' | 'info'")
    rule: str
    ticker: str | None = None
    detail: str


class ComplianceReport(BaseModel):
    as_of: str
    orders_reviewed: int
    rules_checked: list[str]
    alerts: list[ComplianceAlert]
    violations: int
    warnings: int
    clean: bool
    audit_trail: list[str]


class ComplianceSurveillance:
    def __init__(
        self,
        max_position_pct: float = 0.35,
        max_sector_pct: float = 0.60,
        restricted_list: set[str] | None = None,
        wash_window_days: int = 5,
    ):
        self.max_position_pct = max_position_pct
        self.max_sector_pct = max_sector_pct
        self.restricted_list = restricted_list or set()
        self.wash_window_days = wash_window_days

    def review(
        self,
        order_history: pd.DataFrame,
        current_weights: dict[str, float],
        sectors: dict[str, str] | None = None,
        as_of: str | None = None,
    ) -> ComplianceReport:
        """`order_history` needs columns: date, ticker, side, notional."""
        alerts: list[ComplianceAlert] = []
        audit: list[str] = []
        as_of = as_of or str(pd.Timestamp.today().date())
        rules = ["restricted_list", "position_limit", "sector_concentration", "wash_trading"]

        # --- Restricted list -------------------------------------------------
        for ticker in sorted(set(order_history["ticker"]) if len(order_history) else set()):
            if ticker in self.restricted_list:
                alerts.append(ComplianceAlert(
                    severity="violation", rule="restricted_list", ticker=ticker,
                    detail=f"{ticker} is on the restricted list but was traded.",
                ))
        audit.append(f"Screened {len(order_history)} order(s) against "
                     f"{len(self.restricted_list)} restricted name(s).")

        # --- Position limits -------------------------------------------------
        for ticker, w in sorted(current_weights.items()):
            if w > self.max_position_pct + 1e-9:
                alerts.append(ComplianceAlert(
                    severity="violation", rule="position_limit", ticker=ticker,
                    detail=f"{ticker} at {w:.2%} exceeds the {self.max_position_pct:.0%} "
                           f"single-name limit.",
                ))
        audit.append(f"Checked {len(current_weights)} position(s) against a "
                     f"{self.max_position_pct:.0%} single-name limit.")

        # --- Sector concentration -------------------------------------------
        if sectors:
            by_sector: dict[str, float] = defaultdict(float)
            for ticker, w in current_weights.items():
                by_sector[sectors.get(ticker, "unknown")] += w
            for sector, w in sorted(by_sector.items()):
                if w > self.max_sector_pct + 1e-9:
                    alerts.append(ComplianceAlert(
                        severity="warning", rule="sector_concentration",
                        detail=f"Sector '{sector}' at {w:.2%} exceeds the "
                               f"{self.max_sector_pct:.0%} guideline.",
                    ))
            audit.append(f"Aggregated exposure across {len(by_sector)} sector(s).")

        # --- Wash-trading-shaped patterns ------------------------------------
        # Buying and selling the same name inside a short window is the classic
        # wash signature. Here it is at least as likely to mean a signal
        # flip-flopping between rebalances -- a strategy bug -- which is why
        # this is reported rather than assumed benign.
        if len(order_history):
            hist = order_history.copy()
            hist["date"] = pd.to_datetime(hist["date"])
            for ticker, grp in hist.groupby("ticker"):
                grp = grp.sort_values("date")
                for i in range(len(grp) - 1):
                    a, b = grp.iloc[i], grp.iloc[i + 1]
                    gap = (b["date"] - a["date"]).days
                    if a["side"] != b["side"] and gap <= self.wash_window_days:
                        alerts.append(ComplianceAlert(
                            severity="warning", rule="wash_trading", ticker=str(ticker),
                            detail=(
                                f"{ticker}: {a['side']} then {b['side']} within {gap}d "
                                f"(${min(a['notional'], b['notional']):,.0f} offsetting). Wash-shaped "
                                f"— check whether the signal is oscillating."
                            ),
                        ))
                        break  # one alert per name is enough to prompt a look
            audit.append(f"Scanned for offsetting trades within {self.wash_window_days}d.")

        violations = sum(1 for a in alerts if a.severity == "violation")
        warnings_ = sum(1 for a in alerts if a.severity == "warning")

        return ComplianceReport(
            as_of=as_of,
            orders_reviewed=len(order_history),
            rules_checked=rules,
            alerts=alerts,
            violations=violations,
            warnings=warnings_,
            clean=violations == 0 and warnings_ == 0,
            audit_trail=audit,
        )

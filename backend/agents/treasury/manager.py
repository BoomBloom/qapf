"""Agent 16 — Treasury & Funding.

Deliberately narrow, matching README's own scoping note: "distinct from the
Portfolio Manager, which allocates strategy capital, not manages the
cash/broker relationship... lower priority for a single-operator system
without multiple prime broker relationships." Built last because two of its
three original pillars genuinely don't apply yet to what QAPF actually is
today:

- CASH YIELD: real and buildable now. Every other agent's account-value math
  (Agent 2's cash_weight, Agent 12's reconciliation) treats idle cash as
  earning nothing. A real broker doesn't work that way, and the gap compounds
  over a multi-month paper/live stage.
- MARGIN: real and buildable now, but currently UNUSED by design. Agent 2 is
  long-only/cash-account by deliberate decision (allocator.py's docstring:
  "Qlib's optimizer hard-codes no-shorting; margin/borrow are unmodeled").
  This module builds the REG-T calculator as real infrastructure for
  whenever that changes, not as something QAPF calls today.
- CURRENCY HEDGING: NOT built. QAPF trades USD-denominated US cash equities
  only, in a single-currency broker relationship -- there is no FX exposure
  to hedge. Building a hedging function with no real exposure to hedge would
  be exactly the "no placeholder data" violation CLAUDE.md warns against.
  This is an explicit seam (same pattern Agent 6 used for its unbuilt NLP
  scoring), not a stub: `hedge_fx_exposure` deliberately does not exist here.
  Add it only when/if QAPF trades a non-USD instrument for real.

CASH-INTEREST TIER SOURCE: Interactive Brokers' published USD cash rate,
verified via live web search 2026-08-19 (interactivebrokers.com's own
pricing page returned HTTP 403 to a direct fetch, same as earlier in this
project's research) -- accounts with NAV >= $100,000 earn the full published
rate on USD cash above a $10,000 threshold; accounts below $100,000 NAV earn
a pro-rated fraction of that rate (NAV / $100,000). These threshold figures
($10k, $100k) are IBKR's structural design (blended-tier interest, the same
shape as its margin tiers) and change rarely; the RATE percentage itself
changes with the Fed funds benchmark and should be re-verified against
IBKR's current published rate before being trusted for a real funding
decision, not assumed to still be 3.13% by the time this runs.
"""

from .schemas import CashYieldAssessment, MarginRequirement

# Verified live via web search 2026-08-19, IBKR's own pricing page (direct
# fetch blocked, HTTP 403 -- same limitation this project's earlier broker
# research hit). Re-verify before relying on this for a real cash-yield
# decision; it moves with the Fed funds benchmark, unlike the $10k/$100k
# tier thresholds below, which are IBKR's structural design.
IBKR_CASH_TIER_RATE_APY = 0.0313
IBKR_CASH_UNCOMPENSATED_THRESHOLD = 10_000.0
IBKR_CASH_TOP_TIER_NAV = 100_000.0

REG_T_INITIAL_MARGIN_PCT = 0.50
FINRA_MAINTENANCE_MARGIN_PCT = 0.25


class TreasuryManager:
    def assess_cash_yield(
        self,
        nav: float,
        cash_balance: float,
        tier_rate_apy: float = IBKR_CASH_TIER_RATE_APY,
        uncompensated_threshold: float = IBKR_CASH_UNCOMPENSATED_THRESHOLD,
        top_tier_nav: float = IBKR_CASH_TOP_TIER_NAV,
    ) -> CashYieldAssessment:
        reasoning: list[str] = []
        compensated = max(0.0, cash_balance - uncompensated_threshold)
        if compensated == 0.0:
            reasoning.append(
                f"Cash balance ${cash_balance:,.2f} is at or below the ${uncompensated_threshold:,.0f} "
                f"uncompensated threshold -- earns $0, same as holding it at any broker."
            )

        proration = min(1.0, nav / top_tier_nav) if top_tier_nav > 0 else 1.0
        if proration < 1.0:
            reasoning.append(
                f"NAV ${nav:,.2f} is below the ${top_tier_nav:,.0f} top-tier threshold -- earns "
                f"{proration:.1%} of the full {tier_rate_apy:.2%} published rate, not the full rate. "
                f"At QAPF's real $1,000 stage-3 account size (wayfinder ticket 01), this proration is "
                f"the dominant effect, not the headline rate."
            )

        effective_apy = tier_rate_apy * proration
        annual_interest = compensated * effective_apy
        daily_interest = annual_interest / 365.0

        reasoning.append(
            f"${compensated:,.2f} compensated at {effective_apy:.4%} effective APY "
            f"= ${annual_interest:,.2f}/year (${daily_interest:,.4f}/day)."
        )

        return CashYieldAssessment(
            nav=nav, cash_balance=cash_balance,
            uncompensated_threshold=uncompensated_threshold, compensated_balance=compensated,
            tier_rate_apy=tier_rate_apy, proration_factor=proration, effective_apy=effective_apy,
            annual_interest=annual_interest, daily_interest=daily_interest,
            reasoning=reasoning,
        )

    def assess_margin_requirement(self, gross_position_value: float, nav: float) -> MarginRequirement:
        """Reg T (50% initial) and FINRA (25% maintenance) are federal/SRO
        minimums, not IBKR-specific -- real numbers a broker's house margin
        requirement can only be stricter than, never looser. `nav` is the
        account's real net liquidation value, checked against the
        maintenance requirement to determine margin-call status."""
        reasoning: list[str] = []
        initial = gross_position_value * REG_T_INITIAL_MARGIN_PCT
        maintenance = gross_position_value * FINRA_MAINTENANCE_MARGIN_PCT
        excess = nav - maintenance
        call = excess < 0

        reasoning.append(
            f"${gross_position_value:,.2f} gross long equity -> Reg T initial margin "
            f"${initial:,.2f} (50%), FINRA maintenance ${maintenance:,.2f} (25%)."
        )
        if call:
            reasoning.append(
                f"MARGIN CALL: NAV ${nav:,.2f} is ${abs(excess):,.2f} below the maintenance requirement."
            )
        else:
            reasoning.append(f"NAV ${nav:,.2f} clears maintenance by ${excess:,.2f} -- no call.")
        reasoning.append(
            "Not currently applicable to QAPF's own trading: Agent 2 (Portfolio Manager) is "
            "long-only/cash-account by deliberate decision, so gross_position_value should never "
            "exceed nav in practice today. This exists as real infrastructure for if/when that "
            "changes, not as something the live pipeline calls now."
        )

        return MarginRequirement(
            gross_position_value=gross_position_value,
            initial_margin_required=initial, maintenance_margin_required=maintenance,
            excess_liquidity=excess, margin_call=call, reasoning=reasoning,
        )

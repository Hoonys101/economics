from __future__ import annotations
from typing import Optional
from modules.finance.monetary.api import (
    IMonetaryStrategy, MonetaryRuleType, MacroEconomicSnapshotDTO,
    MonetaryPolicyConfigDTO, MonetaryDecisionDTO, OMOActionType
)

class TaylorRuleStrategy:
    """
    Implements the Taylor Rule for interest rate targeting.
    i = r* + pi + alpha(pi - pi*) + beta(y)
    """
    @property
    def rule_type(self) -> MonetaryRuleType:
        return MonetaryRuleType.TAYLOR_RULE

    def calculate_decision(
        self,
        snapshot: MacroEconomicSnapshotDTO,
        current_rate: float,
        config: MonetaryPolicyConfigDTO
    ) -> MonetaryDecisionDTO:

        inflation_rate = snapshot.inflation_rate_annual

        # Determine Output Gap
        # Priority 1: Provided explicit output gap (Legacy compatibility)
        # Priority 2: Okun's Law (Unemployment Gap)
        if snapshot.output_gap is not None:
            output_gap = snapshot.output_gap
        else:
            # Okun's Law: Gap ~ -2 * (u - u*)
            # Note: If u > u* (high unemployment), Gap is negative (recession).
            # We assume a coefficient of 2.0 implicitly or just use the raw gap.
            # Standard Taylor Rule uses log output gap.
            # Here we substitute y with (u* - u).
            # If u=5%, u*=5%, gap=0. If u=6%, gap=-1%.
            output_gap = (config.unemployment_target - snapshot.unemployment_rate)

        # Taylor Rule Calculation
        # i = r* + pi + alpha * (pi - pi*) + beta * output_gap

        target_rate = (
            config.neutral_rate +
            inflation_rate +
            config.taylor_alpha * (inflation_rate - config.inflation_target) +
            config.taylor_beta * output_gap
        )

        # Apply Zero Lower Bound (ZLB) and Max Rate
        target_rate = max(config.min_interest_rate, min(config.max_interest_rate, target_rate))

        # Smoothing (Optional, but good for stability)
        # We don't implement smoothing here strictly, but usually CBs smooth changes.
        # The legacy engine implemented smoothing (max change 0.25%).
        # We will return the raw target and let the Agent apply smoothing if desired,
        # OR we can apply it here if we had 'current_rate'.
        # We DO have current_rate.

        max_change = 0.0025 # 25 bps
        delta = target_rate - current_rate
        if abs(delta) > max_change:
            target_rate = current_rate + (max_change * (1.0 if delta > 0 else -1.0))

        return MonetaryDecisionDTO(
            rule_type=self.rule_type,
            tick=snapshot.tick,
            target_interest_rate=target_rate,
            omo_action=OMOActionType.NONE,
            reasoning=f"Taylor Rule: Infl={inflation_rate:.2%}, Gap={output_gap:.2%}, Target={target_rate:.2%}"
        )


class FriedmanKPercentStrategy:
    """
    Implements Friedman's k-percent rule.
    Targets a fixed growth rate of Money Supply (M2).
    """
    @property
    def rule_type(self) -> MonetaryRuleType:
        return MonetaryRuleType.FRIEDMAN_K_PERCENT

    def calculate_decision(
        self,
        snapshot: MacroEconomicSnapshotDTO,
        current_rate: float,
        config: MonetaryPolicyConfigDTO
    ) -> MonetaryDecisionDTO:

        # 1. Calculate Target M2
        # Target = Current * (1 + k_period)
        # k is annual, need to adjust for period?
        # Assuming config.m2_growth_target is Annual.
        # And update interval is... unknown here.
        # Assuming the target provided in config is relevant for the update frequency
        # or we accept base drift.
        # Let's assume config.m2_growth_target is the target growth for the PERIOD (e.g. 1 tick or 1 update cycle).
        # OR, more safely, treat it as annual and scale it?
        # The Spec says: "M2_target = M2_prev * (1 + k)".
        # We will use the configured target directly.

        # Note: Ideally we should track the *Path* to avoid Base Drift, but for V1 we target next step.
        target_m2 = int(snapshot.current_m2_supply * (1.0 + config.m2_growth_target))

        delta = target_m2 - snapshot.current_m2_supply

        action = OMOActionType.NONE
        amount = 0

        if delta > 0:
            action = OMOActionType.BUY_BONDS
            amount = delta
        elif delta < 0:
            action = OMOActionType.SELL_BONDS
            amount = abs(delta)

        return MonetaryDecisionDTO(
            rule_type=self.rule_type,
            tick=snapshot.tick,
            target_interest_rate=current_rate, # No change to rates, quantity led
            target_m2_supply=target_m2,
            omo_action=action,
            omo_amount_pennies=amount,
            reasoning=f"Friedman k%: Current M2={snapshot.current_m2_supply}, Target={target_m2}, Delta={delta}"
        )


class McCallumRuleStrategy:
    """
    Implements McCallum Rule.
    Targets Monetary Base (M0) to stabilize Nominal GDP.
    """
    @property
    def rule_type(self) -> MonetaryRuleType:
        return MonetaryRuleType.MCCALLUM_RULE

    def calculate_decision(
        self,
        snapshot: MacroEconomicSnapshotDTO,
        current_rate: float,
        config: MonetaryPolicyConfigDTO
    ) -> MonetaryDecisionDTO:

        # Simplified McCallum: Target MB growth to match Target NGDP growth, adjusted for Velocity.
        # Target MB = Current MB * (1 + Target NGDP Growth)
        # We assume Velocity is constant for V1 (or implicitly captured).

        target_mb = int(snapshot.current_monetary_base * (1.0 + config.ngdp_target_growth))

        delta = target_mb - snapshot.current_monetary_base

        action = OMOActionType.NONE
        amount = 0

        if delta > 0:
            action = OMOActionType.BUY_BONDS
            amount = delta
        elif delta < 0:
            action = OMOActionType.SELL_BONDS
            amount = abs(delta)

        return MonetaryDecisionDTO(
            rule_type=self.rule_type,
            tick=snapshot.tick,
            target_interest_rate=current_rate,
            target_monetary_base=target_mb,
            omo_action=action,
            omo_amount_pennies=amount,
            reasoning=f"McCallum Rule: Current MB={snapshot.current_monetary_base}, Target={target_mb}, Delta={delta}"
        )

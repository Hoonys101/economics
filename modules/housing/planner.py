from __future__ import annotations
from typing import Any, List, Optional
import math

from modules.housing.api import (
    IHousingPlanner,
    HouseholdHousingStateDTO,
    HousingMarketStateDTO,
    HousingDecisionDTO,
    HousingActionType,
    RealEstateUnitDTO
)


class HousingPlanner(IHousingPlanner):
    """
    Stateless component that contains all business logic for housing decisions.
    """

    def evaluate_and_decide(
        self,
        household: HouseholdHousingStateDTO,
        market: HousingMarketStateDTO,
        config: Any,
    ) -> HousingDecisionDTO:
        """
        Determines the optimal housing action for a household based on its state and market conditions.
        """

        # --- Priority 1: Homelessness ---
        # The most urgent need is shelter.
        if household.is_homeless:
            # Find the cheapest, minimally acceptable rental unit.
            # Using config.housing.RENT_TO_INCOME_RATIO_MAX as per spec
            max_rent = household.income * config.housing.RENT_TO_INCOME_RATIO_MAX

            affordable_rentals = [
                u for u in market.units_for_rent
                if u.rent_price <= max_rent
            ]

            if affordable_rentals:
                cheapest_rental = min(affordable_rentals, key=lambda u: u.rent_price)
                return HousingDecisionDTO(
                    agent_id=household.id,
                    action=HousingActionType.SEEK_RENTAL,
                    target_unit_id=cheapest_rental.id,
                    justification="Agent is homeless and can afford rent."
                )
            else:
                return HousingDecisionDTO(
                    agent_id=household.id,
                    action=HousingActionType.STAY,
                    justification="Agent is homeless but cannot afford any available rentals."
                )

        # --- Priority 2: Financial Distress (Owner) ---
        # An owner who is financially unstable should liquidate their property.
        if household.owned_property_ids:
            # Assuming an agent owns at most one property for now, as per spec
            owned_property_id = household.owned_property_ids[0]

            # config.housing.FINANCIAL_DISTRESS_ASSET_THRESHOLD_MONTHS
            distress_threshold = household.income * config.housing.FINANCIAL_DISTRESS_ASSET_THRESHOLD_MONTHS

            if household.assets < distress_threshold:
                 return HousingDecisionDTO(
                    agent_id=household.id,
                    action=HousingActionType.SELL_PROPERTY,
                    sell_unit_id=owned_property_id,
                    justification="Agent is in financial distress; liquidating property."
                )

        # --- Priority 3: Desire to Upgrade (Renter to Owner) ---
        # A financially stable renter may want to buy a house.
        # Condition: Is a renter (residing but not owning)
        if household.residing_property_id and not household.owned_property_ids:
            affordable_homes = [
                h for h in market.units_for_sale
                if self._is_purchase_affordable(h, household, config)
            ]

            if affordable_homes:
                best_home = min(affordable_homes, key=lambda h: h.for_sale_price) # Simplistic choice
                return HousingDecisionDTO(
                    agent_id=household.id,
                    action=HousingActionType.SEEK_PURCHASE,
                    target_unit_id=best_home.id,
                    justification="Agent is a renter and can afford to purchase a home."
                )

        # --- Default Action: Stay ---
        # If no other conditions are met, maintain the status quo.
        return HousingDecisionDTO(
            agent_id=household.id,
            action=HousingActionType.STAY,
            justification="No urgent need or opportunity to move."
        )

    def _is_purchase_affordable(
        self,
        home: RealEstateUnitDTO,
        household: HouseholdHousingStateDTO,
        config: Any
    ) -> bool:
        """
        Helper to determine if a home purchase is affordable.
        """
        down_payment = home.for_sale_price * config.finance.MORTGAGE_DOWN_PAYMENT_RATE
        monthly_payment = self._calculate_mortgage_payment(home.for_sale_price, config)

        has_down_payment = household.assets >= down_payment
        can_afford_monthly = monthly_payment < household.income * config.housing.MORTGAGE_TO_INCOME_RATIO_MAX

        return has_down_payment and can_afford_monthly

    def _calculate_mortgage_payment(self, price: float, config: Any) -> float:
        """
        Calculates the estimated monthly mortgage payment.
        Formula: M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1 ]
        """
        # Assuming config has these values or defaulting
        # Using getattr to be safe if config structure varies, but spec implies these exist.
        # However, for pure implementation of spec:

        # Loan Amount = Price - Down Payment
        down_payment_rate = config.finance.MORTGAGE_DOWN_PAYMENT_RATE
        loan_amount = price * (1 - down_payment_rate)

        annual_rate = config.finance.MORTGAGE_INTEREST_RATE
        term_years = config.finance.MORTGAGE_TERM_YEARS

        if annual_rate == 0:
            return loan_amount / (term_years * 12)

        monthly_rate = annual_rate / 12.0
        num_payments = term_years * 12

        numerator = monthly_rate * ((1 + monthly_rate) ** num_payments)
        denominator = ((1 + monthly_rate) ** num_payments) - 1

        if denominator == 0:
             return loan_amount / num_payments # Fallback to avoid div by zero

        return loan_amount * (numerator / denominator)

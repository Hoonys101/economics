from __future__ import annotations
from typing import Any, Union
import logging

from modules.housing.api import IHousingPlanner
from modules.housing.dtos import (
    HousingDecisionRequestDTO,
    HousingDecisionDTO,
    HousingPurchaseDecisionDTO,
    HousingRentalDecisionDTO,
    HousingStayDecisionDTO
)

logger = logging.getLogger(__name__)

class HousingPlanner(IHousingPlanner):
    """
    Stateless component that contains all business logic for housing decisions.
    Centralizes logic for Buying, Renting, and Staying.
    """

    DEFAULT_DOWN_PAYMENT_PCT = 0.20

    def evaluate_housing_options(self, request: HousingDecisionRequestDTO) -> HousingDecisionDTO:
        household = request['household_state']
        market = request['housing_market_snapshot']

        # 1. Evaluate "Buy" Option
        # Use simple affordability metric: Price <= Assets / DownPaymentPct
        max_price = household.assets / self.DEFAULT_DOWN_PAYMENT_PCT

        affordable_properties = []
        if market.for_sale_units:
            for prop in market.for_sale_units:
                if prop.price <= max_price:
                    # Simple Score: Quality / Price (Value for Money)
                    score = prop.quality / prop.price if prop.price > 0 else 0
                    affordable_properties.append((score, prop))

        # Sort by score desc
        affordable_properties.sort(key=lambda x: x[0], reverse=True)
        best_buy_option = affordable_properties[0][1] if affordable_properties else None

        # 2. Evaluate "Rent" Option
        best_rent_option = None
        if market.units_for_rent:
             income = household.current_wage
             max_rent = income * 0.3
             affordable_rentals = [u for u in market.units_for_rent if (u.rent_price or 0) <= max_rent]

             if affordable_rentals:
                 affordable_rentals.sort(key=lambda u: (u.rent_price or 0)) # Cheapest
                 best_rent_option = affordable_rentals[0]

        # 3. Compare and Decide

        # Case A: Homeless - Must act
        if household.is_homeless:
            if best_buy_option:
                return self._create_buy_decision(best_buy_option, household)
            elif best_rent_option:
                return HousingRentalDecisionDTO(
                    decision_type="MAKE_RENTAL_OFFER",
                    target_property_id=self._parse_unit_id(best_rent_option.unit_id)
                )
            else:
                return HousingStayDecisionDTO(decision_type="STAY")

        # Case B: Upgrade / Voluntary Move
        should_buy = False
        if best_buy_option:
            if hasattr(household, 'housing_target_mode') and household.housing_target_mode == "BUY":
                should_buy = True
            elif best_rent_option:
                 # If buy score > rent score?
                 # Just simple check: if we want to buy, we buy.
                 pass

        if should_buy and best_buy_option:
            return self._create_buy_decision(best_buy_option, household)

        # Default: Stay
        return HousingStayDecisionDTO(decision_type="STAY")

    def _create_buy_decision(self, prop: Any, household: Any) -> HousingPurchaseDecisionDTO:
        offer_price = prop.price
        required_down = offer_price * self.DEFAULT_DOWN_PAYMENT_PCT

        # Ensure household has enough for down payment (already checked by max_price but good to be safe)
        if household.assets < required_down:
             # Fallback: Can't afford down payment despite max_price check (maybe floating point or rounding)
             pass

        return HousingPurchaseDecisionDTO(
            decision_type="INITIATE_PURCHASE",
            target_property_id=self._parse_unit_id(prop.unit_id),
            offer_price=offer_price,
            down_payment_amount=required_down
        )

    def _parse_unit_id(self, unit_id_str: str) -> int:
        try:
            return int(unit_id_str.split('_')[1])
        except (IndexError, ValueError):
            try:
                return int(unit_id_str)
            except:
                return 0

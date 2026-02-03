from typing import List, Optional
import math
import logging

from modules.market.housing_planner_api import (
    IHousingPlanner,
    HousingOfferRequestDTO,
    HousingDecisionDTO,
    MortgageApplicationDTO
)
from modules.market.loan_api import MortgageApplicationRequestDTO

logger = logging.getLogger(__name__)

class HousingPlanner(IHousingPlanner):
    """
    Stateless component that contains all business logic for housing decisions.
    Implements IHousingPlanner.
    """

    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        household = request['household_state']
        housing_market = request['housing_market_snapshot']
        loan_market = request['loan_market_snapshot']
        current_debt = request.get('applicant_current_debt', 0.0)
        annual_income = request.get('applicant_annual_income', 0.0)

        MIN_DOWN_PAYMENT_PCT = 0.2 # Standard requirement, ideally from config

        # 1. Assess Market Conditions
        interest_rate = loan_market['interest_rate']
        max_dti = loan_market['max_dti']
        max_ltv = loan_market['max_ltv']

        # 2. Calculate Max Affordable Loan (DTI Constraint)
        monthly_income = annual_income / 12.0

        # Estimate existing debt service (Monthly)
        # Using current market rate for estimation if specific loan details unknown
        monthly_rate = interest_rate / 12.0
        if monthly_rate == 0:
             existing_monthly_payment = current_debt / 360.0
        else:
             existing_monthly_payment = current_debt * monthly_rate

        max_allowed_new_monthly_payment = (monthly_income * max_dti) - existing_monthly_payment

        max_loan_dti = 0.0
        if max_allowed_new_monthly_payment > 0:
            term_months = 360
            if monthly_rate == 0:
                max_loan_dti = max_allowed_new_monthly_payment * term_months
            else:
                max_loan_dti = max_allowed_new_monthly_payment * ( (1+monthly_rate)**term_months - 1 ) / ( monthly_rate * (1+monthly_rate)**term_months )

        # 3. Assess Purchasing Power
        cash = household.econ_state.assets
        purchasing_power = cash + max_loan_dti

        # 4. Filter Properties
        properties = getattr(housing_market, 'for_sale_units', [])
        affordable_properties = []

        for prop in properties:
            price = prop.price

            # Basic Affordability Check
            if price > purchasing_power:
                continue

            # Check Down Payment Constraint (LTV)
            # Max Loan for this property = Price * MaxLTV
            # Required Down Payment = Price - Max Loan
            required_down_payment = price * (1.0 - max_ltv)

            if cash < required_down_payment:
                continue

            # Check if loan amount needed is within DTI limits
            # Loan Needed = Price - Cash (Using all cash)
            # Actually we can retain some cash, but let's see minimal loan needed.
            # Minimal Loan = Price - Cash.
            if (price - cash) > max_loan_dti:
                continue

            affordable_properties.append(prop)

        # 5. Make Decision
        # Priority: Homelessness -> Buy if affordable.
        if household.econ_state.is_homeless and affordable_properties:
            # Pick cheapest for now (simplistic logic)
            best_prop = min(affordable_properties, key=lambda p: p.price)
            offer_price = best_prop.price

            # Determine Down Payment & Loan Amount
            # We want to minimize down payment while satisfying LTV and DTI?
            # Or maximize down payment to minimize debt?
            # Strategy: Pay target down payment (e.g. 20%) if possible, else minimal required.

            target_down = offer_price * MIN_DOWN_PAYMENT_PCT
            required_down_ltv = offer_price * (1.0 - max_ltv)

            actual_down = max(target_down, required_down_ltv)

            if cash < actual_down:
                actual_down = cash # Should not happen given check above, but purely safe
            else:
                # If we have excess cash, maybe use more? For now stick to target/required.
                pass

            loan_amount = offer_price - actual_down

            # Ensure loan amount is within DTI limit
            if loan_amount > max_loan_dti:
                 # Reduce loan amount, increase down payment
                 diff = loan_amount - max_loan_dti
                 actual_down += diff
                 loan_amount = max_loan_dti

                 if actual_down > cash:
                     # Should have been filtered out
                     logger.warning(f"HousingPlanner: Logic error, down payment {actual_down} exceeds cash {cash}")
                     return self._stay_decision()

            try:
                # unit_id might be "unit_123" or just "123"
                prop_id_str = best_prop.unit_id.replace("unit_", "")
                prop_id = int(prop_id_str)
            except ValueError:
                logger.error(f"HousingPlanner: Invalid property ID {best_prop.unit_id}")
                return self._stay_decision()

            mortgage_app = MortgageApplicationRequestDTO(
                applicant_id=household.id,
                requested_principal=loan_amount,
                property_id=prop_id,
                property_value=offer_price,
                applicant_monthly_income=annual_income / 12.0,
                existing_monthly_debt_payments=existing_monthly_payment,
                loan_term=360
            )

            return HousingDecisionDTO(
                decision_type="MAKE_OFFER",
                target_property_id=prop_id,
                offer_price=offer_price,
                mortgage_application=mortgage_app
            )

        # Default: Stay
        return self._stay_decision()

    def _stay_decision(self) -> HousingDecisionDTO:
        return HousingDecisionDTO(
            decision_type="STAY",
            target_property_id=None,
            offer_price=None,
            mortgage_application=None
        )

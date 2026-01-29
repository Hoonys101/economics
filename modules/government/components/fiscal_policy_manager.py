from __future__ import annotations
from typing import Any, List, Optional
import math
from modules.government.dtos import FiscalPolicyDTO, TaxBracketDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.government.api import IFiscalPolicyManager

class FiscalPolicyManager(IFiscalPolicyManager):
    """
    Component responsible for managing fiscal policy, including determining tax brackets
    and calculating tax liabilities.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def determine_fiscal_stance(self, market_snapshot: MarketSnapshotDTO) -> FiscalPolicyDTO:
        """
        Determines the current fiscal policy based on market conditions.
        Calculates absolute tax brackets based on survival cost.
        """
        # 1. Calculate Survival Cost
        # Survival Cost = Basic Food Price * Daily Consumption
        basic_food_price = market_snapshot.prices.get("basic_food", 5.0)
        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
        survival_cost = basic_food_price * daily_consumption

        # Ensure non-zero survival cost to prevent issues
        if survival_cost <= 0:
            survival_cost = 5.0 # Fallback

        # 2. Get Tax Brackets Configuration
        # Format: List of (multiple_of_survival_cost, tax_rate)
        # e.g., [(0.5, 0.0), (1.0, 0.05), (3.0, 0.10), (inf, 0.20)]
        raw_brackets = getattr(self.config_module, "TAX_BRACKETS", [])

        # If no brackets configured, use a default progressive structure
        if not raw_brackets:
            raw_brackets = [
                (1.0, 0.0),    # 0% up to 1x survival
                (3.0, 0.10),   # 10% from 1x to 3x survival
                (float('inf'), 0.20) # 20% above 3x survival
            ]

        # 3. Convert to Absolute TaxBracketDTOs
        progressive_tax_brackets: List[TaxBracketDTO] = []
        previous_ceiling = 0.0

        for multiple, rate in raw_brackets:
            if multiple == float('inf'):
                ceiling = None
            else:
                ceiling = multiple * survival_cost

            bracket = TaxBracketDTO(
                floor=previous_ceiling,
                rate=rate,
                ceiling=ceiling
            )
            progressive_tax_brackets.append(bracket)

            if ceiling is None:
                break # Reached infinity

            previous_ceiling = ceiling

        return FiscalPolicyDTO(
            progressive_tax_brackets=progressive_tax_brackets
        )

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """
        Calculates the tax owed based on a progressive bracket system.
        """
        if income <= 0:
            return 0.0

        total_tax = 0.0

        for bracket in policy.progressive_tax_brackets:
            # Determine the income chunk that falls into this bracket
            bracket_floor = bracket.floor
            bracket_ceiling = bracket.ceiling if bracket.ceiling is not None else float('inf')

            if income <= bracket_floor:
                continue

            taxable_in_bracket = min(income, bracket_ceiling) - bracket_floor

            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate

            if income <= bracket_ceiling:
                break

        return total_tax

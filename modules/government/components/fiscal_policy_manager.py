from __future__ import annotations
from typing import Any, List, Optional
import math
from modules.government.dtos import FiscalPolicyDTO, TaxBracketDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.government.api import IFiscalPolicyManager
from modules.finance.utils.currency_math import round_to_pennies
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE

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
        # MarketSnapshotDTO is now a TypedDict.
        # Prioritize 'market_signals' (new) > 'market_data' (legacy)

        # MIGRATION: Default is now pennies (500), but logic below assumes DOLLARS from Market
        # If fallback is needed, we must be careful.
        # Let's say fallback is 5.0 dollars (legacy constant usage in tests might expect 5.0).
        # We will convert whatever we get to pennies.
        basic_food_price_raw = 5.0

        signals = getattr(market_snapshot, 'market_signals', {})
        if isinstance(signals, dict) and 'basic_food' in signals:
             # Use new signal
             signal = signals['basic_food']
             # MarketSignalDTO keys are attributes, not dict keys if it's a dataclass
             price = getattr(signal, 'best_ask', None)
             if price is None or price <= 0:
                 price = getattr(signal, 'last_traded_price', None)
             if price is not None and price > 0:
                 basic_food_price_raw = float(price)

        else:
             m_data = getattr(market_snapshot, 'market_data', {})
             if isinstance(m_data, dict) and 'goods_market' in m_data:
                 price = m_data['goods_market'].get('basic_food_current_sell_price', 5.0)
                 # Protective check for Mock objects in tests
                 try:
                     basic_food_price_raw = float(price)
                 except (ValueError, TypeError):
                     basic_food_price_raw = 5.0

        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)

        # MIGRATION: Assume market prices are float DOLLARS.
        # Convert to pennies explicitly.
        # If raw_price is small (e.g. 5.0), it becomes 500.
        # If raw_price is huge (e.g. 500.0), it becomes 50000.
        # We removed the heuristic check < 1000.0.

        # Calculate survival cost in pennies
        # survival_cost = (Price in Dollars * 100) * Consumption
        # Note: round_to_pennies expects input in pennies (fractional).
        # Since basic_food_price_raw is in DOLLARS, we multiply by 100.
        survival_cost = round_to_pennies(basic_food_price_raw * 100 * float(daily_consumption))

        # Ensure non-zero survival cost to prevent issues
        if survival_cost <= 0:
            # Fallback to config default or hardcoded safe value (500 pennies)
            survival_cost = int(DEFAULT_BASIC_FOOD_PRICE)

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

        # 3. Convert to Absolute TaxBracketDTOs (in pennies)
        progressive_tax_brackets: List[TaxBracketDTO] = []
        previous_ceiling = 0

        for multiple, rate in raw_brackets:
            if multiple == float('inf'):
                ceiling = None
            else:
                ceiling = int(multiple * survival_cost)

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

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: int) -> int:
        """
        Calculates the tax owed based on a progressive bracket system.
        Income and return value are in pennies.
        """
        if income <= 0:
            return 0

        total_tax = 0.0

        for bracket in policy.progressive_tax_brackets:
            # Determine the income chunk that falls into this bracket
            bracket_floor = bracket.floor
            bracket_ceiling = bracket.ceiling if bracket.ceiling is not None else float('inf')

            if income <= bracket_floor:
                continue

            # Calculate taxable amount in this bracket
            # Use float('inf') comparison logic
            if bracket.ceiling is None:
                 taxable_in_bracket = income - bracket_floor
            else:
                 taxable_in_bracket = min(income, bracket_ceiling) - bracket_floor

            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate

            if bracket.ceiling is not None and income <= bracket_ceiling:
                break

        return round_to_pennies(total_tax)

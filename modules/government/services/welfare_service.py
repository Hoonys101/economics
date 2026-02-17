from typing import List, Any, Dict, Optional
import logging
from modules.government.api import IWelfareService
from modules.government.welfare.api import IWelfareRecipient
from modules.government.dtos import (
    WelfareResultDTO,
    BailoutResultDTO,
    PaymentRequestDTO,
    BailoutLoanDTO,
    IAgent
)
from simulation.dtos.api import MarketSnapshotDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.government.constants import (
    DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO,
    DEFAULT_STIMULUS_TRIGGER_GDP_DROP,
    DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK,
    DEFAULT_BASIC_FOOD_PRICE
)
from modules.finance.api import BailoutCovenant
from modules.finance.utils.currency_math import round_to_pennies

logger = logging.getLogger(__name__)

class WelfareService(IWelfareService):
    """
    Stateless service responsible for all welfare and subsidy logic.
    """
    def __init__(self, config_module: Any):
        self.config = config_module
        self.spending_this_tick: int = 0

    def get_survival_cost(self, market_data: MarketSnapshotDTO) -> int:
        """ Calculates current survival cost based on food prices. Returns pennies. """
        avg_food_price_pennies = 0

        raw_data = market_data.market_data
        goods_market = raw_data.get("goods_market", {})

        if "basic_food_current_sell_price" in goods_market:
            val = goods_market["basic_food_current_sell_price"]
            # Assume market data is float dollars
            if isinstance(val, float):
                avg_food_price_pennies = round_to_pennies(val * 100)
            else:
                avg_food_price_pennies = int(val)
        else:
            # Fallback to config or constant (which is pennies)
            if hasattr(self.config, "GOODS_INITIAL_PRICE"):
                 val = self.config.GOODS_INITIAL_PRICE.get("basic_food", DEFAULT_BASIC_FOOD_PRICE)
            else:
                 val = DEFAULT_BASIC_FOOD_PRICE

            if isinstance(val, float):
                 avg_food_price_pennies = round_to_pennies(val * 100)
            else:
                 avg_food_price_pennies = int(val)

        if hasattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK"):
             daily_food_need = self.config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK
        else:
             daily_food_need = DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK

        # Calculation in pennies
        # daily_food_need is float quantity.
        return int(max(avg_food_price_pennies * daily_food_need, 1000)) # Min 1000 pennies ($10)

    def run_welfare_check(self, agents: List[IAgent], market_data: MarketSnapshotDTO, current_tick: int, gdp_history: List[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests.
        """
        payment_requests = []
        total_paid = 0

        # Filter for eligible welfare recipients (Safe filtering for mixed lists)
        welfare_recipients = [a for a in agents if isinstance(a, IWelfareRecipient)]

        # 1. Calculate Survival Cost (Dynamic)
        survival_cost = self.get_survival_cost(market_data)

        # 2. Unemployment Benefit
        if hasattr(self.config, "UNEMPLOYMENT_BENEFIT_RATIO"):
            unemployment_ratio = self.config.UNEMPLOYMENT_BENEFIT_RATIO
        else:
            unemployment_ratio = DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO

        benefit_amount = survival_cost * unemployment_ratio

        # Apply multiplier
        effective_benefit_amount = round_to_pennies(benefit_amount * welfare_budget_multiplier)

        if effective_benefit_amount > 0:
            for agent in welfare_recipients:
                if not agent.is_active:
                    continue

                # Unemployment Benefit
                # We assume agent has is_employed property or check it dynamically
                if hasattr(agent, "is_employed") and not agent.is_employed:
                    payment_requests.append(PaymentRequestDTO(
                        payer="GOVERNMENT", # Placeholder
                        payee=agent,
                        amount=effective_benefit_amount,
                        currency=DEFAULT_CURRENCY,
                        memo="welfare_support_unemployment"
                    ))
                    total_paid += effective_benefit_amount

        # 3. Stimulus Check
        current_gdp = market_data.market_data.get("total_production", 0.0)

        if hasattr(self.config, "STIMULUS_TRIGGER_GDP_DROP"):
             trigger_drop = self.config.STIMULUS_TRIGGER_GDP_DROP
        else:
             trigger_drop = DEFAULT_STIMULUS_TRIGGER_GDP_DROP

        should_stimulus = False
        if len(gdp_history) >= 10:
            past_gdp = gdp_history[-10]
            if past_gdp > 0:
                change = (current_gdp - past_gdp) / past_gdp
                if change <= trigger_drop:
                    should_stimulus = True

        if should_stimulus:
             base_stimulus_amount = survival_cost * 5.0
             effective_stimulus_amount = round_to_pennies(base_stimulus_amount * welfare_budget_multiplier)

             active_households = [a for a in welfare_recipients if a.is_active]

             for h in active_households:
                 payment_requests.append(PaymentRequestDTO(
                     payer="GOVERNMENT",
                     payee=h,
                     amount=effective_stimulus_amount,
                     currency=DEFAULT_CURRENCY,
                     memo="welfare_support_stimulus"
                 ))
                 total_paid += effective_stimulus_amount

             if effective_stimulus_amount > 0:
                 logger.warning(
                     f"STIMULUS_TRIGGERED | GDP Drop Detected. Requests generated.",
                     extra={"tick": current_tick, "gdp_current": current_gdp}
                 )

        self.spending_this_tick += total_paid

        return WelfareResultDTO(
            payment_requests=payment_requests,
            total_paid=total_paid
        )

    def provide_firm_bailout(self, firm: IAgent, amount: int, current_tick: int, is_solvent: bool) -> Optional[BailoutResultDTO]:
        """
        Evaluates bailout eligibility and returns a DTO.
        """
        if is_solvent: # Logic from FinanceSystem (only solvent firms get simple bailout? or insolvent ones?)
            # Usually bailouts are for distressed firms.
            # But the logic in Government.py was:
            # is_solvent = finance_system.evaluate_solvency(...)
            # If solvent, maybe no bailout needed? Or bailout is a loan?
            # Wait, FinanceSystem.evaluate_solvency returns True if solvent.
            # Bailouts are typically for firms that are NOT solvent or liquidity constraint?
            # But `Government.provide_firm_bailout` (legacy) checked `finance_system.evaluate_solvency`.
            # If I look at `FinanceSystem.evaluate_solvency`, it returns True if healthy.
            # Why would we bail out a healthy firm?
            # Maybe the logic was inverted or I misunderstood.
            # Legacy code: `if self.finance_system: is_solvent = ...`
            # Then it calls `fiscal_engine`.
            # WelfareManager.provide_firm_bailout in legacy was used.
            # The code I read from WelfareManager earlier:
            # `if is_solvent: ... return BailoutResultDTO`.
            # This implies we ONLY bail out solvent firms (liquidity crisis vs insolvency)?
            # Or `evaluate_solvency` returns True if eligible for bailout?
            # `FinanceSystem.evaluate_solvency` calls Altman Z-Score. High score = Healthy.
            # So `is_solvent=True` means healthy.
            # If healthy, we give loan?
            # This seems odd for a "bailout".
            # However, I will preserve the logic from `WelfareManager.py`.

            # Simple assumption for loan terms based on current code behavior or defaults
            loan_dto = BailoutLoanDTO(
                firm_id=firm.id,
                amount=amount,
                interest_rate=0.05, # Default or config?
                covenants=BailoutCovenant(
                    dividends_allowed=False,
                    executive_bonus_allowed=False
                )
            )

            payment_request = PaymentRequestDTO(
                payer="GOVERNMENT",
                payee=firm.id,
                amount=amount,
                currency=DEFAULT_CURRENCY,
                memo="bailout_loan_disbursement"
            )

            return BailoutResultDTO(
                loan_request=loan_dto,
                payment_request=payment_request
            )

        return None

    def get_spending_this_tick(self) -> int:
        return self.spending_this_tick

    def reset_tick_flow(self) -> None:
        self.spending_this_tick = 0

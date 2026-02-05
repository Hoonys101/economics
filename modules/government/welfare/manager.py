from typing import List, Any, Dict, Optional
import logging
from modules.government.api import IWelfareManager
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

logger = logging.getLogger(__name__)

class WelfareManager(IWelfareManager):
    def __init__(self, config_module: Any):
        self.config = config_module
        self.spending_this_tick: float = 0.0

    def get_survival_cost(self, market_data: MarketSnapshotDTO) -> float:
        """ Calculates current survival cost based on food prices. """
        avg_food_price = 0.0

        raw_data = market_data.market_data
        goods_market = raw_data.get("goods_market", {})

        if "basic_food_current_sell_price" in goods_market:
            avg_food_price = goods_market["basic_food_current_sell_price"]
        else:
            avg_food_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("basic_food", DEFAULT_BASIC_FOOD_PRICE)

        daily_food_need = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK)
        return max(avg_food_price * daily_food_need, 10.0)

    def run_welfare_check(self, agents: List[IAgent], market_data: MarketSnapshotDTO, current_tick: int, gdp_history: List[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests.
        """
        payment_requests = []
        total_paid = 0.0

        # Filter for eligible welfare recipients (Safe filtering for mixed lists)
        welfare_recipients = [a for a in agents if isinstance(a, IWelfareRecipient)]

        # 1. Calculate Survival Cost (Dynamic)
        survival_cost = self.get_survival_cost(market_data)

        # 2. Unemployment Benefit
        unemployment_ratio = getattr(self.config, "UNEMPLOYMENT_BENEFIT_RATIO", DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO)
        benefit_amount = survival_cost * unemployment_ratio

        # Apply multiplier
        effective_benefit_amount = benefit_amount * welfare_budget_multiplier

        if effective_benefit_amount > 0:
            for agent in welfare_recipients:
                if not agent.is_active:
                    continue

                # Unemployment Benefit
                if not agent.is_employed:
                    payment_requests.append(PaymentRequestDTO(
                        payer="GOVERNMENT", # Placeholder, will be replaced by actual ID in execution or ignored
                        payee=agent,
                        amount=effective_benefit_amount,
                        currency=DEFAULT_CURRENCY,
                        memo="welfare_support_unemployment"
                    ))
                    total_paid += effective_benefit_amount

        # 3. Stimulus Check
        current_gdp = market_data.market_data.get("total_production", 0.0)

        trigger_drop = getattr(self.config, "STIMULUS_TRIGGER_GDP_DROP", DEFAULT_STIMULUS_TRIGGER_GDP_DROP)

        should_stimulus = False
        if len(gdp_history) >= 10:
            past_gdp = gdp_history[-10]
            if past_gdp > 0:
                change = (current_gdp - past_gdp) / past_gdp
                if change <= trigger_drop:
                    should_stimulus = True

        if should_stimulus:
             base_stimulus_amount = survival_cost * 5.0
             effective_stimulus_amount = base_stimulus_amount * welfare_budget_multiplier

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

    def provide_firm_bailout(self, firm: IAgent, amount: float, current_tick: int, is_solvent: bool) -> Optional[BailoutResultDTO]:
        """
        Evaluates bailout eligibility and returns a DTO.
        """
        if is_solvent:
            # Create Loan DTO
            # Logic from FinanceSystem.grant_bailout_loan would be moved/mirrored here?
            # Or we assume FinanceSystem still handles the specifics of the loan creation?
            # The spec says "Returns a DTO containing a loan request".
            # The Government agent, upon receiving this, should probably ask FinanceSystem to create the loan using this DTO.

            # Simple assumption for loan terms based on current code behavior or defaults
            loan_dto = BailoutLoanDTO(
                firm_id=firm.id,
                amount=amount,
                interest_rate=0.05, # Default or config?
                covenants=BailoutCovenant(
                    dividends_allowed=False,
                    executive_salary_freeze=True,
                    mandatory_repayment=0.5
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

    def get_spending_this_tick(self) -> float:
        return self.spending_this_tick

    def reset_tick_flow(self) -> None:
        self.spending_this_tick = 0.0

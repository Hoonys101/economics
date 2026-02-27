from _typeshed import Incomplete
from modules.finance.api import BailoutCovenant as BailoutCovenant
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from modules.government.api import IWelfareService as IWelfareService
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE as DEFAULT_BASIC_FOOD_PRICE, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK as DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK, DEFAULT_STIMULUS_TRIGGER_GDP_DROP as DEFAULT_STIMULUS_TRIGGER_GDP_DROP, DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO as DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO
from modules.government.dtos import BailoutLoanDTO as BailoutLoanDTO, BailoutResultDTO as BailoutResultDTO, IAgent as IAgent, PaymentRequestDTO as PaymentRequestDTO, WelfareResultDTO as WelfareResultDTO
from modules.government.welfare.api import IWelfareRecipient as IWelfareRecipient
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.dtos.api import MarketSnapshotDTO as MarketSnapshotDTO
from typing import Any

logger: Incomplete

class WelfareService(IWelfareService):
    """
    Stateless service responsible for all welfare and subsidy logic.
    """
    config: Incomplete
    spending_this_tick: int
    def __init__(self, config_module: Any) -> None: ...
    def get_survival_cost(self, market_data: MarketSnapshotDTO) -> int:
        """ Calculates current survival cost based on food prices. Returns pennies. """
    def run_welfare_check(self, agents: list[IAgent], market_data: MarketSnapshotDTO, current_tick: int, gdp_history: list[float], welfare_budget_multiplier: float = 1.0) -> WelfareResultDTO:
        """
        Identifies agents needing support and returns a DTO containing
        welfare payment requests.
        """
    def provide_firm_bailout(self, firm: IAgent, amount: int, current_tick: int, is_solvent: bool) -> BailoutResultDTO | None:
        """
        Evaluates bailout eligibility and returns a DTO.
        """
    def get_spending_this_tick(self) -> int: ...
    def reset_tick_flow(self) -> None: ...

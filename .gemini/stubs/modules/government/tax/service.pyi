from _typeshed import Incomplete
from decimal import Decimal as Decimal
from modules.finance.api import IFinancialEntity as IFinancialEntity, TaxCollectionResult as TaxCollectionResult
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from modules.government.api import ITaxService as ITaxService, ITaxableHousehold as ITaxableHousehold
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager as FiscalPolicyManager
from modules.government.constants import DEFAULT_ANNUAL_WEALTH_TAX_RATE as DEFAULT_ANNUAL_WEALTH_TAX_RATE, DEFAULT_TICKS_PER_YEAR as DEFAULT_TICKS_PER_YEAR, DEFAULT_WEALTH_TAX_THRESHOLD as DEFAULT_WEALTH_TAX_THRESHOLD
from modules.government.dtos import FiscalPolicyDTO as FiscalPolicyDTO, IAgent as IAgent, PaymentRequestDTO as PaymentRequestDTO, TaxAssessmentResultDTO as TaxAssessmentResultDTO
from modules.government.taxation.system import TaxationSystem as TaxationSystem
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.dtos.api import MarketSnapshotDTO as MarketSnapshotDTO
from typing import Any

class TaxService(ITaxService):
    """
    Implementation of the ITaxService.
    Encapsulates tax calculation and revenue recording logic.
    MIGRATION: Uses integer pennies.
    """
    config_module: Incomplete
    taxation_system: Incomplete
    fiscal_policy_manager: Incomplete
    total_collected_tax: dict[CurrencyCode, int]
    revenue_this_tick: dict[CurrencyCode, int]
    tax_revenue: dict[str, int]
    current_tick_stats: dict[str, Any]
    def __init__(self, config_module: Any) -> None: ...
    def determine_fiscal_stance(self, snapshot: MarketSnapshotDTO) -> FiscalPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: int) -> int:
        """Calculates the tax amount for a given income and fiscal policy."""
    def calculate_corporate_tax(self, profit: int, rate: float) -> int:
        """Calculates corporate tax based on profit and a flat rate."""
    def calculate_wealth_tax(self, net_worth: int) -> int:
        """Calculates wealth tax based on net worth (pennies)."""
    def collect_wealth_tax(self, agents: list[IAgent]) -> TaxAssessmentResultDTO:
        """
        Calculates wealth tax for all eligible agents and returns a DTO
        containing payment requests for the government to execute.
        """
    def record_revenue(self, result: TaxCollectionResult) -> None:
        """
        Updates internal ledgers based on a verified tax collection result.
        """
    def get_revenue_this_tick(self) -> dict[CurrencyCode, int]: ...
    def get_revenue_breakdown_this_tick(self) -> dict[str, float]: ...
    def get_total_collected_this_tick(self) -> int: ...
    def get_tax_revenue(self) -> dict[str, int]: ...
    def get_total_collected_tax(self) -> dict[CurrencyCode, int]: ...
    def reset_tick_flow(self) -> None: ...

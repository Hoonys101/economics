from _typeshed import Incomplete
from dataclasses import dataclass
from modules.finance.api import IFinancialAgent as IFinancialAgent
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from modules.government.api import IGovernment as IGovernment
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE as DEFAULT_BASIC_FOOD_PRICE, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK as DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK
from modules.government.dtos import TaxBracketDTO as TaxBracketDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.dtos.settlement_dtos import SettlementResultDTO as SettlementResultDTO
from simulation.dtos.transactions import TransactionDTO as TransactionDTO
from simulation.firms import Firm as Firm
from simulation.models import Transaction
from typing import Any, Protocol

logger: Incomplete

class ITaxConfig(Protocol):
    TAX_BRACKETS: list[tuple[float, float]]
    TAX_RATE_BASE: float
    SALES_TAX_RATE: float
    GOODS_INITIAL_PRICE: dict[str, float]
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK: float
    TAX_MODE: str
    INCOME_TAX_PAYER: str
    CORPORATE_TAX_RATE: float

@dataclass
class TaxIntent:
    payer_id: int
    payee_id: int
    amount: int
    reason: str

class TaxationSystem:
    """
    Pure logic component for tax calculations.
    Decoupled from Government agent state (policies are passed in) and Settlement execution.
    """
    config_module: Incomplete
    def __init__(self, config_module: Any) -> None: ...
    def calculate_income_tax(self, income: int, survival_cost: int, current_income_tax_rate: float, tax_mode: str = 'PROGRESSIVE', tax_brackets: list[TaxBracketDTO] | None = None) -> int:
        """
        Calculates income tax based on the provided parameters.
        Logic moved from TaxAgency.
        income and survival_cost are in pennies.
        """
    def calculate_corporate_tax(self, profit: int, current_corporate_tax_rate: float) -> int:
        """Calculates corporate tax."""
    def calculate_tax_intents(self, transaction: Transaction, buyer: IFinancialAgent, seller: IFinancialAgent, government: IGovernment, market_data: dict[str, Any] | None = None) -> list[TaxIntent]:
        """
        Determines applicable taxes for a transaction and returns TaxIntents.
        Does NOT execute any transfer.
        """
    def generate_corporate_tax_intents(self, firms: list['Firm'], current_tick: int) -> list['TransactionDTO']:
        """
        Calculates corporate tax for all eligible firms and returns transaction intents.
        """
    def record_revenue(self, results: list['SettlementResultDTO']) -> None:
        """
        Records the outcome of tax payments.
        """

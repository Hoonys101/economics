from _typeshed import Incomplete
from modules.finance.api import IBank as IBank, ICentralBank, IFinancialAgent, IFinancialEntity, InsufficientFundsError as InsufficientFundsError, OMOInstructionDTO
from modules.finance.monetary.api import IMonetaryStrategy as IMonetaryStrategy
from modules.finance.wallet.api import IWallet as IWallet
from modules.memory.api import MemoryV2Interface as MemoryV2Interface
from modules.system.api import CurrencyCode as CurrencyCode, ICurrencyHolder
from simulation.core_markets import Market as Market
from simulation.dtos.strategy import ScenarioStrategy as ScenarioStrategy
from simulation.models import Order as Order, Transaction as Transaction
from typing import Any

logger: Incomplete

class CentralBank(ICurrencyHolder, IFinancialAgent, IFinancialEntity, ICentralBank):
    """
    Wave 5: Central Bank Agent.
    Implements Multi-Rule Strategy Pattern for monetary policy.
    Supports Taylor Rule, Friedman k%, and McCallum Rule.
    """
    id: Incomplete
    tracker: Incomplete
    config_module: Incomplete
    memory_v2: Incomplete
    strategy: Incomplete
    bonds: list[Any]
    wallet: Incomplete
    bond_market: Market | None
    base_rate: Incomplete
    update_interval: Incomplete
    inflation_target: Incomplete
    monetary_policy: IMonetaryStrategy
    monetary_config: Incomplete
    potential_gdp: float
    gdp_ema_alpha: float
    def __init__(self, tracker: Any, config_module: Any, memory_interface: MemoryV2Interface | None = None, strategy: ScenarioStrategy | None = None) -> None: ...
    def set_bond_market(self, market: Market) -> None:
        """Sets the bond market reference for OMO execution."""
    @property
    def assets(self) -> dict[CurrencyCode, int]:
        """Legacy compatibility accessor."""
    @property
    def balance_pennies(self) -> int: ...
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    def get_all_balances(self) -> dict[CurrencyCode, int]: ...
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]:
        """Implementation of ICurrencyHolder."""
    def purchase_bonds(self, bond: Any) -> None:
        """
        Purchases government bonds, adding them to the Central Bank's balance sheet.
        This is a key part of Quantitative Easing (QE).
        """
    def add_bond_to_portfolio(self, bond: Any) -> None:
        """
        Adds a bond to the portfolio.
        Protocol method expected by FinanceSystem.
        """
    def get_base_rate(self) -> float: ...
    def step(self, current_tick: int):
        """
        Called every tick by Engine.
        Updates Potential GDP estimate and recalculates rate/executes OMO periodically.
        """
    def deposit(self, amount: int, currency: CurrencyCode = ...) -> None:
        """Deposits a given amount into the central bank's cash reserves."""
    def mint(self, amount: int, currency: CurrencyCode = ...) -> None:
        """
        Mints new currency (adds to cash reserves).
        Alias for deposit but semantically distinct for Genesis Protocol.
        """
    def withdraw(self, amount: int, currency: CurrencyCode = ...) -> None:
        """
        Withdraws a given amount from the central bank's cash reserves.
        As a Fiat Currency Issuer, the Central Bank can have a negative balance (creating money).
        """
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    def get_all_balances(self) -> dict[CurrencyCode, int]: ...
    @property
    def total_wealth(self) -> int: ...
    def get_liquid_assets(self, currency: CurrencyCode = ...) -> int: ...
    def get_total_debt(self) -> int: ...
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> list[Order]:
        """
        Takes an instruction and creates market orders to fulfill it.
        This generates the Orders, but they must be placed by the caller (step method).
        """
    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for OMO settlement.
        """

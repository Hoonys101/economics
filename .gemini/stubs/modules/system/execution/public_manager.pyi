from _typeshed import Incomplete
from modules.finance.api import IFinancialAgent as IFinancialAgent, ILiquidator as ILiquidator, ISettlementSystem as ISettlementSystem, InsufficientFundsError as InsufficientFundsError
from modules.simulation.api import IConfigurable as IConfigurable
from modules.system.api import AgentBankruptcyEventDTO as AgentBankruptcyEventDTO, AssetBuyoutRequestDTO as AssetBuyoutRequestDTO, AssetBuyoutResultDTO as AssetBuyoutResultDTO, CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY, IAssetRecoverySystem as IAssetRecoverySystem, ICurrencyHolder as ICurrencyHolder, ISystemFinancialAgent as ISystemFinancialAgent, MarketSignalDTO as MarketSignalDTO, PublicManagerReportDTO as PublicManagerReportDTO
from modules.system.constants import ID_PUBLIC_MANAGER as ID_PUBLIC_MANAGER
from simulation.models import Order
from typing import Any

class PublicManager(IAssetRecoverySystem, ILiquidator, ICurrencyHolder, IFinancialAgent, ISystemFinancialAgent):
    """
    A system-level service responsible for asset recovery and liquidation.
    It acts as a 'Receiver' in bankruptcy proceedings, taking custody of assets
    and liquidating them back into the market to prevent value destruction.

    Implements IAssetRecoverySystem, ILiquidator, and IFinancialAgent.
    """
    config: Incomplete
    logger: Incomplete
    managed_inventory: dict[str, float]
    system_treasury: dict[CurrencyCode, int]
    settlement_system: ISettlementSystem | None
    last_tick_recovered_assets: dict[str, float]
    last_tick_revenue: dict[CurrencyCode, int]
    total_revenue_lifetime: dict[CurrencyCode, int]
    cumulative_deficit: int
    def __init__(self, config: Any) -> None: ...
    @property
    def id(self) -> int:
        """Returns the unique integer ID for the PublicManager."""
    def is_system_agent(self) -> bool:
        """Marker for SettlementSystem to allow overdraft (Soft Budget Constraint)."""
    def get_balance(self, currency: CurrencyCode = ...) -> int:
        """Returns the current balance for the specified currency."""
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]:
        """Implementation of ICurrencyHolder."""
    @property
    def balance_pennies(self) -> int: ...
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    def get_liquid_assets(self, currency: CurrencyCode = ...) -> int: ...
    def get_total_debt(self) -> int: ...
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """Takes ownership of a defunct agent's inventory."""
    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent.
        Updates internal inventory state but does NOT move funds (caller must execute transfer).
        """
    def receive_liquidated_assets(self, inventory: dict[str, float]) -> None:
        """
        Receives inventory from a liquidated firm via asset buyout.
        Used by LiquidationManager during the 'Asset Liquidation' phase.
        """
    def generate_liquidation_orders(self, market_signals: dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> list[Order]:
        """
        Generates non-disruptive SELL orders for managed assets.
        This is typically called in Phase 4.5.
        """
    def confirm_sale(self, item_id: str, quantity: float) -> None:
        """
        Confirms a sale transaction and permanently removes assets from inventory.
        Must be called by TransactionManager upon successful trade.
        """
    def deposit_revenue(self, amount: int, currency: CurrencyCode = ...) -> None:
        """Deposits revenue from liquidation sales into the system treasury."""
    def get_deficit(self) -> int: ...
    def get_status_report(self) -> PublicManagerReportDTO: ...
    def set_settlement_system(self, system: ISettlementSystem) -> None:
        """Injects the SettlementSystem dependency for Mint-to-Buy operations."""
    def liquidate_assets(self, bankrupt_agent: IFinancialAgent, assets: Any, tick: int) -> None:
        '''
        Implementation of ILiquidator.
        Performs "Mint-to-Buy" asset recovery:
        1. Valuates assets using agent configuration.
        2. Takes custody of assets (Inventory Update).
        3. Mints new money to pay the bankrupt agent (Liquidity Injection).
        '''

import logging
from _typeshed import Incomplete
from modules.finance.api import AgentID as AgentID, FXMatchDTO as FXMatchDTO, IAccountRegistry as IAccountRegistry, IBank, ICentralBank, IEconomicMetricsService as IEconomicMetricsService, IFinancialAgent, IHeirProvider as IHeirProvider, ILiquidator, IMonetaryAuthority, IMonetaryLedger as IMonetaryLedger, IPanicRecorder as IPanicRecorder, IPortfolioHandler as IPortfolioHandler, InsufficientFundsError as InsufficientFundsError, LienDTO as LienDTO, PortfolioAsset as PortfolioAsset, PortfolioDTO as PortfolioDTO, ZeroSumViolationError as ZeroSumViolationError
from modules.finance.transaction.api import TransactionResultDTO as TransactionResultDTO
from modules.government.api import IGovernment as IGovernment
from modules.market.housing_planner_api import MortgageApplicationDTO as MortgageApplicationDTO
from modules.system.api import CurrencyCode as CurrencyCode, IAgentRegistry as IAgentRegistry
from modules.system.constants import ID_ESCROW as ID_ESCROW, ID_PUBLIC_MANAGER as ID_PUBLIC_MANAGER, ID_SYSTEM as ID_SYSTEM
from simulation.finance.api import ITransaction as ITransaction
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from typing import Any
from uuid import UUID as UUID

class SettlementSystem(IMonetaryAuthority):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.
    MIGRATION: Uses integer pennies for all monetary values.
    INTEGRATION: Uses TransactionEngine for atomic transfers.
    """
    logger: Incomplete
    bank: Incomplete
    metrics_service: Incomplete
    total_liquidation_losses: int
    agent_registry: Incomplete
    estate_registry: Incomplete
    panic_recorder: IPanicRecorder | None
    monetary_authority: ICentralBank | None
    monetary_ledger: IMonetaryLedger | None
    account_registry: Incomplete
    def __init__(self, logger: logging.Logger | None = None, bank: IBank | None = None, metrics_service: IEconomicMetricsService | None = None, agent_registry: IAgentRegistry | None = None, account_registry: IAccountRegistry | None = None, estate_registry: Any | None = None) -> None: ...
    def set_monetary_ledger(self, ledger: IMonetaryLedger) -> None: ...
    def set_monetary_authority(self, authority: ICentralBank) -> None:
        """Sets the monetary authority (Central Bank System) for LLR operations."""
    def set_panic_recorder(self, recorder: IPanicRecorder) -> None: ...
    def set_metrics_service(self, service: IEconomicMetricsService) -> None:
        """Sets the economic metrics service for recording system-wide financial events."""
    def register_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """
        Registers an account link between a bank and an agent.
        Used to maintain the reverse index for bank runs.
        """
    def deregister_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """
        Removes an account link between a bank and an agent.
        """
    def get_account_holders(self, bank_id: AgentID) -> list[AgentID]:
        """
        Returns a list of all agents holding accounts at the specified bank.
        This provides O(1) access to depositors for bank run simulation.
        """
    def get_agent_banks(self, agent_id: AgentID) -> list[AgentID]:
        """
        Returns a list of banks where the agent holds an account.
        """
    def remove_agent_from_all_accounts(self, agent_id: AgentID) -> None:
        """
        Removes an agent from all bank account indices.
        Called upon agent liquidation/deletion.
        """
    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = ...) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
    def get_total_circulating_cash(self, currency: CurrencyCode = ...) -> int:
        """
        Deprecated: Use get_total_m2_pennies() instead.
        Previously returned physical cash held by non-bank agents.
        Now aliases to get_total_m2_pennies() for backward compatibility.
        """
    def get_total_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """
        Calculates total M2 = Sum(balances of Household + Firm + Government + Estate Registry agents).
        Strictly excludes ID_SYSTEM, ID_CENTRAL_BANK, ID_ESCROW, ID_PUBLIC_MANAGER, and any agent implementing IBank.
        Ensures agents are not counted twice (e.g. if in both registries).
        """
    def get_assets_by_currency(self) -> dict[str, int]:
        """
        Implements ICurrencyHolder for M2 verification.
        Returns total cash held in escrow accounts.
        """
    def process_liquidation(self, liquidator: ILiquidator, bankrupt_agent: IFinancialAgent, assets: Any, tick: int) -> None:
        """
        Delegates asset liquidation to the authorized liquidator.
        """
    def record_liquidation(self, agent: IFinancialAgent, inventory_value: int, capital_value: int, recovered_cash: int, reason: str, tick: int, government_agent: IFinancialAgent | None = None) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        """
    def execute_multiparty_settlement(self, transfers: list[tuple[IFinancialAgent, IFinancialAgent, int]], tick: int) -> bool:
        """
        Executes a batch of transfers atomically using TransactionEngine.
        Format: (DebitAgent, CreditAgent, Amount)
        """
    def settle_atomic(self, debit_agent: IFinancialAgent, credits_list: list[tuple[IFinancialAgent, int, str]], tick: int) -> bool:
        """
        Executes a one-to-many atomic settlement.
        All credits are summed to determine the total debit amount.
        """
    def execute_swap(self, match: FXMatchDTO) -> ITransaction | None:
        """
        Phase 4.1: Executes an atomic currency swap (Barter FX).
        Ensures both legs (A->B, B->A) succeed or neither occurs.
        """
    def transfer(self, debit_agent: IFinancialAgent, credit_agent: IFinancialAgent, amount: int, memo: str, debit_context: dict[str, Any] | None = None, credit_context: dict[str, Any] | None = None, tick: int = 0, currency: CurrencyCode = ...) -> ITransaction | None:
        """
        Executes an atomic transfer using TransactionEngine.
        Returns the created Transaction object (or None on failure) to support the
        Transaction Injection Pattern used by System Agents (e.g., CentralBank).
        """
    def create_and_transfer(self, source_authority: IFinancialAgent, destination: IFinancialAgent, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> ITransaction | None:
        """
        Creates new money (or grants) and transfers it to an agent.
        """
    def transfer_and_destroy(self, source: IFinancialAgent, sink_authority: IFinancialAgent, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> ITransaction | None:
        """
        Transfers money from an agent to an authority to be destroyed.
        """
    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = 'god_mode_injection') -> bool: ...
    def audit_total_m2(self, expected_total: int | None = None) -> bool:
        """
        Verifies that the current M2 matches the expected total.
        logs MONEY_SUPPLY_CHECK tag for forensics.
        """

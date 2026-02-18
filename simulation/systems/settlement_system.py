from typing import Optional, Dict, Any, cast, TYPE_CHECKING, Tuple, List, Set
import logging
from uuid import UUID
from collections import defaultdict

from simulation.finance.api import ITransaction
from modules.finance.api import (
    IFinancialAgent, IFinancialEntity, IBank, InsufficientFundsError,
    IPortfolioHandler, PortfolioDTO, PortfolioAsset, IHeirProvider, LienDTO, AgentID,
    IMonetaryAuthority
)
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, ICurrencyHolder, IAgentRegistry
from modules.system.constants import ID_CENTRAL_BANK
from modules.market.housing_planner_api import MortgageApplicationDTO
from simulation.models import Transaction
from modules.simulation.api import IGovernment, ICentralBank, IAgent
from modules.common.protocol import enforce_purity

# Transaction Engine Imports
from modules.finance.transaction.api import TransactionResultDTO, TransactionDTO
from modules.finance.transaction.engine import (
    TransactionEngine, TransactionValidator, TransactionExecutor, SimpleTransactionLedger
)
from modules.finance.transaction.adapter import RegistryAccountAccessor, DictionaryAccountAccessor

if TYPE_CHECKING:
    from simulation.firms import Firm

class SettlementSystem(IMonetaryAuthority):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.
    MIGRATION: Uses integer pennies for all monetary values.
    INTEGRATION: Uses TransactionEngine for atomic transfers.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, bank: Optional[IBank] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bank = bank # TD-179: Reference to Bank for Seamless Payments
        self.total_liquidation_losses: int = 0
        self.agent_registry: Optional[IAgentRegistry] = None # Injected by SimulationInitializer

        # Transaction Engine (Initialized lazily)
        self._transaction_engine: Optional[TransactionEngine] = None

        # TD-INT-STRESS-SCALE: Reverse Index for Bank Accounts
        # BankID -> Set[AgentID]
        self._bank_depositors: Dict[int, Set[int]] = defaultdict(set)
        # AgentID -> Set[BankID] (for fast removal)
        self._agent_banks: Dict[int, Set[int]] = defaultdict(set)

    def _get_engine(self, context_agents: Optional[List[Any]] = None) -> TransactionEngine:
        """
        Retrieves the TransactionEngine.
        If Registry is available, returns the cached registry-backed engine.
        If Registry is missing (e.g., tests), constructs a temporary engine using context_agents.
        """
        if self.agent_registry:
            if not self._transaction_engine:
                # Initialize Registry-backed Engine
                accessor = RegistryAccountAccessor(self.agent_registry)
                validator = TransactionValidator(accessor)
                executor = TransactionExecutor(accessor)
                ledger = SimpleTransactionLedger(self.logger)
                self._transaction_engine = TransactionEngine(validator, executor, ledger)
            return self._transaction_engine

        # Fallback for Tests: Create temporary engine with local map
        if context_agents:
            agents_map = {}
            for agent in context_agents:
                # Use Protocol check if possible, or strict attribute access
                if isinstance(agent, IAgent) or hasattr(agent, 'id'):
                    agents_map[agent.id] = agent
                    agents_map[str(agent.id)] = agent

            accessor = DictionaryAccountAccessor(agents_map)
            validator = TransactionValidator(accessor)
            executor = TransactionExecutor(accessor)
            ledger = SimpleTransactionLedger(self.logger)
            return TransactionEngine(validator, executor, ledger)

        raise RuntimeError("Agent Registry not initialized in SettlementSystem and no context agents provided.")

    def register_account(self, bank_id: int, agent_id: int) -> None:
        """
        Registers an account link between a bank and an agent.
        Used to maintain the reverse index for bank runs.
        """
        self._bank_depositors[bank_id].add(agent_id)
        self._agent_banks[agent_id].add(bank_id)

    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        """
        Removes an account link between a bank and an agent.
        """
        if bank_id in self._bank_depositors:
            self._bank_depositors[bank_id].discard(agent_id)
            if not self._bank_depositors[bank_id]:
                del self._bank_depositors[bank_id]

        if agent_id in self._agent_banks:
            self._agent_banks[agent_id].discard(bank_id)
            if not self._agent_banks[agent_id]:
                del self._agent_banks[agent_id]

    def get_account_holders(self, bank_id: int) -> List[int]:
        """
        Returns a list of all agents holding accounts at the specified bank.
        This provides O(1) access to depositors for bank run simulation.
        """
        if bank_id in self._bank_depositors:
            return list(self._bank_depositors[bank_id])
        return []

    def remove_agent_from_all_accounts(self, agent_id: int) -> None:
        """
        Removes an agent from all bank account indices.
        Called upon agent liquidation/deletion.
        """
        if agent_id in self._agent_banks:
            # Copy to avoid modification during iteration
            banks = list(self._agent_banks[agent_id])
            for bank_id in banks:
                self.deregister_account(bank_id, agent_id)

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
        if self.agent_registry:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                # Prefer IFinancialEntity for standard "pennies" check if default currency
                if currency == DEFAULT_CURRENCY and isinstance(agent, IFinancialEntity):
                    return agent.balance_pennies

                # Fallback to IFinancialAgent for multi-currency or legacy
                if isinstance(agent, IFinancialAgent):
                    return agent.get_balance(currency)

        self.logger.warning(f"get_balance: Agent {agent_id} not found or Registry not linked or Agent not IFinancialAgent.")
        return 0

    def get_assets_by_currency(self) -> Dict[str, int]:
        """
        Implements ICurrencyHolder for M2 verification.
        Returns total cash held in escrow accounts.
        """
        return {DEFAULT_CURRENCY: 0}

    def record_liquidation(
        self,
        agent: IFinancialAgent,
        inventory_value: int,
        capital_value: int,
        recovered_cash: int,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialAgent] = None
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        """
        # Loss = Book Value (Inventory + Capital) - Recovered Cash
        loss_amount = inventory_value + capital_value - recovered_cash
        if loss_amount < 0:
            loss_amount = 0

        self.total_liquidation_losses += loss_amount

        agent_id = agent.id
        self.logger.info(
            f"LIQUIDATION: Agent {agent_id} liquidated. "
            f"Inventory: {inventory_value}, Capital: {capital_value}, Recovered: {recovered_cash}. "
            f"Net Destruction: {loss_amount}. Total Destroyed: {self.total_liquidation_losses}. "
            f"Reason: {reason}",
            extra={"tick": tick, "tags": ["liquidation", "bankruptcy", "ledger"]}
        )

        if government_agent:
            current_assets_val = agent.get_balance(DEFAULT_CURRENCY)

            if current_assets_val > 0:
                self.transfer(
                    debit_agent=agent,
                    credit_agent=government_agent,
                    amount=current_assets_val,
                    memo="liquidation_escheatment",
                    tick=tick,
                    currency=DEFAULT_CURRENCY
                )

    def execute_multiparty_settlement(
        self,
        transfers: List[Tuple[IFinancialAgent, IFinancialAgent, int]],
        tick: int
    ) -> bool:
        """
        Executes a batch of transfers atomically using TransactionEngine.
        Format: (DebitAgent, CreditAgent, Amount)
        """
        if not transfers:
            return True

        # Convert to TransactionDTOs
        dtos = []
        agents_involved = []

        for i, (debit, credit, amount) in enumerate(transfers):
             agents_involved.append(debit)
             agents_involved.append(credit)

             # Prep Seamless
             if not self._prepare_seamless_funds(debit, amount, DEFAULT_CURRENCY):
                 self.logger.warning(f"MULTIPARTY_FAIL | Insufficient funds for {debit.id}")
                 return False

             dtos.append(TransactionDTO(
                 transaction_id=f"batch_{tick}_{i}",
                 source_account_id=str(debit.id),
                 destination_account_id=str(credit.id),
                 amount=amount,
                 currency=DEFAULT_CURRENCY,
                 description=f"multiparty_seq_{i}"
             ))

        # Execute Batch
        try:
            engine = self._get_engine(context_agents=agents_involved)
            results = engine.process_batch(dtos)
        except RuntimeError:
             # If engine fails to init (no registry, no agents?), fail
             self.logger.error("MULTIPARTY_FAIL | Transaction Engine initialization failed.")
             return False

        # Check results
        all_success = all(r.status == 'COMPLETED' for r in results)

        if not all_success:
            self.logger.error("MULTIPARTY_FAIL | Batch execution failed.")
            return False

        return True

    def settle_atomic(
        self,
        debit_agent: IFinancialAgent,
        credits_list: List[Tuple[IFinancialAgent, int, str]],
        tick: int
    ) -> bool:
        """
        Executes a one-to-many atomic settlement.
        All credits are summed to determine the total debit amount.
        """
        if not credits_list:
            return True

        # 0. Validate Credits
        for _, amount, memo in credits_list:
             if not isinstance(amount, int) or amount < 0:
                 self.logger.error(f"SETTLEMENT_FAIL | Invalid credit amount {amount}. Memo: {memo}")
                 return False
             if not self._validate_memo(memo):
                 return False

        # 1. Calculate Total Debit
        total_debit = sum(amount for _, amount, _ in credits_list)
        if total_debit <= 0:
             return True

        # 2. Prepare Funds (Seamless)
        if not self._prepare_seamless_funds(debit_agent, total_debit, DEFAULT_CURRENCY):
            return False

        # 3. Create Batch DTOs
        dtos = []
        agents_involved = [debit_agent]

        for i, (credit_agent, amount, memo) in enumerate(credits_list):
            if amount <= 0: continue
            agents_involved.append(credit_agent)
            dtos.append(TransactionDTO(
                 transaction_id=f"atomic_{tick}_{i}",
                 source_account_id=str(debit_agent.id),
                 destination_account_id=str(credit_agent.id),
                 amount=amount,
                 currency=DEFAULT_CURRENCY,
                 description=memo
            ))

        # Execute Batch
        try:
            engine = self._get_engine(context_agents=agents_involved)
            results = engine.process_batch(dtos)
        except RuntimeError:
            self.logger.error("SETTLEMENT_ATOMIC_FAIL | Engine init failed.")
            return False

        return all(r.status == 'COMPLETED' for r in results)

    def _validate_memo(self, memo: str) -> bool:
        if not isinstance(memo, str):
            self.logger.warning(f"Invalid memo type: {type(memo)}. Rejecting.")
            return False
        if len(memo) > 255:
             self.logger.warning(f"Memo too long: {len(memo)} chars. Max 255. Rejecting.")
             return False
        return True

    def _prepare_seamless_funds(self, agent: IFinancialAgent, amount: int, currency: CurrencyCode) -> bool:
        """
        Checks if agent has enough cash. If not, attempts to withdraw from Bank
        and deposit to Agent's wallet (Seamless Payment).
        """
        # Central Bank check
        if isinstance(agent, ICentralBank) or (agent.id == ID_CENTRAL_BANK):
            return True

        current_cash = 0
        if isinstance(agent, IFinancialEntity) and currency == DEFAULT_CURRENCY:
            current_cash = agent.balance_pennies
        elif isinstance(agent, IFinancialAgent):
            current_cash = agent.get_balance(currency)

        if current_cash >= amount:
            return True

        # Needs Bank Withdrawal
        if self.bank and currency == DEFAULT_CURRENCY:
            needed = amount - current_cash
            # Check Bank Balance
            # Assuming bank uses string ID
            bank_balance = self.bank.get_customer_balance(str(agent.id))

            if bank_balance >= needed:
                success = self.bank.withdraw_for_customer(int(agent.id), needed)
                if success:
                    # Inject cash into agent wallet to preserve Zero-Sum
                    if isinstance(agent, IFinancialEntity):
                        agent.deposit(needed, currency)
                    elif isinstance(agent, IFinancialAgent):
                        agent._deposit(needed, currency)

                    self.logger.info(
                        f"SEAMLESS_PREP | Agent {agent.id} withdrew {needed} from bank to wallet for transfer.",
                        extra={"agent_id": agent.id}
                    )
                    return True

        self.logger.error(
            f"SETTLEMENT_FAIL | Insufficient funds (Cash+Bank). Cash: {current_cash}, Req: {amount}.",
            extra={"tags": ["insufficient_funds"]}
        )
        return False

    @enforce_purity()
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Executes an atomic transfer using TransactionEngine.
        """
        if not isinstance(amount, int):
             raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}.")

        if not self._validate_memo(memo):
            return None

        if amount <= 0:
            return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)

        if debit_agent is None or credit_agent is None:
             self.logger.error("SETTLEMENT_FAIL | Null agents.")
             return None

        # Prepare Funds
        if not self._prepare_seamless_funds(debit_agent, amount, currency):
            return None

        # Execute via Engine
        try:
            engine = self._get_engine(context_agents=[debit_agent, credit_agent])
            result = engine.process_transaction(
                source_account_id=str(debit_agent.id),
                destination_account_id=str(credit_agent.id),
                amount=amount,
                currency=currency,
                description=memo
            )
        except RuntimeError:
             self.logger.error("SETTLEMENT_FAIL | Engine init failed.")
             return None

        if result.status == 'COMPLETED':
             return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)
        else:
             self.logger.error(f"SETTLEMENT_FAIL | Engine Error: {result.message}")
             return None

    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        """
        if amount <= 0: return None

        is_central_bank = isinstance(source_authority, ICentralBank) or (source_authority.id == ID_CENTRAL_BANK)

        if is_central_bank:
            # Minting is special: Source doesn't need funds.
            try:
                if isinstance(destination, IFinancialEntity):
                    destination.deposit(amount, currency)
                elif isinstance(destination, IFinancialAgent):
                    destination._deposit(amount, currency)
                else:
                    self.logger.error(f"MINT_FAIL | Destination agent {destination.id} does not implement IFinancialEntity or IFinancialAgent.")
                    return None

                self.logger.info(
                    f"MINT_AND_TRANSFER | Created {amount} {currency} from {source_authority.id} to {destination.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                tx = self._create_transaction_record(source_authority.id, destination.id, amount, reason, tick)
                tx.transaction_type = "money_creation"
                return tx
            except Exception as e:
                self.logger.error(f"MINT_FAIL | {e}")
                return None
        else:
            return self.transfer(source_authority, destination, amount, reason, tick=tick, currency=currency)

    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed.
        """
        if amount <= 0: return None

        is_central_bank = isinstance(sink_authority, ICentralBank) or (sink_authority.id == ID_CENTRAL_BANK)

        if is_central_bank:
            # Burning: Withdraw from source.
            try:
                if isinstance(source, IFinancialEntity):
                    source.withdraw(amount, currency)
                elif isinstance(source, IFinancialAgent):
                    source._withdraw(amount, currency)

                self.logger.info(
                    f"TRANSFER_AND_DESTROY | Destroyed {amount} {currency} from {source.id} to {sink_authority.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                tx = self._create_transaction_record(source.id, sink_authority.id, amount, reason, tick)
                tx.transaction_type = "money_destruction"
                return tx
            except Exception as e:
                self.logger.error(f"BURN_FAIL | {e}")
                return None
        else:
            return self.transfer(source, sink_authority, amount, reason, tick=tick, currency=currency)

    def _create_transaction_record(self, buyer_id: int, seller_id: int, amount: int, memo: str, tick: int) -> Optional[Transaction]:
        if buyer_id is None or seller_id is None:
             return None

        return Transaction(
            buyer_id=buyer_id,
            seller_id=seller_id,
            item_id="currency",
            quantity=amount,
            price=1,
            market_id="settlement",
            transaction_type="transfer",
            time=tick,
            metadata={"memo": memo}
        )

    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = "god_mode_injection") -> bool:
        if not self.agent_registry: return False

        central_bank = self.agent_registry.get_agent(ID_CENTRAL_BANK)
        if not central_bank:
             central_bank = self.agent_registry.get_agent(str(ID_CENTRAL_BANK))
        if not central_bank: return False

        target_agent = self.agent_registry.get_agent(target_agent_id)
        if not target_agent: return False

        tx = self.create_and_transfer(
            source_authority=central_bank,
            destination=target_agent,
            amount=amount,
            reason=reason,
            tick=tick
        )
        return tx is not None

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        if not self.agent_registry: return False

        agents = self.agent_registry.get_all_financial_agents()
        total_cash = 0
        bank_reserves = 0
        total_deposits = 0

        for agent in agents:
            agent_id = getattr(agent, 'id', None)
            if agent_id == ID_CENTRAL_BANK or str(agent_id) == str(ID_CENTRAL_BANK):
                continue

            current_balance = 0
            if isinstance(agent, IFinancialEntity):
                current_balance = agent.balance_pennies
            elif isinstance(agent, IFinancialAgent):
                current_balance = agent.get_balance(DEFAULT_CURRENCY)
            elif isinstance(agent, ICurrencyHolder):
                 assets = agent.get_assets_by_currency()
                 current_balance = assets.get(DEFAULT_CURRENCY, 0)

            total_cash += current_balance

            if isinstance(agent, IBank):
                bank_reserves += current_balance
                total_deposits += agent.get_total_deposits()

        total_m2 = (total_cash - bank_reserves) + total_deposits

        if expected_total is not None:
            if total_m2 != expected_total:
                self.logger.critical(
                    f"AUDIT_INTEGRITY_FAILURE | M2 Mismatch! Expected: {expected_total}, Actual: {total_m2}, Diff: {total_m2 - expected_total}",
                    extra={"expected": expected_total, "actual": total_m2, "diff": total_m2 - expected_total}
                )
                return False
            else:
                self.logger.info(f"AUDIT_PASS | M2 Verified: {total_m2}")
                return True
        else:
             self.logger.info(f"AUDIT_PASS | M2 Current: {total_m2} (No expectation set)")
             return True

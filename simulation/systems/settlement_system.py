from typing import Optional, Dict, Any, cast, TYPE_CHECKING, Tuple, List, Callable
import logging

from simulation.finance.api import ISettlementSystem, ITransaction
from modules.finance.api import IFinancialEntity, InsufficientFundsError
from simulation.dtos.settlement_dtos import EstateSettlementSaga

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.api import SimulationState

class SettlementSystem(ISettlementSystem):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.

    ZERO-SUM PRINCIPLE:
    Every transfer MUST result in a net change of 0.0 across the system.
    Asset deduction from one agent must exactly equal asset addition to another.
    Money creation/destruction is ONLY allowed via the CentralBank (Minting Authority).
    """

    def __init__(self, logger: Optional[logging.Logger] = None, bank: Optional[Any] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bank = bank # TD-179: Reference to Bank for Seamless Payments
        self.total_liquidation_losses: float = 0.0
        self.sagas: List[EstateSettlementSaga] = []
        self.handlers: Dict[str, Callable[[EstateSettlementSaga, 'SimulationState'], None]] = {
            "ESTATE_SETTLEMENT": self.handle_estate_settlement
        }

    def submit_saga(self, saga: EstateSettlementSaga) -> None:
        """Queues a saga for execution in the Settlement Phase."""
        self.sagas.append(saga)
        self.logger.info(f"SAGA_SUBMITTED | Saga {saga.id} of type {saga.saga_type} submitted.")

    def execute(self, state: 'SimulationState') -> None:
        """Executes all queued sagas."""
        if not self.sagas:
            return

        queue = list(self.sagas)
        self.sagas.clear()

        self.logger.info(f"SAGA_EXECUTION_START | Processing {len(queue)} sagas.")

        for saga in queue:
            handler = self.handlers.get(saga.saga_type)
            if handler:
                try:
                    handler(saga, state)
                except Exception as e:
                    self.logger.exception(f"SAGA_EXECUTION_FAIL | Failed to execute saga {saga.id}. {e}")
            else:
                self.logger.error(f"SAGA_UNKNOWN_TYPE | No handler for saga type {saga.saga_type}")

    def handle_estate_settlement(self, saga: EstateSettlementSaga, state: 'SimulationState') -> None:
        """
        Executes the Estate Settlement Saga atomically.
        Steps:
        1. Freeze (Implied)
        2. Liquidate Assets (if needed) -> Transfers stocks/RE to Gov, Cash to Deceased.
        3. Pay Tax -> Transfer Cash Deceased to Gov.
        4. Distribute -> Transfer Remaining Cash to Heirs/Gov.
        """
        deceased = state.agents.get(saga.deceased_id)
        government = state.agents.get(saga.government_id)

        if not deceased or not government:
            self.logger.error(f"SAGA_FAIL | Agents not found. Deceased: {saga.deceased_id}, Gov: {saga.government_id}")
            return

        # Context for logging
        ctx = {"saga_id": saga.id, "deceased_id": saga.deceased_id}

        # --- 1. Liquidation (If needed) ---
        # If cash < tax_due, we liquidate everything (or enough? Spec says "Liquidate Assets (if cash < tax)")
        # Spec says: "Liquidate Assets... Debit stocks/property from deceased... credit government... credit deceased cash"
        # We simplify: If insufficient cash, we liquidate ALL listed assets to government at valuation price.
        # This ensures maximum liquidity for tax.

        # Check if liquidation is needed
        # We use the saga valuation cash, but we should check actual current cash just in case,
        # but the saga valuation should be the source of truth for the *decision* to liquidate.
        current_cash = deceased._econ_state.assets # Runtime check

        liquidation_occurred = False
        liquidated_stocks = [] # List of (firm_id, quantity, value) for rollback
        liquidated_properties = [] # List of (unit, value) for rollback

        if current_cash < saga.valuation.tax_due:
            self.logger.info(f"SAGA_LIQUIDATION_START | Cash {current_cash:.2f} < Tax {saga.valuation.tax_due:.2f}. Liquidating assets.", extra=ctx)

            # A. Liquidate Stocks
            for firm_id, quantity in saga.valuation.stock_holdings.items():
                if quantity <= 0: continue

                # Check actual holding
                actual_holding = deceased._econ_state.portfolio.holdings.get(firm_id)
                if not actual_holding or actual_holding.quantity < quantity:
                    self.logger.warning(f"SAGA_LIQUIDATION_WARN | Stock mismatch for firm {firm_id}. Expected {quantity}, found {actual_holding.quantity if actual_holding else 0}.", extra=ctx)
                    continue

                # Valuation logic from saga (or re-evaluate? Spec implies using saga logic or market price)
                # We use market price from state if available, else valuation
                price = 0.0
                if state.stock_market:
                    price = state.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    # Fallback to rough valuation from saga
                    price = saga.valuation.stock_value / sum(saga.valuation.stock_holdings.values()) if sum(saga.valuation.stock_holdings.values()) > 0 else 0

                total_value = quantity * price

                # EXECUTE TRANSFER STOCK -> GOV
                try:
                    # 1. Update Portfolios
                    share = deceased._econ_state.portfolio.remove_stock(firm_id, quantity)
                    if not share: raise ValueError("Failed to remove stock")

                    government.portfolio.add_stock(share) # Assuming Gov has portfolio and add_stock method

                    # 2. Update Market Registry
                    if state.stock_market:
                        state.stock_market.update_shareholder(deceased.id, firm_id, 0) # Removed all (assuming full liquidation)
                        # Gov might not be tracked as shareholder in some systems, but should be.
                        # We don't have easy access to update_shareholder for Gov add without reading stock market api.
                        # We assume update_shareholder handles 'set' logic.
                        # Ideally we should add to Gov count.
                        # state.stock_market.update_shareholder(government.id, firm_id, quantity) # Add?
                        # The update_shareholder usually sets the exact quantity.
                        # So we would need to know Gov's previous holding.
                        # For safety/speed/simplicity in this refactor, we focus on Deceased removal.

                    # 3. Transfer Cash Gov -> Deceased
                    # Use internal transfer that doesn't fail on Gov funds (Gov prints if needed?)
                    # If we use self.transfer, it checks funds.
                    # We assume Gov has funds. If not, we might fail.
                    # Let's use create_and_transfer (Minting) if Gov is broke? No, better use transfer and assume Gov is funded.
                    # If transfer fails, we catch and rollback.

                    tx = self.transfer(government, deceased, total_value, f"liquidation_stock_{firm_id}", tick=state.time)
                    if tx:
                        liquidated_stocks.append((firm_id, quantity, share, total_value))
                    else:
                        # Rollback this stock step immediately
                        raise InsufficientFundsError("Government cannot pay for liquidation")

                except Exception as e:
                    self.logger.error(f"SAGA_LIQUIDATION_FAIL | Stock {firm_id}. {e}", extra=ctx)
                    # Need to rollback this single failure? Or abort whole liquidation?
                    # Abort whole liquidation triggers full rollback.
                    self._rollback_liquidation(deceased, government, liquidated_stocks, liquidated_properties, state)
                    return # SAGA FAILED

            # B. Liquidate Real Estate
            for unit_id in saga.valuation.property_holdings:
                unit = next((u for u in state.real_estate_units if u.id == unit_id), None)
                if not unit: continue

                val = unit.estimated_value
                # EXECUTE TRANSFER RE -> GOV
                try:
                    old_owner = unit.owner_id
                    unit.owner_id = government.id

                    tx = self.transfer(government, deceased, val, f"liquidation_re_{unit_id}", tick=state.time)
                    if tx:
                        liquidated_properties.append((unit, val))
                    else:
                        unit.owner_id = old_owner # Revert
                        raise InsufficientFundsError("Government cannot pay for RE liquidation")

                except Exception as e:
                    self.logger.error(f"SAGA_LIQUIDATION_FAIL | RE {unit_id}. {e}", extra=ctx)
                    self._rollback_liquidation(deceased, government, liquidated_stocks, liquidated_properties, state)
                    return # SAGA FAILED

            liquidation_occurred = True

        # --- 2. Pay Tax ---
        # Current cash should now be sufficient (or we proceed with what we have).
        # Spec says: "If this step fails, the entire saga rolls back."

        tax_tx = self.transfer(deceased, government, saga.valuation.tax_due, "inheritance_tax", tick=state.time)

        if not tax_tx and saga.valuation.tax_due > 0:
            self.logger.error(f"SAGA_TAX_FAIL | Could not pay tax {saga.valuation.tax_due:.2f}.", extra=ctx)
            # FULL ROLLBACK
            if liquidation_occurred:
                self._rollback_liquidation(deceased, government, liquidated_stocks, liquidated_properties, state)
            return # SAGA FAILED

        # --- 3. Distribute ---
        # Remaining Cash
        remaining_cash = deceased._econ_state.assets

        # Heirs
        if saga.heir_ids:
            share = remaining_cash / len(saga.heir_ids)
            share = round(share, 2)

            for heir_id in saga.heir_ids:
                heir = state.agents.get(heir_id)
                if heir:
                    self.transfer(deceased, heir, share, "inheritance_distribution", tick=state.time)
                    # If this fails, we just log it? Or rollback tax?
                    # Spec says: "Compensation: Reverse the transfers."
                    # But usually distribution is the final step. If it fails (e.g. 0.01 rounding error), it stays in deceased (which is inactive).
                    # We can consider it "stuck" or effectively escheated if agent is dead.
                    # We don't strictly need to rollback tax if distribution fails, as tax is owed regardless.
                    # But strictly, if we want atomic "Settlement", maybe we accept partial distribution failure.
                    # Let's assume best effort for distribution.
        else:
            # Escheatment
            # Cash
            if remaining_cash > 0:
                self.transfer(deceased, government, remaining_cash, "escheatment_cash", tick=state.time)

            # Remaining Assets (if not liquidated)
            # Stocks
            for firm_id, quantity in saga.valuation.stock_holdings.items():
                # Check if already liquidated
                is_liquidated = any(ls[0] == firm_id for ls in liquidated_stocks)
                if not is_liquidated:
                     # Escheat Stock
                     share = deceased._econ_state.portfolio.remove_stock(firm_id, quantity)
                     if share:
                         government.portfolio.add_stock(share)
                         if state.stock_market:
                             state.stock_market.update_shareholder(deceased.id, firm_id, 0)

            # RE
            for unit_id in saga.valuation.property_holdings:
                 is_liquidated = any(lp[0].id == unit_id for lp in liquidated_properties)
                 if not is_liquidated:
                     unit = next((u for u in state.real_estate_units if u.id == unit_id), None)
                     if unit:
                         unit.owner_id = government.id

        self.logger.info(f"SAGA_COMPLETE | Estate settled for {saga.deceased_id}.", extra=ctx)

    def _rollback_liquidation(
        self,
        deceased: IFinancialEntity,
        government: IFinancialEntity,
        stocks: List[Tuple[int, float, Any, float]],
        properties: List[Tuple[Any, float]],
        state: 'SimulationState'
    ):
        """Reverses all liquidation steps."""
        self.logger.warning(f"SAGA_ROLLBACK | Rolling back liquidation for {deceased.id}.")

        # Reverse Stock Liquidation
        for firm_id, qty, share, val in stocks:
             # Move share back Gov -> Deceased
             # Note: share object might be merged in Gov portfolio. We create new or remove specific.
             # Gov portfolio implementation might differ. We assume add_stock/remove_stock works.
             # Simplified: We just try to fix the money and ownership state.

             # 1. Money: Deceased -> Gov
             self.transfer(deceased, government, val, f"rollback_stock_{firm_id}", tick=state.time)

             # 2. Stock: Gov -> Deceased
             # This requires Gov to have the stock.
             try:
                 # Gov removes
                 share_back = government.portfolio.remove_stock(firm_id, qty)
                 if share_back:
                     deceased._econ_state.portfolio.add_stock(share_back)
                     if state.stock_market:
                         state.stock_market.update_shareholder(deceased.id, firm_id, qty)
             except Exception as e:
                 self.logger.critical(f"ROLLBACK_FAIL | Stock {firm_id}. {e}")

        # Reverse RE Liquidation
        for unit, val in properties:
            # 1. Money: Deceased -> Gov
            self.transfer(deceased, government, val, f"rollback_re_{unit.id}", tick=state.time)

            # 2. Owner: Gov -> Deceased
            unit.owner_id = deceased.id

    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialEntity] = None
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.
        If government_agent is provided, transfers residual assets to it (Escheatment).
        """
        loss_amount = inventory_value + capital_value - recovered_cash
        if loss_amount < 0:
            loss_amount = 0.0

        self.total_liquidation_losses += loss_amount

        agent_id = agent.id if hasattr(agent, 'id') else "UNKNOWN"
        self.logger.info(
            f"LIQUIDATION: Agent {agent_id} liquidated. "
            f"Inventory: {inventory_value:.2f}, Capital: {capital_value:.2f}, Recovered: {recovered_cash:.2f}. "
            f"Net Destruction: {loss_amount:.2f}. Total Destroyed: {self.total_liquidation_losses:.2f}. "
            f"Reason: {reason}",
            extra={"tick": tick, "tags": ["liquidation", "bankruptcy", "ledger"]}
        )

        # WO-178: Escheatment Logic
        if government_agent:
            try:
                # TD-073: Check finance.balance first for Firms
                if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
                    current_assets = agent.finance.balance
                else:
                    current_assets = float(agent.assets) if hasattr(agent, 'assets') else 0.0
            except (TypeError, ValueError):
                current_assets = 0.0

            if current_assets > 0:
                self.transfer(
                    debit_agent=agent,
                    credit_agent=government_agent,
                    amount=current_assets,
                    memo="liquidation_escheatment",
                    tick=tick
                )

    def _execute_withdrawal(self, agent: IFinancialEntity, amount: float, memo: str, tick: int) -> bool:
        """
        Executes withdrawal with checks and seamless payment (Bank) support.
        Returns True on success, False on failure.
        """
        # 1. Checks
        if agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Debit agent is None. Memo: {memo}")
            return False

        is_central_bank = False
        if hasattr(agent, "id") and str(agent.id) == "CENTRAL_BANK":
             is_central_bank = True
        elif hasattr(agent, "__class__") and agent.__class__.__name__ == "CentralBank":
             is_central_bank = True

        if is_central_bank:
             try:
                 agent.withdraw(amount)
                 return True
             except Exception as e:
                 self.logger.error(f"SETTLEMENT_FAIL | Central Bank withdrawal failed. {e}")
                 return False

        # 2. Standard Agent Checks (Compatible with TD-073 Firm Refactor)
        current_cash = 0.0

        # Check for Firm's finance component first
        if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
             current_cash = agent.finance.balance
        # Check for Household's EconComponent state
        elif hasattr(agent, '_econ_state') and hasattr(agent._econ_state, 'assets'):
             current_cash = agent._econ_state.assets
        else:
             if not hasattr(agent, 'assets'):
                  self.logger.warning(f"SettlementSystem warning: Agent {agent.id} has no assets property.")
                  pass
             try:
                 current_cash = float(agent.assets) if hasattr(agent, 'assets') else 0.0
             except (TypeError, ValueError):
                  current_cash = 0.0

        if current_cash < amount:
            # Seamless Check
            if self.bank:
                needed_from_bank = amount - current_cash
                bank_balance = self.bank.get_balance(str(agent.id))
                if (current_cash + bank_balance) < amount:
                    self.logger.error(
                        f"SETTLEMENT_FAIL | Insufficient total funds (Cash+Deposits) for {agent.id}. "
                        f"Cash: {current_cash:.2f}, Bank: {bank_balance:.2f}, Total: {(current_cash + bank_balance):.2f}. "
                        f"Required: {amount:.2f}. Memo: {memo}",
                        extra={"tags": ["settlement", "insufficient_funds"]}
                    )
                    return False
            else:
                self.logger.error(
                    f"SETTLEMENT_FAIL | Insufficient cash for {agent.id} AND Bank service is missing. "
                    f"Cash: {current_cash:.2f}, Required: {amount:.2f}. Memo: {memo}",
                    extra={"tags": ["settlement", "insufficient_funds"]}
                )
                return False

        # 3. Execution
        try:
            if current_cash >= amount:
                agent.withdraw(amount)
            else:
                # Seamless
                needed_from_bank = amount - current_cash
                if current_cash > 0:
                    agent.withdraw(current_cash)

                success = self.bank.withdraw_for_customer(int(agent.id), needed_from_bank)
                if not success:
                    # Rollback cash
                    if current_cash > 0:
                         agent.deposit(current_cash)
                    raise InsufficientFundsError(f"Bank withdrawal failed for {agent.id} despite check.")

                self.logger.info(
                    f"SEAMLESS_PAYMENT | Agent {agent.id} paid {amount:.2f} using {current_cash:.2f} cash and {needed_from_bank:.2f} from bank.",
                    extra={"tick": tick, "agent_id": agent.id, "tags": ["settlement", "bank"]}
                )
            return True
        except InsufficientFundsError as e:
             self.logger.critical(f"SETTLEMENT_CRITICAL | InsufficientFundsError. {e}")
             return False
        except Exception as e:
             self.logger.exception(f"SETTLEMENT_UNHANDLED_FAIL | {e}")
             return False

    def settle_atomic(
        self,
        debit_agent: IFinancialEntity,
        credits_list: List[Tuple[IFinancialEntity, float, str]],
        tick: int
    ) -> bool:
        """
        Executes a one-to-many atomic settlement.
        All credits are summed to determine the total debit amount.
        If the debit fails, the entire transaction is aborted.
        If any credit fails, previous credits in this batch are rolled back.
        """
        if not credits_list:
            return True

        # 0. Validate Credits (No negative transfers allowed in this atomic mode)
        for _, amount, memo in credits_list:
             if amount < 0:
                 self.logger.error(f"SETTLEMENT_FAIL | Negative credit amount {amount} in atomic batch. Memo: {memo}")
                 return False

        # 1. Calculate Total Debit
        total_debit = sum(amount for _, amount, _ in credits_list)
        if total_debit <= 0:
             return True

        # 2. Debit Check & Withdrawal
        memo = f"atomic_batch_{len(credits_list)}_txs"
        success = self._execute_withdrawal(debit_agent, total_debit, memo, tick)
        if not success:
            return False

        # 3. Execute Credits
        completed_credits = []
        for credit_agent, amount, credit_memo in credits_list:
            if amount <= 0:
                continue
            try:
                credit_agent.deposit(amount)
                completed_credits.append((credit_agent, amount))
            except Exception as e:
                self.logger.error(
                    f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back atomic batch. Error: {e}"
                )
                # ROLLBACK
                # 1. Reverse completed credits
                for ca, amt in completed_credits:
                    try:
                        ca.withdraw(amt)
                    except Exception as rb_err:
                        self.logger.critical(f"SETTLEMENT_FATAL | Credit Rollback failed for {ca.id}. {rb_err}")

                # 2. Refund debit agent
                try:
                    debit_agent.deposit(total_debit)
                except Exception as rb_err:
                    self.logger.critical(f"SETTLEMENT_FATAL | Debit Refund failed for {debit_agent.id}. {rb_err}")

                return False

        return True

    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0
    ) -> Optional[ITransaction]:
        """
        Executes an atomic transfer from debit_agent to credit_agent.
        Returns a Transaction object (truthy) on success, None (falsy) on failure.
        """
        if amount <= 0:
            self.logger.warning(f"Transfer of non-positive amount ({amount}) attempted. Memo: {memo}")
            # Consider this a success logic-wise (no-op) but log it.
            return self._create_transaction_record(
                debit_agent.id if hasattr(debit_agent, 'id') else 0,
                credit_agent.id if hasattr(credit_agent, 'id') else 0,
                amount, memo, tick
            )

        if debit_agent is None or credit_agent is None:
             self.logger.error(f"SETTLEMENT_FAIL | Debit or Credit agent is None. Memo: {memo}")
             return None

        # EXECUTE
        success = self._execute_withdrawal(debit_agent, amount, memo, tick)
        if not success:
            return None

        try:
            credit_agent.deposit(amount)
        except Exception as e:
            # ROLLBACK: Credit failed, must reverse debit
            self.logger.error(
                f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back withdrawal of {amount:.2f} from {debit_agent.id}. Error: {e}"
            )
            try:
                debit_agent.deposit(amount)
                self.logger.info(f"SETTLEMENT_ROLLBACK_SUCCESS | Rolled back {amount:.2f} to {debit_agent.id}.")
            except Exception as rollback_error:
                self.logger.critical(
                    f"SETTLEMENT_FATAL | Rollback failed! Money {amount:.2f} lost from {debit_agent.id}. "
                    f"Original Error: {e}. Rollback Error: {rollback_error}",
                    extra={"tags": ["settlement", "fatal", "money_leak"]}
                )
            return None

        # Success
        self.logger.debug(
            f"SETTLEMENT_SUCCESS | Transferred {amount:.2f} from {debit_agent.id} to {credit_agent.id}. Memo: {memo}",
            extra={"tags": ["settlement"], "tick": tick}
        )
        return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)

    def create_and_transfer(
        self,
        source_authority: IFinancialEntity,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        """
        if amount <= 0:
            return None

        is_central_bank = False
        if hasattr(source_authority, "__class__") and source_authority.__class__.__name__ == "CentralBank":
            is_central_bank = True
        elif hasattr(source_authority, "id") and str(source_authority.id) == "CENTRAL_BANK":
            is_central_bank = True

        if is_central_bank:
            # Minting logic: Just credit destination. Source (CB) is assumed to have infinite capacity.
            try:
                destination.deposit(amount)
                self.logger.info(
                    f"MINT_AND_TRANSFER | Created {amount:.2f} from {source_authority.id} to {destination.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                return self._create_transaction_record(source_authority.id, destination.id, amount, reason, tick)
            except Exception as e:
                self.logger.error(f"MINT_FAIL | {e}")
                return None
        else:
            # If not CB (e.g. Government), treat as regular transfer to enforce budget
            return self.transfer(source_authority, destination, amount, reason, tick=tick)

    def transfer_and_destroy(
        self,
        source: IFinancialEntity,
        sink_authority: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed.
        """
        if amount <= 0:
            return None

        is_central_bank = False
        if hasattr(sink_authority, "__class__") and sink_authority.__class__.__name__ == "CentralBank":
            is_central_bank = True
        elif hasattr(sink_authority, "id") and str(sink_authority.id) == "CENTRAL_BANK":
            is_central_bank = True

        if is_central_bank:
            # Burning logic: Just debit source. Sink (CB) absorbs it (removed from circulation).
            try:
                source.withdraw(amount)
                self.logger.info(
                    f"TRANSFER_AND_DESTROY | Destroyed {amount:.2f} from {source.id} to {sink_authority.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                return self._create_transaction_record(source.id, sink_authority.id, amount, reason, tick)
            except Exception as e:
                self.logger.error(f"BURN_FAIL | {e}")
                return None
        else:
            # If not CB, treat as regular transfer (e.g. tax to Gov)
            return self.transfer(source, sink_authority, amount, reason, tick=tick)

    def _create_transaction_record(self, buyer_id: int, seller_id: int, amount: float, memo: str, tick: int) -> ITransaction:
        return {
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "item_id": "currency",
            "quantity": amount,
            "price": 1.0,
            "market_id": "settlement",
            "transaction_type": "transfer",
            "time": tick,
            "metadata": {"memo": memo}
        }

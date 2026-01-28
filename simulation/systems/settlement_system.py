from typing import Optional, Dict, Any, cast, TYPE_CHECKING
import logging

from simulation.finance.api import ISettlementSystem, ITransaction
from modules.finance.api import IFinancialEntity, InsufficientFundsError

if TYPE_CHECKING:
    from simulation.firms import Firm

class SettlementSystem(ISettlementSystem):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.

    ZERO-SUM PRINCIPLE:
    Every transfer MUST result in a net change of 0.0 across the system.
    Asset deduction from one agent must exactly equal asset addition to another.
    Money creation/destruction is ONLY allowed via the CentralBank (Minting Authority).
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.total_liquidation_losses: float = 0.0

    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.
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

        # 1. ATOMIC CHECK: Verify funds BEFORE any modification
        if debit_agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Debit agent is None. Memo: {memo}")
            return None

        if credit_agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Credit agent is None. Memo: {memo}")
            return None

        # Special Case: Central Bank (Minting Authority) can have negative assets (Fiat Issuer).
        is_central_bank = False
        if hasattr(debit_agent, "id") and str(debit_agent.id) == "CENTRAL_BANK":
             is_central_bank = True
        elif hasattr(debit_agent, "__class__") and debit_agent.__class__.__name__ == "CentralBank":
             is_central_bank = True

        if not is_central_bank:
            if hasattr(debit_agent, 'assets'):
                try:
                    current_assets = float(debit_agent.assets)
                    if current_assets < amount:
                        self.logger.error(
                            f"SETTLEMENT_FAIL | Insufficient funds for {debit_agent.id} to transfer {amount:.2f} to {credit_agent.id}. "
                            f"Assets: {current_assets:.2f}. Memo: {memo}",
                            extra={"tags": ["settlement", "insufficient_funds"]}
                        )
                        return None
                except (TypeError, ValueError):
                    self.logger.warning(
                        f"SettlementSystem warning: Agent {debit_agent.id} assets property is not float compatible."
                    )
            else:
                 self.logger.warning(f"SettlementSystem warning: Agent {debit_agent.id} has no assets property.")

        # 2. EXECUTE: Perform the debit and credit
        try:
            debit_agent.withdraw(amount)
            credit_agent.deposit(amount)

            self.logger.debug(
                f"SETTLEMENT_SUCCESS | Transferred {amount:.2f} from {debit_agent.id} to {credit_agent.id}. Memo: {memo}",
                extra={"tags": ["settlement"], "tick": tick}
            )
            return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)

        except InsufficientFundsError as e:
            self.logger.critical(
                f"SETTLEMENT_CRITICAL | Race condition or logic error. InsufficientFundsError during transfer. "
                f"Initial check passed but withdrawal failed. Details: {e}",
                extra={"tags": ["settlement", "error"]}
            )
            return None
        except Exception as e:
            self.logger.exception(
                 f"SETTLEMENT_UNHANDLED_FAIL | An unexpected error occurred during transfer. Details: {e}"
            )
            return None

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

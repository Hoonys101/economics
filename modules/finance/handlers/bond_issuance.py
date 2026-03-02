from typing import Any, Dict
import logging
import uuid
from modules.finance.api import ITransactionHandler, IBondMarketSystem, BondIssuanceRequestDTO
from modules.finance.transaction.api import ILedgerEngine
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class BondIssuanceHandler(ITransactionHandler):
    """
    Handler for Bond Issuance Transactions.
    Co-ordinates payment (via LedgerEngine) and asset creation (via BondMarketSystem).
    """
    def __init__(self, bond_market_system: IBondMarketSystem, ledger_engine: ILedgerEngine):
        self.bond_market_system = bond_market_system
        self.ledger_engine = ledger_engine
        self._active_issuances: Dict[str, BondIssuanceRequestDTO] = {}

    def validate(self, request: Any, context: Any) -> bool:
        if not isinstance(request, BondIssuanceRequestDTO):
            return False
        return True

    def execute(self, request: Any, context: Any) -> bool:
        if not isinstance(request, BondIssuanceRequestDTO):
            raise ValueError("Invalid request type for BondIssuanceHandler")

        transaction_id = request.transaction_id or str(uuid.uuid4())
        self._active_issuances[transaction_id] = request

        # 1. Calculate Total Cost
        total_cost = request.issue_price * request.quantity

        # 2. Execute Financial Transfer (Buyer -> Issuer)
        # Note: We assume DEFAULT_CURRENCY (USD) as BondIssuanceRequestDTO doesn't specify currency yet.
        ledger_result = self.ledger_engine.process_transaction(
            source_account_id=str(request.buyer_id),
            destination_account_id=str(request.issuer_id),
            amount=total_cost,
            currency=DEFAULT_CURRENCY,
            description=f"Bond Issuance: {request.quantity} units @ {request.issue_price/100:.2f}"
        )

        if ledger_result.status != 'COMPLETED':
            logger.error(f"Bond Issuance Payment Failed: {ledger_result.message}")
            # We return False (or raise exception depending on protocol contract - currently Any)
            # Raising exception is safer for now to propagate error message
            raise ValueError(f"Bond Issuance Payment Failed: {ledger_result.message}")

        # 3. Execute Asset Creation (Bond Market System)
        try:
            if not self.bond_market_system.issue_bond(request):
                raise ValueError("Bond Market System returned False")
        except Exception as e:
            # ROLLBACK Payment!
            logger.warning(f"Bond Creation Failed: {e}. Initiating Payment Rollback.")

            try:
                reverse_result = self.ledger_engine.process_transaction(
                    source_account_id=str(request.issuer_id),
                    destination_account_id=str(request.buyer_id),
                    amount=total_cost,
                    currency=DEFAULT_CURRENCY,
                    description=f"ROLLBACK: Bond Issuance Failed"
                )
                if reverse_result.status != 'COMPLETED':
                    logger.critical(f"CRITICAL: Rollback failed for Bond Issuance! Money trapped in Issuer {request.issuer_id}. Error: {reverse_result.message}")
            except Exception as rb_error:
                logger.critical(f"CRITICAL: Rollback exception for Bond Issuance! Money trapped. Error: {rb_error}")

            raise ValueError(f"Bond Issuance Failed during asset creation: {e}")

        return True

    def rollback(self, transaction_id: str, context: Any) -> bool:
        request = self._active_issuances.get(transaction_id)
        if not request:
            logger.warning(f"Rollback requested for unknown transaction_id: {transaction_id}")
            return False

        total_cost = request.issue_price * request.quantity

        try:
            # Reverse payment
            reverse_result = self.ledger_engine.process_transaction(
                source_account_id=str(request.issuer_id),
                destination_account_id=str(request.buyer_id),
                amount=total_cost,
                currency=DEFAULT_CURRENCY,
                description=f"ROLLBACK: Bond Issuance Reversal for {transaction_id}"
            )
            if reverse_result.status != 'COMPLETED':
                logger.critical(f"CRITICAL: Rollback failed for Bond Issuance! Money trapped in Issuer {request.issuer_id}. Error: {reverse_result.message}")
                return False

            # Cancel bond
            bond_id = f"BOND_{transaction_id}"
            if not self.bond_market_system.cancel_bond(bond_id):
                logger.error(f"Failed to cancel bond {bond_id} in BondMarketSystem.")
                return False

            # Clean up
            del self._active_issuances[transaction_id]
            logger.info(f"Successfully rolled back Bond Issuance {transaction_id}.")
            return True

        except Exception as e:
            logger.critical(f"CRITICAL: Rollback exception for Bond Issuance {transaction_id}. Error: {e}")
            return False

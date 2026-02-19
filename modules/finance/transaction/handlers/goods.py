from typing import Any
import logging
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from simulation.systems.api import ISpecializedTransactionHandler
from modules.finance.utils.currency_math import round_to_pennies
from modules.finance.transaction.handlers.protocols import ISolvent, ITaxCollector, IConsumptionTracker

logger = logging.getLogger(__name__)

class GoodsTransactionHandler(ISpecializedTransactionHandler):
    """
    Handles 'goods' transactions using atomic escrow and sales tax logic.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, state: SimulationState) -> bool:
        settlement = state.settlement_system
        government = state.government
        escrow_agent = state.escrow_agent
        config = state.config_module
        sys_logger = state.logger or logger

        if not settlement:
            sys_logger.error("GoodsTransactionHandler: Settlement system not available in state.")
            return False

        if not escrow_agent:
            sys_logger.error("GoodsTransactionHandler: Escrow agent not available in state.")
            return False

        if not government:
            sys_logger.error("GoodsTransactionHandler: Government not available in state.")
            return False

        trade_value = int(tx.quantity * tx.price)
        if tx.total_pennies > 0:
            trade_value = tx.total_pennies

        # Sales Tax Logic
        sales_tax_rate = getattr(config, "SALES_TAX_RATE", 0.05)
        tax_amount = round_to_pennies(trade_value * sales_tax_rate)
        total_cost = trade_value + tax_amount

        # Solvency Check (Legacy compatibility)
        # Using Protocol check instead of hasattr
        if isinstance(buyer, ISolvent):
             try:
                 if buyer.assets < total_cost:
                     buyer.check_solvency(government)
             except Exception:
                 pass

        # --- 3-Step Escrow Logic (Atomic) ---
        # 1. Secure Total Amount in Escrow
        memo_escrow = f"escrow_hold:{tx.item_id}"
        escrow_success = settlement.transfer(
            buyer,
            escrow_agent,
            total_cost,
            memo_escrow
        )

        if not escrow_success:
            return False

        # 2. Distribute Funds from Escrow
        try:
            # 2a. Pay Seller
            memo_trade = f"goods_trade:{tx.item_id}"
            trade_success = settlement.transfer(
                escrow_agent,
                seller,
                trade_value,
                memo_trade
            )

            if not trade_success:
                # Critical Failure: Funds stuck in escrow. Rollback buyer.
                sys_logger.critical(f"ESCROW_FAIL | Trade transfer to seller failed. Rolling back {total_cost} to buyer {buyer.id}.")
                settlement.transfer(escrow_agent, buyer, total_cost, "escrow_reversal:trade_failure")
                return False

            # 2b. Pay Tax to Government
            if tax_amount > 0:
                memo_tax = f"sales_tax:{tx.item_id}"
                # Push tax to Government via Settlement
                tax_success = settlement.transfer(
                    escrow_agent,
                    government,
                    tax_amount,
                    memo_tax
                )

                if not tax_success:
                    # Critical Failure: Tax transfer failed. Rollback everything.
                    sys_logger.critical(f"ESCROW_FAIL | Tax transfer to government failed. Rolling back trade and escrow.")
                    # Revert seller payment
                    settlement.transfer(seller, escrow_agent, trade_value, "reversal:tax_failure")
                    # Return all to buyer
                    settlement.transfer(escrow_agent, buyer, total_cost, "escrow_reversal:tax_failure")
                    return False

                # Explicitly record tax revenue since we bypassed collect_tax
                if isinstance(government, ITaxCollector):
                    government.record_revenue({
                        "success": True,
                        "amount_collected": tax_amount,
                        "tax_type": f"sales_tax_{tx.transaction_type}",
                        "payer_id": buyer.id,
                        "payee_id": government.id,
                        "error_message": None
                    })

            # Track Consumption Expenditure (Confirmed Success)
            if isinstance(buyer, IConsumptionTracker):
                buyer.add_consumption_expenditure(total_cost, item_id=tx.item_id)

            return True

        except Exception as e:
            sys_logger.exception(f"ESCROW_EXCEPTION | Unexpected error during distribution: {e}")
            return False

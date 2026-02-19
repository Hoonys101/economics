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
        config = state.config_module
        sys_logger = state.logger or logger

        if not settlement:
            sys_logger.error("GoodsTransactionHandler: Settlement system not available in state.")
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

        # --- Atomic Settlement Logic ---
        try:
            credits_list = []

            # 1. Seller Payment
            memo_trade = f"goods_trade:{tx.item_id}"
            credits_list.append((seller, trade_value, memo_trade))

            # 2. Tax Payment
            if tax_amount > 0:
                memo_tax = f"sales_tax:{tx.item_id}"
                credits_list.append((government, tax_amount, memo_tax))

            # Execute Atomic Settlement
            success = settlement.settle_atomic(
                debit_agent=buyer,
                credits_list=credits_list,
                tick=tx.time
            )

            if not success:
                return False

            # --- Post-Transaction Side Effects ---

            # Record Tax Revenue
            if tax_amount > 0 and isinstance(government, ITaxCollector):
                government.record_revenue({
                    "success": True,
                    "amount_collected": tax_amount,
                    "tax_type": f"sales_tax_{tx.transaction_type}",
                    "payer_id": buyer.id,
                    "payee_id": government.id,
                    "error_message": None
                })

            # Track Consumption Expenditure
            if isinstance(buyer, IConsumptionTracker):
                buyer.add_consumption_expenditure(total_cost, item_id=tx.item_id)

            return True

        except Exception as e:
            sys_logger.exception(f"SETTLEMENT_EXCEPTION | Unexpected error during atomic settlement: {e}")
            return False

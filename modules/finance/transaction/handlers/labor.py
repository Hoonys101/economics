from typing import Any
import logging
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from simulation.systems.api import ISpecializedTransactionHandler
from modules.finance.utils.currency_math import round_to_pennies
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE
from modules.finance.transaction.handlers.protocols import ITaxCollector, IIncomeTracker

logger = logging.getLogger(__name__)

class LaborTransactionHandler(ISpecializedTransactionHandler):
    """
    Handles 'labor' and 'research_labor' transactions, including income tax withholding.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, state: SimulationState) -> bool:
        settlement = state.settlement_system
        government = state.government
        config = state.config_module
        sys_logger = state.logger or logger
        current_time = state.time

        if not settlement:
            sys_logger.error("LaborTransactionHandler: Settlement system not available in state.")
            return False

        if not government:
            sys_logger.error("LaborTransactionHandler: Government not available in state.")
            return False

        # Calculate trade value (SSoT: total_pennies)
        trade_value = 0
        if tx.total_pennies > 0:
            trade_value = tx.total_pennies
        else:
            trade_value = int(tx.quantity * tx.price)

        # Market Data Access
        goods_market_data = state.market_data.get("goods_market", {}) if state.market_data else {}

        # Income Tax Logic
        tax_payer = getattr(config, "INCOME_TAX_PAYER", "HOUSEHOLD")

        # Standardized price handling for survival cost calculation
        avg_food_price_pennies = 0
        if "basic_food_current_sell_price" in goods_market_data:
            val = goods_market_data["basic_food_current_sell_price"]
            if isinstance(val, float):
                 avg_food_price_pennies = round_to_pennies(val * 100)
            else:
                 avg_food_price_pennies = int(val)
        else:
            val = getattr(config, "GOODS_INITIAL_PRICE", {}).get("basic_food", DEFAULT_BASIC_FOOD_PRICE)
            if isinstance(val, float):
                 avg_food_price_pennies = round_to_pennies(val * 100)
            else:
                 avg_food_price_pennies = int(val)

        daily_food_need = getattr(config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)

        # Survival cost in pennies, max 1000 pennies ($10) as baseline protection
        survival_cost = int(max(avg_food_price_pennies * daily_food_need, 1000))

        # Calculate Tax (Standardized method call on Gov)
        # Note: calculate_income_tax is on Government agent.
        tax_amount = 0
        if isinstance(government, ITaxCollector):
            tax_amount = int(government.calculate_income_tax(trade_value, survival_cost))
        else:
             sys_logger.warning("LaborTransactionHandler: Government does not implement ITaxCollector.")

        if tax_payer == "FIRM":
            # Firm pays Wage to Household AND Tax to Gov Atomically
            credits = [(seller, trade_value, f"labor_wage:{tx.transaction_type}")]
            if tax_amount > 0:
                credits.append((government, tax_amount, "income_tax_firm"))

            success = settlement.settle_atomic(
                debit_agent=buyer,
                credits_list=credits,
                tick=current_time
            )

            if success and tax_amount > 0 and isinstance(government, ITaxCollector):
                government.record_revenue({
                    "success": True,
                    "amount_collected": tax_amount,
                    "tax_type": "income_tax_firm",
                    "payer_id": buyer.id,
                    "payee_id": government.id
                })
        else:
            # Household pays tax (Withholding model)
            # Pay GROSS wage to household
            success = settlement.transfer(buyer, seller, trade_value, f"labor_wage_gross:{tx.transaction_type}")
            if success and tax_amount > 0:
                # Then collect tax from household
                tax_success = settlement.settle_atomic(
                    debit_agent=seller,
                    credits_list=[(government, tax_amount, "income_tax_household")],
                    tick=current_time
                )

                if tax_success and isinstance(government, ITaxCollector):
                    government.record_revenue({
                        "success": True,
                        "amount_collected": tax_amount,
                        "tax_type": "income_tax_household",
                        "payer_id": seller.id,
                        "payee_id": government.id
                    })

        if success and isinstance(seller, IIncomeTracker):
            seller.add_labor_income(trade_value)

        return success

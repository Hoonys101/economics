from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Any, Dict
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.dtos.context_dtos import FinancialTransactionContext

if TYPE_CHECKING:
    from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
    from simulation.components.engines.hr_engine import HREngine
    from simulation.components.engines.finance_engine import FinanceEngine
    from simulation.components.engines.production_engine import ProductionEngine
    from simulation.components.engines.sales_engine import SalesEngine
    from modules.finance.wallet.wallet import Wallet
    from simulation.finance.api import ISettlementSystem
    from simulation.dtos.config_dtos import FirmConfigDTO
    from modules.system.api import MarketContextDTO
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

@dataclass
class FirmExecutionContext:
    firm_id: int
    wallet: Wallet
    production_state: ProductionState
    finance_state: FinanceState
    hr_state: HRState
    sales_state: SalesState
    production_engine: ProductionEngine
    finance_engine: FinanceEngine
    hr_engine: HREngine
    sales_engine: SalesEngine
    settlement_system: Optional[ISettlementSystem]
    config: FirmConfigDTO
    logger: logging.Logger
    firm_proxy: Any = None # Needed for HREngine.fire_employee and Settlement

class FirmOrderProcessor:
    def process_order(self, order: Order, context: FirmExecutionContext, government: Optional[Any], current_time: int, market_context: Optional[MarketContextDTO] = None) -> None:
        """
        Command Bus: Routes internal orders to the correct engine.
        Logic extracted from Firm._execute_internal_order.
        """
        def get_amount(o: Order) -> float:
            return o.monetary_amount['amount'] if o.monetary_amount else o.quantity

        def get_currency(o: Order) -> CurrencyCode:
             return o.monetary_amount['currency'] if o.monetary_amount else DEFAULT_CURRENCY

        gov_id = government.id if government else None

        fin_ctx = FinancialTransactionContext(
            government_id=gov_id,
            tax_rates={},
            market_context=market_context or {},
            shareholder_registry=None
        )

        if order.order_type == "SET_TARGET":
            context.production_state.production_target = order.quantity
            context.logger.info(f"INTERNAL_EXEC | Firm {context.firm_id} set production target to {order.quantity:.1f}")

        elif order.order_type == "INVEST_AUTOMATION":
            amount = get_amount(order)
            tx = context.finance_engine.invest_in_automation(
                context.finance_state, context.firm_id, context.wallet, amount, fin_ctx, current_time
            )
            if tx:
                if context.settlement_system and context.settlement_system.transfer(context.firm_proxy, government, amount, "Automation", currency=tx.currency):
                    gained = context.production_engine.invest_in_automation(
                        context.production_state, amount, context.config.automation_cost_per_pct
                    )
                    context.finance_engine.record_expense(context.finance_state, amount, tx.currency)
                    context.logger.info(f"INTERNAL_EXEC | Firm {context.firm_id} invested {amount:.1f} in automation (+{gained:.4f}).")

        elif order.order_type == "PAY_TAX":
            amount = get_amount(order)
            currency = get_currency(order)
            reason = order.item_id

            tx = context.finance_engine.pay_ad_hoc_tax(
                context.finance_state, context.firm_id, context.wallet, amount, currency, reason, fin_ctx, current_time
            )
            if tx:
                if context.settlement_system and context.settlement_system.transfer(context.firm_proxy, government, amount, reason, currency=currency):
                    context.finance_engine.record_expense(context.finance_state, amount, currency)

        elif order.order_type == "INVEST_RD":
            amount = get_amount(order)
            tx = context.finance_engine.invest_in_rd(
                context.finance_state, context.firm_id, context.wallet, amount, fin_ctx, current_time
            )
            if tx:
                if context.settlement_system and context.settlement_system.transfer(context.firm_proxy, government, amount, "R&D", currency=tx.currency):
                    context.finance_engine.record_expense(context.finance_state, amount, tx.currency)
                    revenue = context.finance_state.last_revenue
                    if context.production_engine.execute_rd_outcome(context.production_state, context.hr_state, revenue, amount, current_time):
                        context.logger.info(f"INTERNAL_EXEC | Firm {context.firm_id} R&D SUCCESS (Budget: {amount:.1f})")

        elif order.order_type == "INVEST_CAPEX":
            amount = get_amount(order)
            tx = context.finance_engine.invest_in_capex(
                context.finance_state, context.firm_id, context.wallet, amount, fin_ctx, current_time
            )
            if tx:
                if context.settlement_system and context.settlement_system.transfer(context.firm_proxy, government, amount, "CAPEX", currency=tx.currency):
                    context.production_engine.invest_in_capex(context.production_state, amount, context.config.capital_to_output_ratio)
                    context.logger.info(f"INTERNAL_EXEC | Firm {context.firm_id} invested {amount:.1f} in CAPEX.")

        elif order.order_type == "SET_DIVIDEND":
            context.finance_state.dividend_rate = order.quantity

        elif order.order_type == "SET_PRICE":
            # Just logs logic, actual pricing happens in post_ask
            pass

        elif order.order_type == "FIRE":
            context.hr_engine.fire_employee(
                context.hr_state, context.firm_id, context.firm_proxy, context.wallet, context.settlement_system, order.target_agent_id, order.price
            )

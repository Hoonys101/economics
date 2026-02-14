from __future__ import annotations
from typing import List, Optional, Any, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.firm.api import (
    AssetManagementInputDTO, AssetManagementResultDTO,
    RDInputDTO, RDResultDTO
)
from simulation.models import Order
from simulation.dtos import FiscalContext
from simulation.dtos.context_dtos import FinancialTransactionContext
from simulation.components.engines.asset_management_engine import AssetManagementEngine
from simulation.components.engines.rd_engine import RDEngine

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class FirmActionExecutor:
    """
    Executes internal orders for a Firm.
    Delegates to stateless engines and updates firm state.
    """
    def execute(
        self,
        firm: 'Firm',
        orders: List[Order],
        fiscal_context: FiscalContext,
        current_time: int,
        market_context: Optional[MarketContextDTO] = None
    ) -> None:
        """
        Orchestrates internal orders by delegating to specialized engines.
        Moved from Firm.execute_internal_orders.
        """
        snapshot = firm.get_snapshot_dto()
        government = fiscal_context.government if fiscal_context else None
        gov_id = government.id if government else None

        fin_ctx = FinancialTransactionContext(
            government_id=gov_id,
            tax_rates={},
            market_context=market_context or {},
            shareholder_registry=None
        )

        def get_amount(o: Order) -> int:
            val = o.monetary_amount['amount_pennies'] if o.monetary_amount else o.quantity
            return int(val)

        def get_currency(o: Order) -> CurrencyCode:
             return o.monetary_amount['currency'] if o.monetary_amount else DEFAULT_CURRENCY

        for order in orders:
            if order.market_id != "internal":
                continue

            amount = get_amount(order)

            # --- Delegate to AssetManagementEngine ---
            if order.order_type in ["INVEST_AUTOMATION", "INVEST_CAPEX"]:
                investment_type = "AUTOMATION" if order.order_type == "INVEST_AUTOMATION" else "CAPEX"

                # Check funds
                if firm.wallet.get_balance(DEFAULT_CURRENCY) < amount:
                    logger.warning(f"INTERNAL_EXEC | Firm {firm.id} failed to invest {amount} (Insufficient Funds).")
                    continue

                asset_input = AssetManagementInputDTO(
                    firm_snapshot=snapshot,
                    investment_type=investment_type,
                    investment_amount=amount
                )

                # Using engine from firm instance
                asset_result: AssetManagementResultDTO = firm.asset_management_engine.invest(asset_input)

                if asset_result.success:
                    # Transfer funds
                    if firm.settlement_system and firm.settlement_system.transfer(firm, government, int(asset_result.actual_cost), order.order_type):
                        # Apply state changes
                        firm.production_state.automation_level += asset_result.automation_level_increase
                        firm.production_state.capital_stock += asset_result.capital_stock_increase

                        firm.record_expense(int(asset_result.actual_cost), DEFAULT_CURRENCY)
                        logger.info(f"INTERNAL_EXEC | Firm {firm.id} invested {asset_result.actual_cost} in {order.order_type}.")
                    else:
                         logger.warning(f"INTERNAL_EXEC | Firm {firm.id} failed transfer for {order.order_type}.")
                else:
                    logger.warning(f"INTERNAL_EXEC | Firm {firm.id} failed {order.order_type}: {asset_result.message}")

            # --- Delegate to RDEngine ---
            elif order.order_type == "INVEST_RD":
                # Check funds
                if firm.wallet.get_balance(DEFAULT_CURRENCY) < amount:
                    logger.warning(f"INTERNAL_EXEC | Firm {firm.id} failed to invest R&D {amount} (Insufficient Funds).")
                    continue

                rd_input = RDInputDTO(firm_snapshot=snapshot, investment_amount=amount, current_time=current_time)
                rd_result: RDResultDTO = firm.rd_engine.research(rd_input)

                if firm.settlement_system and firm.settlement_system.transfer(firm, government, amount, "R&D"):
                    firm.record_expense(amount, DEFAULT_CURRENCY)

                    if rd_result.success:
                         firm.production_state.base_quality += rd_result.quality_improvement
                         firm.production_state.productivity_factor *= rd_result.productivity_multiplier_change
                         firm.production_state.research_history["success_count"] += 1
                         firm.production_state.research_history["last_success_tick"] = current_time
                         logger.info(f"INTERNAL_EXEC | Firm {firm.id} R&D SUCCESS (Budget: {amount:.1f})")

                    firm.production_state.research_history["total_spent"] += amount

            # --- Existing Handlers (HR, Finance) ---
            elif order.order_type == "SET_TARGET":
                firm.production_state.production_target = order.quantity
                logger.info(f"INTERNAL_EXEC | Firm {firm.id} set production target to {order.quantity:.1f}")

            elif order.order_type == "PAY_TAX":
                amount = get_amount(order)
                currency = get_currency(order)
                reason = order.item_id

                tx = firm.finance_engine.pay_ad_hoc_tax(
                    firm.finance_state, firm.id, firm.wallet.get_all_balances(), amount, currency, reason, fin_ctx, current_time
                )
                if tx:
                    if firm.settlement_system and firm.settlement_system.transfer(firm, government, amount, reason, currency=currency):
                        firm.finance_engine.record_expense(firm.finance_state, amount, currency)

            elif order.order_type == "SET_DIVIDEND":
                firm.finance_state.dividend_rate = order.quantity

            elif order.order_type == "SET_PRICE":
                pass

            elif order.order_type == "FIRE":
                 tx = firm.hr_engine.create_fire_transaction(
                    firm.hr_state, firm.id, firm.wallet.get_balance(DEFAULT_CURRENCY), order.target_agent_id, order.price, current_time
                 )
                 if tx:
                    employee = next((e for e in firm.hr_state.employees if e.id == order.target_agent_id), None)
                    if employee and firm.settlement_system and firm.settlement_system.transfer(firm, employee, int(tx.price), "Severance", currency=tx.currency):
                        firm.hr_engine.finalize_firing(firm.hr_state, order.target_agent_id)
                        logger.info(f"INTERNAL_EXEC | Firm {firm.id} fired employee {order.target_agent_id}.")
                    else:
                        logger.warning(f"INTERNAL_EXEC | Firm {firm.id} failed to fire {order.target_agent_id} (transfer failed).")

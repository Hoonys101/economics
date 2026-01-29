from __future__ import annotations
from typing import List, Optional, Any, Dict
import logging

from simulation.models import Order
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.ai.firm_system2_planner import FirmSystem2Planner

# Import new managers
from simulation.decisions.firm.finance_manager import FinanceManager
from simulation.decisions.firm.hr_manager import HRManager
from simulation.decisions.firm.operations_manager import OperationsManager
from simulation.decisions.firm.sales_manager import SalesManager

logger = logging.getLogger(__name__)

class CorporateManager:
    """
    CEO Module (WO-027).
    Refactored for WO-142 Departmentalization.
    Orchestrates specialized managers (HR, Finance, Ops, Sales).
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.system2_planner: Optional[FirmSystem2Planner] = None

        # Instantiate managers
        self.finance_manager = FinanceManager()
        self.hr_manager = HRManager()
        self.operations_manager = OperationsManager()
        self.sales_manager = SalesManager()

    def realize_ceo_actions(
        self,
        firm: FirmStateDTO,
        context: DecisionContext,
        action_vector: FirmActionVector
    ) -> List[Order]:
        """
        Main entry point. Orchestrates all channel executions using pure DTOs.
        Returns a list of Orders (External and Internal).
        """
        orders: List[Order] = []

        # Phase 21: System 2 Strategic Guidance
        if self.system2_planner is None:
             self.system2_planner = FirmSystem2Planner(None, self.config_module)

        guidance = self.system2_planner.project_future(context.current_time, context.market_data, firm)

        # 1. Finance (Dividends, Debt)
        financial_plan = self.finance_manager.formulate_plan(
            context,
            dividend_aggressiveness=action_vector.dividend_aggressiveness,
            debt_aggressiveness=action_vector.debt_aggressiveness
        )
        orders.extend(financial_plan.orders)

        # 2. HR (Hiring)
        hr_plan = self.hr_manager.formulate_plan(
            context,
            hiring_aggressiveness=action_vector.hiring_aggressiveness
        )
        orders.extend(hr_plan.orders)

        # 3. Operations (Production, Procurement, Automation, R&D, Capex)
        ops_plan = self.operations_manager.formulate_plan(
            context,
            capital_aggressiveness=action_vector.capital_aggressiveness,
            rd_aggressiveness=action_vector.rd_aggressiveness,
            guidance=guidance
        )
        orders.extend(ops_plan.orders)
        
        # 4. Sales (Pricing)
        sales_plan = self.sales_manager.formulate_plan(
            context,
            sales_aggressiveness=action_vector.sales_aggressiveness
        )
        orders.extend(sales_plan.orders)

        return orders

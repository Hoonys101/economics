import pytest
from unittest.mock import MagicMock, patch
from simulation.firms import Firm
from modules.firm.api import (
    FinanceDecisionInputDTO, BudgetPlanDTO,
    HRDecisionInputDTO, HRDecisionOutputDTO,
    FirmSnapshotDTO, HRIntentDTO, SalesIntentDTO,
    IFinanceEngine, IHREngine, IProductionEngine, ISalesEngine, IPricingEngine,
    IAssetManagementEngine, IRDEngine, IBrandEngine
)
from simulation.components.engines.hr_engine import HREngine
from simulation.models import Order
from simulation.dtos import DecisionInputDTO
from modules.simulation.dtos.api import FirmConfigDTO

class TestFirmSurgicalSeparation:

    @pytest.fixture
    def mock_firm(self):
        # Create a Firm with mocked engines
        mock_core_config = MagicMock()
        mock_core_config.id = 1
        mock_core_config.name = "TestFirm"
        mock_core_config.initial_needs = {}

        mock_decision_engine = MagicMock()
        mock_config_dto = MagicMock(spec=FirmConfigDTO)
        # Populate required fields
        mock_config_dto.firm_min_production_target = 10.0
        mock_config_dto.ipo_initial_shares = 1000
        mock_config_dto.dividend_rate = 0.1
        mock_config_dto.profit_history_ticks = 10
        mock_config_dto.default_unit_cost = 10
        mock_config_dto.goods = {}
        mock_config_dto.labor_alpha = 0.5
        mock_config_dto.automation_labor_reduction = 0.5
        mock_config_dto.labor_elasticity_min = 0.1
        mock_config_dto.capital_depreciation_rate = 0.01

        firm = Firm(
            core_config=mock_core_config,
            engine=mock_decision_engine,
            specialization="food",
            productivity_factor=1.0,
            config_dto=mock_config_dto
        )

        # Inject Mock Engines
        firm.finance_engine = MagicMock(spec=IFinanceEngine)
        firm.hr_engine = MagicMock(spec=HREngine)
        firm.production_engine = MagicMock(spec=IProductionEngine)
        firm.sales_engine = MagicMock(spec=ISalesEngine)
        firm.pricing_engine = MagicMock(spec=IPricingEngine)
        firm.asset_management_engine = MagicMock(spec=IAssetManagementEngine)
        firm.rd_engine = MagicMock(spec=IRDEngine)
        firm.brand_engine = MagicMock(spec=IBrandEngine)

        firm.action_executor = MagicMock() # Mock execute_internal_orders delegate

        # Ensure execute_internal_orders delegates to action_executor or we mock execute_internal_orders directly
        firm.execute_internal_orders = MagicMock()

        # Ensure firm has enough capital to pass any internal sanity checks
        firm.wallet.load_balances({"USD": 10000000})

        return firm

    def test_make_decision_orchestrates_engines(self, mock_firm):
        # Setup Inputs
        input_dto = MagicMock(spec=DecisionInputDTO)
        input_dto.current_time = 10
        input_dto.market_snapshot = MagicMock()
        # Ensure market_signals is empty or safe
        input_dto.market_snapshot.market_signals = {}

        # Mock labor market stats to allow comparison
        # MagicMock > 0 fails, so we need to set avg_wage to a real number
        input_dto.market_snapshot.labor = MagicMock()
        input_dto.market_snapshot.labor.avg_wage = 10.0

        input_dto.goods_data = []
        input_dto.market_data = {}

        # Setup Engine Returns
        mock_budget = MagicMock(spec=BudgetPlanDTO)
        mock_budget.labor_budget_pennies = 10000
        mock_firm.finance_engine.plan_budget.return_value = mock_budget

        # Use real DTO to satisfy type checks in Firm
        mock_hr_result = HRIntentDTO(
            hiring_target=1,
            wage_updates={},
            fire_employee_ids=[]
        )

        # Explicitly ensure hr_engine is a fresh MagicMock
        mock_firm.hr_engine = MagicMock()
        # Use return_value to ensure return value is respected
        mock_firm.hr_engine.decide_workforce.return_value = mock_hr_result

        # Configure Sales Engine (Crucial: Must return a list for sales_orders)
        mock_sales_result = MagicMock(spec=SalesIntentDTO)
        mock_sales_result.sales_orders = []
        mock_sales_result.price_adjustments = {}
        mock_sales_result.marketing_spend_pennies = 0
        mock_sales_result.new_marketing_budget_rate = 0.05
        mock_firm.sales_engine.decide_pricing.return_value = mock_sales_result

        # Configure Pricing Engine Mock
        mock_pricing_result = MagicMock()
        mock_pricing_result.new_price = 1000
        mock_pricing_result.shadow_price = 1000.0
        mock_pricing_result.demand = 0.0
        mock_pricing_result.supply = 0.0
        mock_pricing_result.excess_demand_ratio = 0.0
        mock_firm.pricing_engine.calculate_price.return_value = mock_pricing_result

        # Configure Sales Engine dynamic pricing check (side effect)
        def side_effect_dynamic_pricing(state, orders, *args, **kwargs):
            from modules.firm.api import DynamicPricingResultDTO
            return DynamicPricingResultDTO(orders=orders, price_updates={})
        mock_firm.sales_engine.check_and_apply_dynamic_pricing.side_effect = side_effect_dynamic_pricing

        # Configure Production Engine (Procurement)
        from modules.firm.api import ProcurementIntentDTO
        procurement_order = Order(
            agent_id=1, side="BUY", item_id="wood", quantity=10,
            price_pennies=500, market_id="wood",
            price_limit=5.0
        )
        mock_procurement_intent = MagicMock(spec=ProcurementIntentDTO)
        mock_procurement_intent.purchase_orders = [procurement_order]
        mock_firm.production_engine.decide_procurement.return_value = mock_procurement_intent

        # Act
        external_orders, tactic = mock_firm.make_decision(input_dto)

        # Assert: Finance Engine called
        assert mock_firm.finance_engine.plan_budget.called
        call_args_fin = mock_firm.finance_engine.plan_budget.call_args[0][0]
        assert isinstance(call_args_fin, FinanceDecisionInputDTO)
        assert call_args_fin.current_tick == 10

        # Assert: HR Engine called
        assert mock_firm.hr_engine.decide_workforce.called

        # Assert: Production Engine called
        assert mock_firm.production_engine.decide_procurement.called

        # Assert: Internal execution called
        mock_firm.execute_internal_orders.assert_called_once()
        executed_orders = mock_firm.execute_internal_orders.call_args[0][0]
        # Should be a list, not a Mock
        assert isinstance(executed_orders, list)

        # Assert: Orders Merged
        # external_orders should contain generated HR order and procurement_order
        assert len(external_orders) == 2
        assert procurement_order in external_orders
        # Verify HR order presence
        hr_orders = [o for o in external_orders if o.market_id == 'labor']
        assert len(hr_orders) == 1
        assert hr_orders[0].side == 'BUY'

    def test_state_persistence_across_ticks(self, mock_firm):
        """
        Verify that Firm updates its internal state based on previous actions,
        simulating persistence across ticks.
        """
        # 1. Initial State
        mock_firm.hr_state.employees = []
        mock_firm.hr_state.employee_wages = {}

        # Test Case: Firing
        fire_order = Order(
            agent_id=1, side="FIRE", item_id="internal", quantity=1,
            price_pennies=1000, market_id="internal", target_agent_id=101,
            price_limit=10.0
        )

        # Inject employee to fire
        employee_mock = MagicMock()
        employee_mock.id = 101
        mock_firm.hr_state.employees = [employee_mock]
        mock_firm.hr_state.employee_wages = {101: 1000}

        # Setup inputs
        fiscal_context = MagicMock()
        current_time = 10

        # We need to use the real action_executor logic
        from modules.firm.orchestrators.firm_action_executor import FirmActionExecutor
        real_action_executor = FirmActionExecutor()

        # Setup mocks for what FirmActionExecutor calls on the firm
        mock_tx = MagicMock()
        mock_tx.price = 1000
        mock_tx.currency = "USD"
        mock_firm.hr_engine.create_fire_transaction.return_value = mock_tx

        # Mock Settlement System
        mock_settlement = MagicMock()
        mock_settlement.transfer.return_value = True
        mock_firm.settlement_system = mock_settlement

        # Execute using real executor directly (since mock_firm.execute_internal_orders is mocked in fixture)
        real_action_executor.execute(mock_firm, [fire_order], fiscal_context, current_time)

        # Assertions
        # 1. create_fire_transaction called
        mock_firm.hr_engine.create_fire_transaction.assert_called()

        # 2. finalize_firing called
        mock_firm.hr_engine.finalize_firing.assert_called_with(mock_firm.hr_state, 101)

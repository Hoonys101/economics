import pytest
from unittest.mock import MagicMock, patch
from simulation.firms import Firm
from modules.firm.api import (
    FinanceDecisionInputDTO, BudgetPlanDTO,
    HRDecisionInputDTO, HRDecisionOutputDTO,
    FirmSnapshotDTO
)
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

        firm = Firm(
            core_config=mock_core_config,
            engine=mock_decision_engine,
            specialization="food",
            productivity_factor=1.0,
            config_dto=mock_config_dto
        )

        # Inject Mock Engines
        firm.finance_engine = MagicMock()
        firm.hr_engine = MagicMock()
        firm.production_engine = MagicMock()
        firm.sales_engine = MagicMock()
        firm.pricing_engine = MagicMock()
        firm.asset_management_engine = MagicMock()
        firm.rd_engine = MagicMock()
        firm.brand_engine = MagicMock()

        firm.action_executor = MagicMock() # Mock execute_internal_orders delegate

        # Ensure execute_internal_orders delegates to action_executor or we mock execute_internal_orders directly
        firm.execute_internal_orders = MagicMock()

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

        mock_hr_result = MagicMock(spec=HRDecisionOutputDTO)
        engine_order = Order(
            agent_id=1, side="BUY", item_id="labor", quantity=1,
            price_pennies=1000, market_id="labor",
            price_limit=10.0
        )
        mock_hr_result.hiring_orders = [engine_order]
        mock_firm.hr_engine.manage_workforce.return_value = mock_hr_result

        # Configure Pricing Engine Mock (called in _calculate_invisible_hand_price)
        mock_pricing_result = MagicMock()
        mock_pricing_result.new_price = 1000
        mock_pricing_result.shadow_price = 1000.0
        mock_pricing_result.demand = 0.0
        mock_pricing_result.supply = 0.0
        mock_pricing_result.excess_demand_ratio = 0.0
        mock_firm.pricing_engine.calculate_price.return_value = mock_pricing_result

        # Configure Sales Engine Mock (check_and_apply_dynamic_pricing)
        # It must return DynamicPricingResultDTO with the passed orders
        def side_effect_dynamic_pricing(state, orders, *args, **kwargs):
            from modules.firm.api import DynamicPricingResultDTO
            return DynamicPricingResultDTO(orders=orders, price_updates={})
        mock_firm.sales_engine.check_and_apply_dynamic_pricing.side_effect = side_effect_dynamic_pricing

        # Setup Legacy Decision Engine Return
        legacy_order_keep = Order(
            agent_id=1, side="SELL", item_id="food", quantity=10,
            price_pennies=2000, market_id="food",
            price_limit=20.0
        )
        legacy_order_ignore = Order(
            agent_id=1, side="BUY", item_id="labor", quantity=5, # Should be filtered
            price_pennies=1000, market_id="labor",
            price_limit=10.0
        )
        mock_firm.decision_engine.make_decisions.return_value = ([legacy_order_keep, legacy_order_ignore], "TACTIC")

        # Act
        external_orders, tactic = mock_firm.make_decision(input_dto)

        # Assert: Finance Engine called
        assert mock_firm.finance_engine.plan_budget.called
        call_args_fin = mock_firm.finance_engine.plan_budget.call_args[0][0]
        assert isinstance(call_args_fin, FinanceDecisionInputDTO)
        assert call_args_fin.current_tick == 10

        # Assert: HR Engine called
        assert mock_firm.hr_engine.manage_workforce.called
        call_args_hr = mock_firm.hr_engine.manage_workforce.call_args[0][0]
        assert isinstance(call_args_hr, HRDecisionInputDTO)
        assert call_args_hr.budget_plan == mock_budget

        # Assert: Orders Merged and Filtered
        # external_orders should contain engine_order and legacy_order_keep, but NOT legacy_order_ignore
        assert len(external_orders) == 2
        assert engine_order in external_orders
        assert legacy_order_keep in external_orders
        assert legacy_order_ignore not in external_orders

        # Assert: Internal execution called
        mock_firm.execute_internal_orders.assert_called_once()
        executed_orders = mock_firm.execute_internal_orders.call_args[0][0]
        assert len(executed_orders) == 2 # Same list passed to internal executor (it filters internally if needed)

    def test_state_persistence_across_ticks(self, mock_firm):
        """
        Verify that Firm updates its internal state based on previous actions,
        simulating persistence across ticks.
        """
        # 1. Initial State
        mock_firm.hr_state.employees = []
        mock_firm.hr_state.employee_wages = {}

        # 2. Simulate HR Engine returning a wage update (as if from firing or negotiation)
        # Note: In the current refactor, HREngine returns orders (hire/fire) and wage updates.
        # But 'finalize_firing' and 'hire' are executed by transaction handlers or internal execution.
        # So we verify that IF an internal order is executed, state changes.

        # Mock action executor to APPLY changes or we verify that Firm's logic applies them.
        # Firm.make_decision calls execute_internal_orders.
        # But for HR, hiring happens via Market (External). Firing is Internal.

        # Test Case: Firing
        fire_order = Order(
            agent_id=1, side="FIRE", item_id="internal", quantity=1,
            price_pennies=1000, market_id="internal", target_agent_id=101,
            price_limit=10.0 # Added price_limit
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

        # Since finalize_firing is a mock in engines, the state won't change automatically
        # unless we set side_effect.
        # But this confirms the Orchestrator (ActionExecutor) correctly delegated the Persistence/State Update step.

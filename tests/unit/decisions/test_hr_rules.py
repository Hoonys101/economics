import pytest
from simulation.dtos import DecisionContext
from simulation.schemas import FirmActionVector
from tests.utils.factories import create_firm_config_dto

class TestHRRules:
    def test_make_decisions_hires_labor(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify BUY orders for labor when understaffed."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.8,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.production_target = 100.0
        state.production.inventory["food"] = 0.0
        state.hr.employees = [] # 0 Employees

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        # 3. Execution
        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        # 4. Verification
        labor_orders = [o for o in orders if getattr(o, "item_id", None) == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) > 0
        assert labor_orders[0].price > 10.0 # High aggressiveness bids up wage
        assert labor_orders[0].quantity > 0

    @pytest.mark.skip(reason="Legacy Mutation Assertion: Needs migration to Order Verification")
    def test_make_decisions_does_not_hire_when_full(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify no labor orders when employees >= needed."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.production_target = 10.0
        state.production.inventory["food"] = 0.0
        state.hr.employees = [1] * 100 # Mock employee IDs
        state.hr.employees_data = {i: {"labor_skill": 1.0} for i in range(100)}

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        labor_orders = [o for o in orders if getattr(o, "item_id", None) == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) == 0

    def test_make_decisions_fires_excess_labor(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify FIRE orders when overstaffed."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.production_target = 0.0 # No production needed
        state.production.inventory["food"] = 100.0 # Full inventory
        state.hr.employees = [1, 2]
        state.hr.employees_data = {1: {"wage": 10.0, "skill": 1.0}, 2: {"wage": 10.0, "skill": 1.0}}

        # Ensure we have cash to fire
        state.finance.balance = 1000.0

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        # 2. Verify Firing
        fire_orders = [o for o in orders if o.order_type == "FIRE"]
        assert len(fire_orders) > 0

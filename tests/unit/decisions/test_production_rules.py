import pytest
from simulation.dtos import DecisionContext
from tests.utils.factories import create_firm_config_dto

class TestProductionRules:
    def test_initialization(
        self, ai_decision_engine, mock_ai_engine, firm_engine_config
    ):
        assert ai_decision_engine.corporate_manager is not None
        assert ai_decision_engine.ai_engine == mock_ai_engine
        assert ai_decision_engine.config_module == firm_engine_config

    def test_make_decisions_overstock_reduces_target(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.inventory["food"] = 150.0 # Force overstock (150 > 100 * 1.2)
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(overstock_threshold=1.2),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        expected_target = max(
            firm_engine_config.FIRM_MIN_PRODUCTION_TARGET,
            initial_target * (1 - firm_engine_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )

        # Verify via orders (Purity)
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        assert target_orders[0].quantity == expected_target

    def test_make_decisions_understock_increases_target(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.inventory["food"] = 20.0
        state.production.production_target = 50.0  # Set lower than max (100) to allow increase
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(understock_threshold=0.8),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        expected_target = min(
            firm_engine_config.FIRM_MAX_PRODUCTION_TARGET,
            initial_target * (1 + firm_engine_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )

        # Verify via orders (Purity)
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        assert target_orders[0].quantity == expected_target

    def test_make_decisions_target_within_bounds_no_change(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.inventory["food"] = 100.0
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        # Ensure NO SET_TARGET order is generated
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) == 0

    def test_make_decisions_target_min_max_bounds(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        # Test min bound
        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.production.inventory["food"] = 1000.0
        state.production.production_target = firm_engine_config.FIRM_MIN_PRODUCTION_TARGET * 0.5

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        # Verify via orders
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        # It should try to reduce, but get clamped to MIN.
        # Logic: new_target = target * (1-adj) = 5 * 0.9 = 4.5.
        # Clamped: max(MIN, 4.5) = 10.
        # So it should be 10.
        assert target_orders[0].quantity == firm_engine_config.FIRM_MIN_PRODUCTION_TARGET

# Verified for TD-180

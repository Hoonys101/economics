import pytest
from simulation.dtos import DecisionContext
from simulation.schemas import FirmActionVector
from tests.utils.factories import create_firm_config_dto

class TestFinanceRules:
    def test_rd_investment(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify R&D investment when aggressiveness is high."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            rd_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.finance.balance = 100000.0 # High Cash

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        invest_orders = [o for o in orders if o.order_type == "INVEST_RD"]
        assert len(invest_orders) > 0

    def test_capex_investment(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify Capex investment when aggressiveness is high."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            capital_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.finance.balance = 100000.0 # High Cash

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        capex_orders = [o for o in orders if o.order_type == "INVEST_CAPEX"]
        assert len(capex_orders) > 0

    def test_dividend_setting(
        self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto
    ):
        """Verify dividend rate setting based on aggressiveness."""
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
            dividend_aggressiveness=0.9, # High Payout
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.finance.altman_z_score = 5.0 # Healthy
        state.finance.consecutive_loss_turns = 0
        state.finance.balance = 1000.0

        config = create_firm_config_dto()
        config.dividend_rate_min = 0.1
        config.dividend_rate_max = 0.5

        context = DecisionContext(
            state=state,
            config=config,
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = ai_decision_engine.make_decisions(context)
        orders = output.orders

        div_orders = [o for o in orders if o.order_type == "SET_DIVIDEND"]
        assert len(div_orders) > 0
        rate = div_orders[0].quantity
        assert rate > 0.1

# Verified for TD-180

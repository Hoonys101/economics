import pytest
from unittest.mock import MagicMock
from simulation.ai.household_ai import HouseholdAI
from modules.system.api import MarketSignalDTO, MarketSnapshotDTO
from simulation.dtos.api import GovernmentPolicyDTO

class TestHouseholdAIInsight:

    def test_active_learning_td_error(self):
        """Verify update_learning_v2 returns accumulated TD-Error."""
        ai = HouseholdAI(agent_id="test_agent", ai_decision_engine=MagicMock())
        ai.q_consumption = {"food": MagicMock()}
        ai.q_consumption["food"].update_q_table.return_value = 0.5 # TD Error

        # Other Q-Tables return 0
        ai.q_work = MagicMock()
        ai.q_work.update_q_table.return_value = 0.0
        ai.q_investment = MagicMock()
        ai.q_investment.update_q_table.return_value = 0.0

        ai.last_consumption_states = {"food": "s1"}
        ai.last_consumption_action_idxs = {"food": 1}
        ai.last_work_state = "s1"
        ai.last_work_action_idx = 1
        ai.last_investment_state = "s1"
        ai.last_investment_action_idx = 1

        td_error = ai.update_learning_v2(1.0, {"assets": 100}, {})
        assert td_error == 0.5

    def test_perceptual_filters_lag(self):
        """Verify low insight agents see 5-tick lagged prices."""
        ai = HouseholdAI(agent_id="lemon", ai_decision_engine=MagicMock())

        # Setup history
        signal = MarketSignalDTO(
            market_id="m1", item_id="item1", best_bid=10, best_ask=12,
            last_traded_price=100, last_trade_tick=10,
            price_history_7d=[10, 20, 30, 40, 50, 60, 70], # Lag 5 = index -5 = 30
            volatility_7d=0.1, order_book_depth_buy=1, order_book_depth_sell=1,
            total_bid_quantity=1, total_ask_quantity=1, is_frozen=False
        )
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.market_signals = {"item1": signal}

        # Inject context
        ai.ai_decision_engine.context.market_snapshot = snapshot

        # Agent data with low insight
        agent_data = {"market_insight": 0.1, "debt_data": {}}
        market_data = {"debt_data": {}}

        filtered = ai._apply_perceptual_filters(agent_data, market_data)

        assert "perceived_prices" in filtered
        # 5-tick lag from end: 70(0), 60(1), 50(2), 40(3), 30(4), 20(5 from end?? no len-5)
        # Logic: idx = max(0, len(history) - 5) = 7 - 5 = 2.
        # history[2] = 30.
        assert filtered["perceived_prices"]["item1"] == 30

    def test_perceptual_filters_sma(self):
        """Verify medium insight agents see 3-tick SMA prices."""
        ai = HouseholdAI(agent_id="laggard", ai_decision_engine=MagicMock())

        # Setup history
        signal = MarketSignalDTO(
            market_id="m1", item_id="item1", best_bid=10, best_ask=12,
            last_traded_price=100, last_trade_tick=10,
            price_history_7d=[10, 20, 30, 40, 50, 60, 70],
            volatility_7d=0.1, order_book_depth_buy=1, order_book_depth_sell=1,
            total_bid_quantity=1, total_ask_quantity=1, is_frozen=False
        )
        snapshot = MagicMock(spec=MarketSnapshotDTO)
        snapshot.market_signals = {"item1": signal}
        ai.ai_decision_engine.context.market_snapshot = snapshot

        # Medium Insight
        agent_data = {"market_insight": 0.5, "debt_data": {}}
        market_data = {"debt_data": {}}

        filtered = ai._apply_perceptual_filters(agent_data, market_data)

        # SMA last 3: 50, 60, 70 -> Avg 60
        assert filtered["perceived_prices"]["item1"] == 60.0

    def test_panic_reaction(self):
        """Verify high panic index + low insight reduces investment aggressiveness."""
        ai = HouseholdAI(agent_id="panic_agent", ai_decision_engine=MagicMock())
        ai.q_investment = MagicMock()
        # Mock Q-Table to return action index 4 (Max Aggressiveness = 1.0)
        ai.action_selector = MagicMock()
        ai.action_selector.choose_action.return_value = 4

        # Setup Context with High Panic
        policy = GovernmentPolicyDTO(0.1, 0.1, 0.1, 0.05, 0.0, 1.0, market_panic_index=0.8, fiscal_stance_indicator="NEUTRAL")
        ai.ai_decision_engine.context.government_policy = policy

        # Low Insight
        agent_data = {"market_insight": 0.1, "assets": 100000, "needs": {}}
        market_data = {"debt_data": {}}

        vector = ai.decide_action_vector(agent_data, market_data, [])

        # Expectation: Investment Aggressiveness Frozen to 0.0
        assert vector.investment_aggressiveness == 0.0

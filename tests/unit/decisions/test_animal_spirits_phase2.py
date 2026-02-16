import pytest
from unittest.mock import MagicMock, Mock
from simulation.models import Order
from simulation.dtos import DecisionContext, MarketSnapshotDTO, HouseholdConfigDTO, FirmConfigDTO
from modules.household.dtos import HouseholdStateDTO
from modules.simulation.dtos.api import FirmStateDTO
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine

class TestHouseholdSurvivalOverride:
    @pytest.fixture
    def mock_household_engine(self):
        ai_engine = MagicMock()
        config = MagicMock()
        logger = MagicMock()
        return AIDrivenHouseholdDecisionEngine(ai_engine, config, logger)

    def test_survival_override_triggered(self, mock_household_engine):
        # Setup Context
        config = MagicMock()
        config.survival_need_emergency_threshold = 0.8
        config.primary_survival_good_id = "food"
        config.survival_bid_premium = 1

        household_state = MagicMock(spec=HouseholdStateDTO)
        household_state.id = 1
        household_state.needs = {"survival": 0.9} # Critical
        household_state.assets = 100.0
        household_state.agent_data = {}
        household_state.expected_inflation = {}
        household_state.preference_asset = 1.0
        household_state.personality = "BALANCED"

        market_signals = {
            "food": {
                "best_ask": 10.0,
                "last_trade_tick": 100
            }
        }
        market_snapshot = MagicMock()
        market_snapshot.market_signals = market_signals

        context = DecisionContext(
            state=household_state,
            config=config,
            goods_data=[],
            market_data={},
            current_time=100,
            market_snapshot=market_snapshot
        )

        # Execute
        output = mock_household_engine._make_decisions_internal(context)
        orders = output.orders

        # Assert
        assert len(orders) == 1
        assert orders[0].order_type == "BUY"
        assert orders[0].item_id == "food"
        assert orders[0].price == 11.0 # 10.0 + 1.0
        assert orders[0].quantity == 1.0

    def test_survival_override_insufficient_funds(self, mock_household_engine):
        # Setup Context
        config = MagicMock()
        config.survival_need_emergency_threshold = 0.8
        config.primary_survival_good_id = "food"
        config.dsr_critical_threshold = 0.5 # Fix comparison error

        household_state = MagicMock(spec=HouseholdStateDTO)
        household_state.id = 1 # Fix attribute error
        household_state.needs = {"survival": 0.9}
        household_state.assets = 5.0 # Poor
        household_state.agent_data = {}
        household_state.expected_inflation = {} # Fix attribute error
        household_state.preference_asset = 1.0
        household_state.personality = "BALANCED" # Fix attribute error
        household_state.current_wage = 10.0 # Fix attribute error

        market_signals = {
            "food": {
                "best_ask": 10.0
            }
        }
        market_snapshot = {"market_signals": market_signals}

        context = DecisionContext(
            state=household_state,
            config=config,
            goods_data=[],
            market_data={},
            current_time=100,
            market_snapshot=market_snapshot
        )

        # Should fall back to normal logic (Mock AI engine returns empty for test)
        mock_household_engine.ai_engine.decide_action_vector.return_value = MagicMock()
        mock_household_engine.consumption_manager.decide_consumption = MagicMock(return_value=[])
        mock_household_engine.labor_manager.decide_labor = MagicMock(return_value=[])
        mock_household_engine.asset_manager.decide_investments = MagicMock(return_value=[])
    # mock_household_engine.housing_manager.decide_housing = MagicMock(return_value=[]) # Removed as it doesn't exist

        output = mock_household_engine._make_decisions_internal(context)
        orders = output.orders

        # Assert no survival order (assumes normal logic returns empty in this mock setup)
        # Verify survival override logic didn't return early
        assert len(orders) == 0

class TestFirmPricingLogic:
    @pytest.fixture
    def mock_firm_engine(self):
        ai_engine = MagicMock()
        config = MagicMock()
        logger = MagicMock()
        engine = AIDrivenFirmDecisionEngine(ai_engine, config, logger)
        # Mock corporate_manager
        engine.corporate_manager = MagicMock()
        return engine

    def test_cost_plus_fallback(self, mock_firm_engine):
        # Setup
        config = MagicMock()
        config.max_price_staleness_ticks = 10
        config.default_target_margin = 0.2
        config.fire_sale_asset_threshold = 0.0 # Disable fire sale

        # Remove spec to allow nested mocking without strict DTO validation (or update spec validation logic)
        firm_state = MagicMock()
        firm_state.id = 1
        # Mock Finance
        firm_state.finance = MagicMock()
        firm_state.finance.balance = 1000.0
        # Mock Production
        firm_state.production = MagicMock()
        firm_state.production.inventory = {"widget": 10}

        firm_state.agent_data = {"productivity_factor": 1.0}

        # Primary order from CEO (Market Price)
        primary_order = Order(1, "SELL", "widget", 10, 50.0, "widget") # Market price 50
        mock_firm_engine.corporate_manager.realize_ceo_actions.return_value = [primary_order]
        mock_firm_engine.ai_engine.decide_action_vector.return_value = MagicMock()

        # Stale Signal
        market_signals = {
            "widget": {
                "last_trade_tick": 50 # Current is 100, diff 50 > 10
            }
        }
        market_snapshot = {"market_signals": market_signals}

        goods_data = [{"id": "widget", "production_cost": 20.0}]

        context = DecisionContext(
            state=firm_state,
            config=config,
            goods_data=goods_data,
            market_data={},
            current_time=100,
            market_snapshot=market_snapshot
        )

        # Execute
        output = mock_firm_engine.make_decisions(context)
        orders = output.orders

        # Assert
        assert len(orders) == 1
        # Cost = 20.0 / 1.0 = 20.0
        # Price = 20.0 * (1 + 0.2) = 24.0
        # Check price_limit or price (OrderDTO vs Order)
        price = getattr(orders[0], 'price_limit', orders[0].price)
        assert price == 24.0

    def test_fire_sale_trigger(self, mock_firm_engine):
        # Setup
        config = MagicMock()
        config.fire_sale_asset_threshold = 100.0
        config.fire_sale_inventory_threshold = 10.0
        config.fire_sale_inventory_target = 5.0
        config.fire_sale_discount = 0.5

        firm_state = MagicMock()
        firm_state.id = 1
        firm_state.finance = MagicMock()
        firm_state.finance.balance = 50.0 # Distressed (< 100)
        firm_state.production = MagicMock()
        firm_state.production.inventory = {"widget": 20} # High Inventory (> 10)
        firm_state.agent_data = {"productivity_factor": 1.0}

        mock_firm_engine.corporate_manager.realize_ceo_actions.return_value = []
        mock_firm_engine.ai_engine.decide_action_vector.return_value = MagicMock()

        market_signals = {
            "widget": {
                "best_bid": 10.0,
                "last_trade_tick": 100
            }
        }
        market_snapshot = {"market_signals": market_signals}

        context = DecisionContext(
            state=firm_state,
            config=config,
            goods_data=[],
            market_data={},
            current_time=100,
            market_snapshot=market_snapshot
        )

        # Execute
        output = mock_firm_engine.make_decisions(context)
        orders = output.orders

        # Assert
        assert len(orders) == 1
        fire_sale = orders[0]
        assert fire_sale.order_type == "SELL"
        assert fire_sale.quantity == 15.0 # 20 - 5
        price = getattr(fire_sale, 'price_limit', fire_sale.price)
        assert price == 5.0 # 10.0 * (1 - 0.5)

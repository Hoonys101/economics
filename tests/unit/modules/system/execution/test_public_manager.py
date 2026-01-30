import pytest
from unittest.mock import MagicMock
from modules.system.execution.public_manager import PublicManager
from modules.system.api import AgentBankruptcyEventDTO, MarketSignalDTO

class TestPublicManager:
    @pytest.fixture
    def public_manager(self):
        config = MagicMock()
        config.LIQUIDATION_SELL_RATE = 0.5
        config.LIQUIDATION_ASK_UNDERCUT = 0.1
        return PublicManager(config)

    def test_process_bankruptcy_event(self, public_manager):
        event: AgentBankruptcyEventDTO = {
            "agent_id": 1,
            "tick": 10,
            "inventory": {"apple": 10.0, "banana": 5.0}
        }

        public_manager.process_bankruptcy_event(event)

        assert public_manager.managed_inventory["apple"] == 10.0
        assert public_manager.managed_inventory["banana"] == 5.0
        assert public_manager.last_tick_recovered_assets["apple"] == 10.0

    def test_generate_liquidation_orders(self, public_manager):
        # Setup inventory
        public_manager.managed_inventory["apple"] = 100.0

        # Setup signals
        signals = {
            "apple": MarketSignalDTO(
                market_id="apple",
                item_id="apple",
                best_ask=10.0,
                best_bid=9.0,
                last_traded_price=9.5,
                last_trade_tick=9,
                price_history_7d=[],
                volatility_7d=0.1,
                order_book_depth_buy=5,
                order_book_depth_sell=5,
                is_frozen=False
            )
        }

        orders = public_manager.generate_liquidation_orders(signals)

        assert len(orders) == 1
        order = orders[0]
        assert order.agent_id == "PUBLIC_MANAGER"
        assert order.item_id == "apple"
        assert order.order_type == "SELL"

        # Sell Rate 0.5 -> 50 apples
        assert order.quantity == 50.0

        # Ask Undercut 0.1 -> 10.0 * 0.9 = 9.0
        assert order.price == 9.0

        # Inventory NOT tentatively decremented (Change in Logic)
        assert public_manager.managed_inventory["apple"] == 100.0

    def test_confirm_sale(self, public_manager):
        public_manager.managed_inventory["apple"] = 100.0
        public_manager.confirm_sale("apple", 50.0)
        assert public_manager.managed_inventory["apple"] == 50.0

        public_manager.confirm_sale("apple", 60.0)
        assert public_manager.managed_inventory["apple"] == 0.0

    def test_deposit_revenue(self, public_manager):
        public_manager.deposit_revenue(100.0)
        assert public_manager.system_treasury == 100.0
        assert public_manager.last_tick_revenue == 100.0

        public_manager.deposit_revenue(50.0)
        assert public_manager.system_treasury == 150.0
        assert public_manager.last_tick_revenue == 150.0

    def test_generate_liquidation_orders_no_signal(self, public_manager):
        public_manager.managed_inventory["pear"] = 10.0
        orders = public_manager.generate_liquidation_orders({})
        assert len(orders) == 0
        assert public_manager.managed_inventory["pear"] == 10.0

    def test_generate_liquidation_orders_resets_metrics(self, public_manager):
        public_manager.last_tick_revenue = 500.0
        public_manager.generate_liquidation_orders({})
        assert public_manager.last_tick_revenue == 0.0

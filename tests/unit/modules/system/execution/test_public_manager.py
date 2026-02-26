import pytest
from unittest.mock import MagicMock
from modules.system.execution.public_manager import PublicManager
from modules.system.api import AgentBankruptcyEventDTO, MarketSignalDTO, DEFAULT_CURRENCY, AssetBuyoutRequestDTO
from modules.system.constants import ID_PUBLIC_MANAGER
from modules.simulation.api import IInventoryHandler
from modules.finance.api import IFinancialAgent

class TestPublicManager:

    @pytest.fixture
    def public_manager(self):
        config = MagicMock()
        config.LIQUIDATION_SELL_RATE = 0.5
        config.LIQUIDATION_ASK_UNDERCUT = 0.1
        return PublicManager(config)

    def test_process_bankruptcy_event(self, public_manager):
        event: AgentBankruptcyEventDTO = {'agent_id': 1, 'tick': 10, 'inventory': {'apple': 10.0, 'banana': 5.0}}
        public_manager.process_bankruptcy_event(event)
        assert public_manager.managed_inventory['apple'] == 10.0
        assert public_manager.managed_inventory['banana'] == 5.0
        assert public_manager.last_tick_recovered_assets['apple'] == 10.0

    def test_generate_liquidation_orders(self, public_manager):
        public_manager.managed_inventory['apple'] = 100.0
        signals = {'apple': MarketSignalDTO(market_id='apple', item_id='apple', best_ask=10.0, best_bid=9.0, last_traded_price=9.5, last_trade_tick=9, price_history_7d=[], volatility_7d=0.1, order_book_depth_buy=5, order_book_depth_sell=5, total_bid_quantity=0.0, total_ask_quantity=0.0, is_frozen=False)}
        orders = public_manager.generate_liquidation_orders(signals)
        assert len(orders) == 1
        order = orders[0]
        assert order.agent_id == ID_PUBLIC_MANAGER
        assert order.item_id == 'apple'
        assert order.order_type == 'SELL'
        assert order.quantity == 50.0
        assert order.price == 9.0
        assert public_manager.managed_inventory['apple'] == 100.0

    def test_confirm_sale(self, public_manager):
        public_manager.managed_inventory['apple'] = 100.0
        public_manager.confirm_sale('apple', 50.0)
        assert public_manager.managed_inventory['apple'] == 50.0
        public_manager.confirm_sale('apple', 60.0)
        assert public_manager.managed_inventory['apple'] == 0.0

    def test_deposit_revenue(self, public_manager):
        public_manager.deposit_revenue(100.0)
        assert public_manager.system_treasury[DEFAULT_CURRENCY] == 100.0
        assert public_manager.last_tick_revenue[DEFAULT_CURRENCY] == 100.0
        public_manager.deposit_revenue(50.0)
        assert public_manager.system_treasury[DEFAULT_CURRENCY] == 150.0
        assert public_manager.last_tick_revenue[DEFAULT_CURRENCY] == 150.0

    def test_generate_liquidation_orders_no_signal(self, public_manager):
        public_manager.managed_inventory['pear'] = 10.0
        orders = public_manager.generate_liquidation_orders({})
        assert len(orders) == 0
        assert public_manager.managed_inventory['pear'] == 10.0

    def test_generate_liquidation_orders_resets_metrics(self, public_manager):
        public_manager.last_tick_revenue = {DEFAULT_CURRENCY: 500.0}
        public_manager.generate_liquidation_orders({})
        assert public_manager.last_tick_revenue == {DEFAULT_CURRENCY: 0.0}

    def test_execute_asset_buyout(self, public_manager):
        request = AssetBuyoutRequestDTO(
            seller_id=1,
            inventory={'gold': 10},
            market_prices={'gold': 100},
            distress_discount=0.5
        )
        result = public_manager.execute_asset_buyout(request)

        assert result.success
        assert result.total_paid_pennies == 500 # 10 * 100 * 0.5
        assert public_manager.managed_inventory['gold'] == 10
        assert public_manager.last_tick_recovered_assets['gold'] == 10

    def test_rollback_asset_buyout(self, public_manager):
        # Setup mocks for currency reversal and asset restoration
        mock_settlement = MagicMock()
        public_manager.set_settlement_system(mock_settlement)

        mock_registry = MagicMock()
        public_manager.set_agent_registry(mock_registry)

        # Create a mock that implements both protocols
        class MockSeller(IInventoryHandler, IFinancialAgent):
             pass

        mock_seller = MagicMock(spec=MockSeller)
        mock_seller.id = 1
        mock_registry.get_agent.return_value = mock_seller

        request = AssetBuyoutRequestDTO(
            seller_id=1,
            inventory={'gold': 10},
            market_prices={'gold': 100},
            distress_discount=0.5
        )
        # 1. Execute
        public_manager.execute_asset_buyout(request)
        assert public_manager.managed_inventory['gold'] == 10

        # 2. Rollback
        success = public_manager.rollback_asset_buyout(request)

        assert success
        assert public_manager.managed_inventory['gold'] == 0
        assert public_manager.last_tick_recovered_assets['gold'] == 0

        # Verify asset restoration
        mock_seller.add_item.assert_called_with('gold', 10, reason="ROLLBACK_BAILOUT")

        # Verify currency reversal (10 * 100 * 0.5 = 500)
        mock_settlement.transfer.assert_called_once()
        args, kwargs = mock_settlement.transfer.call_args
        assert kwargs['debit_agent'] == mock_seller
        assert kwargs['credit_agent'] == public_manager
        assert kwargs['amount'] == 500
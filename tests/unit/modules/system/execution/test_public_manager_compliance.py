import pytest
from unittest.mock import MagicMock
from modules.system.execution.public_manager import PublicManager
from modules.finance.api import IFinancialAgent, InsufficientFundsError
from modules.system.api import AgentBankruptcyEventDTO, MarketSignalDTO

class TestPublicManagerCompliance:

    @pytest.fixture
    def public_manager(self):
        config = MagicMock()
        config.LIQUIDATION_SELL_RATE = 0.1
        config.LIQUIDATION_ASK_UNDERCUT = 0.05
        return PublicManager(config)

    def test_implements_financial_agent(self, public_manager):
        """Verify PublicManager strictly implements IFinancialAgent."""
        assert isinstance(public_manager.id, int), 'PublicManager.id must be an integer'
        assert public_manager.id == 999999
        assert public_manager.total_wealth == 0
        public_manager._deposit(100)
        assert public_manager.total_wealth == 100
        public_manager._withdraw(50)
        assert public_manager.total_wealth == 50
        with pytest.raises(InsufficientFundsError):
            public_manager._withdraw(100)

    def test_implements_asset_recovery_system(self, public_manager):
        """Verify PublicManager implements IAssetRecoverySystem."""
        assert hasattr(public_manager, 'process_bankruptcy_event')
        assert hasattr(public_manager, 'generate_liquidation_orders')
        assert hasattr(public_manager, 'deposit_revenue')
        assert hasattr(public_manager, 'confirm_sale')
        assert hasattr(public_manager, 'get_status_report')

    def test_bankruptcy_processing_id_handling(self, public_manager):
        """Verify handling of bankruptcy events."""
        event: AgentBankruptcyEventDTO = {'agent_id': 99, 'tick': 1, 'inventory': {'gold': 10.0}}
        public_manager.process_bankruptcy_event(event)
        assert public_manager.managed_inventory['gold'] == 10.0

    def test_liquidation_order_generation_id(self, public_manager):
        """Verify generated orders use the correct integer ID."""
        public_manager.managed_inventory['gold'] = 10.0
        signals = {'gold': MarketSignalDTO(market_id='gold', item_id='gold', best_ask=100.0, best_bid=90.0, last_traded_price=95.0, last_trade_tick=1, price_history_7d=[], volatility_7d=0.0, order_book_depth_buy=1, order_book_depth_sell=1, total_bid_quantity=0.0, total_ask_quantity=0.0, is_frozen=False)}
        orders = public_manager.generate_liquidation_orders(signals)
        assert len(orders) > 0
        order = orders[0]
        assert order.agent_id == public_manager.id
        assert isinstance(order.agent_id, int)
        assert order.agent_id == 999999
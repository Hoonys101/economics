import pytest
from unittest.mock import Mock, MagicMock
from simulation.firms import Firm
from simulation.components.engines.sales_engine import SalesEngine
from simulation.components.state.firm_state_models import SalesState
from simulation.models import Order, Transaction
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from modules.simulation.dtos.api import FirmConfigDTO
from modules.simulation.api import AgentCoreConfigDTO

class TestWO157DynamicPricing:

    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=FirmConfigDTO)
        config.sale_timeout_ticks = 10
        config.dynamic_price_reduction_factor = 0.9
        config.profit_history_ticks = 10
        config.inventory_holding_cost_rate = 0.01
        config.firm_maintenance_fee = 10.0
        config.corporate_tax_rate = 0.1
        config.bailout_repayment_ratio = 0.1
        config.valuation_per_multiplier = 10.0
        config.bankruptcy_consecutive_loss_threshold = 5
        config.firm_min_production_target = 10.0
        config.ipo_initial_shares = 1000.0
        config.dividend_rate = 0.1
        config.initial_firm_liquidity_need = 100.0
        config.default_target_margin = 0.2
        config.max_price_staleness_ticks = 10
        config.fire_sale_asset_threshold = 100.0
        config.fire_sale_inventory_threshold = 0.5
        config.fire_sale_inventory_target = 0.5
        config.fire_sale_discount = 0.2
        config.fire_sale_cost_discount = 0.5
        config.invisible_hand_sensitivity = 0.1
        config.GOODS = {}
        return config

    def test_record_sale_updates_tick(self, mock_config):
        core_config = AgentCoreConfigDTO(id=1, name='Firm_1', logger=Mock(), memory_interface=None, value_orientation='PROFIT', initial_needs={})
        firm = Firm(core_config=core_config, engine=Mock(), specialization='widget', productivity_factor=1.0, config_dto=mock_config)
        firm.record_sale('widget', 10.0, 100)
        assert firm.sales_state.inventory_last_sale_tick['widget'] == 100
        firm.record_sale('widget', 5.0, 105)
        assert firm.sales_state.inventory_last_sale_tick['widget'] == 105

    def test_dynamic_pricing_reduction(self, mock_config):
        engine = SalesEngine()
        state = SalesState()
        current_tick = 100
        last_sale = 80
        state.inventory_last_sale_tick['widget'] = last_sale
        orders = [Order(1, 'SELL', 'widget', 10.0, int(100.0 * 100), 100.0, 'market')]

        def estimator(item_id):
            return 50.0
        engine.check_and_apply_dynamic_pricing(state, orders, current_tick, mock_config, estimator)
        assert orders[0].price_limit == 90.0
        assert state.last_prices['widget'] == 90.0

    def test_dynamic_pricing_floor(self, mock_config):
        engine = SalesEngine()
        state = SalesState()
        current_tick = 100
        last_sale = 80
        state.inventory_last_sale_tick['widget'] = last_sale
        orders = [Order(1, 'SELL', 'widget', 10.0, int(52.0 * 100), 52.0, 'market')]

        def estimator(item_id):
            return 50.0
        engine.check_and_apply_dynamic_pricing(state, orders, current_tick, mock_config, estimator)
        assert orders[0].price_limit == 50.0
        assert state.last_prices['widget'] == 50.0

    def test_dynamic_pricing_not_stale(self, mock_config):
        engine = SalesEngine()
        state = SalesState()
        current_tick = 100
        last_sale = 95
        state.inventory_last_sale_tick['widget'] = last_sale
        orders = [Order(1, 'SELL', 'widget', 10.0, int(100.0 * 100), 100.0, 'market')]

        def estimator(item_id):
            return 50.0
        engine.check_and_apply_dynamic_pricing(state, orders, current_tick, mock_config, estimator)
        assert orders[0].price_limit == 100.0

    def test_transaction_processor_calls_record_sale(self, mock_config):
        processor = TransactionProcessor(mock_config)
        state = Mock()
        state.time = 200
        state.settlement_system = Mock()
        state.settlement_system.transfer.return_value = True
        state.market_data = {}
        state.taxation_system = Mock()
        state.taxation_system.calculate_tax_intents.return_value = []
        buyer = Mock()
        buyer.assets = 1000.0
        buyer.inventory = {}
        buyer.inventory_quality = {}
        seller = Mock(spec=Firm)
        seller.record_sale = Mock()
        state.agents = {1: buyer, 2: seller}
        tx = Transaction(buyer_id=1, seller_id=2, item_id='widget', quantity=5.0, price=10.0, market_id='market', transaction_type='goods', time=200)
        state.transactions = [tx]
        handler = GoodsTransactionHandler()
        processor.register_handler('goods', handler)
        processor.execute(state)
        seller.record_sale.assert_called_with('widget', 5.0, 200)
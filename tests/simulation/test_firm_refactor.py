import pytest
from unittest.mock import MagicMock, patch
from simulation.firms import Firm
from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.models import Order, Transaction
from modules.system.api import DEFAULT_CURRENCY, MarketContextDTO

@pytest.fixture
def mock_decision_engine():
    return MagicMock()

@pytest.fixture
def firm_config():
    config = MagicMock(spec=FirmConfigDTO)
    config.firm_min_production_target = 10.0
    config.ipo_initial_shares = 1000.0
    config.dividend_rate = 0.1
    config.bankruptcy_consecutive_loss_threshold = 20
    config.labor_market_min_wage = 10.0
    config.halo_effect = 0.0
    config.labor_alpha = 0.7
    config.automation_labor_reduction = 0.5
    config.labor_elasticity_min = 0.1
    config.capital_depreciation_rate = 0.01
    config.goods = {"FOOD": {"quality_sensitivity": 0.5, "inputs": {}}}
    config.inventory_holding_cost_rate = 0.01
    config.firm_maintenance_fee = 5.0
    config.bailout_repayment_ratio = 0.1
    config.valuation_per_multiplier = 5.0
    config.automation_cost_per_pct = 100.0
    config.capital_to_output_ratio = 2.0
    config.invisible_hand_sensitivity = 0.1
    return config

@pytest.fixture
def firm(mock_decision_engine, firm_config):
    def mock_base_init(self, config):
        self.id = config.id
        self.is_active = True
        self.logger = MagicMock()
        self.needs = {}
        self._inventory = {}
        self.decision_engine = config.decision_engine
        self.memory_v2 = None
        self.settlement_system = MagicMock()

    with patch('simulation.firms.BaseAgent.__init__', side_effect=mock_base_init, autospec=True), \
         patch('simulation.base_agent.BaseAgent.wallet', new_callable=MagicMock) as mock_wallet, \
         patch('simulation.firms.BrandManager'):

        mock_wallet.get_balance.return_value = 1000.0
        mock_wallet.get_all_balances.return_value = {DEFAULT_CURRENCY: 1000.0}

        f = Firm(
            id=1,
            initial_capital=1000.0,
            initial_liquidity_need=100.0,
            specialization="FOOD",
            productivity_factor=1.0,
            decision_engine=mock_decision_engine,
            value_orientation="PROFIT",
            config_dto=firm_config
        )

        # Setup settlement system mock
        f.settlement_system = MagicMock()
        f.settlement_system.transfer.return_value = True

        yield f

def test_firm_initialization_states(firm):
    assert isinstance(firm.hr_state, HRState)
    assert isinstance(firm.finance_state, FinanceState)
    assert isinstance(firm.production_state, ProductionState)
    assert isinstance(firm.sales_state, SalesState)

    assert firm.production_state.specialization == "FOOD"
    assert firm.finance_state.total_shares == 1000.0

def test_inventory_handler_implementation(firm):
    # Test add_item
    firm.add_item("item1", 10.0)
    assert firm.get_quantity("item1") == 10.0

    # Test remove_item
    firm.remove_item("item1", 5.0)
    assert firm.get_quantity("item1") == 5.0

    # Test remove more than available
    assert not firm.remove_item("item1", 10.0)
    assert firm.get_quantity("item1") == 5.0

    # Test liquidate_assets
    assets = firm.liquidate_assets()
    assert firm.get_quantity("item1") == 0.0 # Should be cleared
    assert firm.capital_stock == 0.0
    assert firm.automation_level == 0.0
    assert assets == {DEFAULT_CURRENCY: 1000.0}

def test_command_bus_internal_orders(firm):
    # SET_TARGET
    # OrderDTO uses 'side' as 'order_type' alias
    order = Order(
        agent_id=1, side="SET_TARGET", item_id="target", quantity=50.0,
        price_limit=0.0, market_id="internal"
    )
    firm._execute_internal_order(order, None, 0)
    assert firm.production_state.production_target == 50.0

    # INVEST_AUTOMATION
    # finance_engine.invest_in_automation now takes (state, agent, wallet, amount, gov, settlement)
    firm.finance_engine.invest_in_automation = MagicMock(return_value=True)
    firm.production_engine.invest_in_automation = MagicMock(return_value=0.05)

    order_auto = Order(
        agent_id=1, side="INVEST_AUTOMATION", item_id="automation", quantity=1.0,
        price_limit=0.0, market_id="internal",
        monetary_amount={'amount': 100.0, 'currency': DEFAULT_CURRENCY}
    )
    firm._execute_internal_order(order_auto, None, 0)

    firm.finance_engine.invest_in_automation.assert_called_once()
    # Check arguments: state, firm (self), wallet, amount, gov, settlement
    args = firm.finance_engine.invest_in_automation.call_args[0]
    assert args[1] == firm
    assert args[2] == firm.wallet

    firm.production_engine.invest_in_automation.assert_called_once()

def test_generate_transactions_delegation(firm):
    firm.hr_engine.process_payroll = MagicMock(return_value=[])
    firm.finance_engine.generate_financial_transactions = MagicMock(return_value=[])
    firm.sales_engine.generate_marketing_transaction = MagicMock(return_value=None)

    market_context = {"exchange_rates": {DEFAULT_CURRENCY: 1.0}}

    txs = firm.generate_transactions(
        government=MagicMock(),
        market_data={},
        shareholder_registry=MagicMock(),
        current_time=0,
        market_context=market_context
    )

    firm.hr_engine.process_payroll.assert_called_once()
    firm.finance_engine.generate_financial_transactions.assert_called_once()

    # Check arguments
    f_args = firm.finance_engine.generate_financial_transactions.call_args[0]
    # (state, id, wallet, config, gov, registry, time, context, inv_val)
    assert f_args[2] == firm.wallet

    firm.sales_engine.generate_marketing_transaction.assert_called_once()

def test_produce_delegation(firm):
    firm.production_engine.produce = MagicMock(return_value=10.0)

    firm.produce(current_time=0)

    firm.production_engine.produce.assert_called_once()
    assert firm.current_production == 10.0

def test_finance_engine_interface():
    engine = FinanceEngine()
    assert hasattr(engine, 'invest_in_automation')
    assert hasattr(engine, 'invest_in_rd')
    assert hasattr(engine, 'invest_in_capex')
    assert hasattr(engine, 'pay_ad_hoc_tax')

import pytest
from unittest.mock import MagicMock, patch
from simulation.firms import Firm
from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY, MarketContextDTO
from modules.simulation.api import AgentCoreConfigDTO
from modules.hr.api import IEmployeeDataProvider

@pytest.fixture
def mock_decision_engine():
    return MagicMock()

@pytest.fixture
def firm_config():
    config = MagicMock(spec=FirmConfigDTO)
    # Populate with necessary fields
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
    config.default_unit_cost = 5.0
    config.marketing_decay_rate = 0.05
    config.marketing_efficiency = 1.0
    config.perceived_quality_alpha = 0.5
    config.brand_awareness_saturation = 100.0
    config.marketing_budget_rate_min = 0.01
    config.marketing_budget_rate_max = 0.1
    config.profit_history_ticks = 10
    config.ticks_per_year = 365
    config.severance_pay_weeks = 2.0
    config.sale_timeout_ticks = 10
    config.dynamic_price_reduction_factor = 0.9
    return config

@pytest.fixture
def core_config():
    return AgentCoreConfigDTO(
        id=1,
        value_orientation="PROFIT",
        initial_needs={"liquidity_need": 100.0},
        name="Firm_1",
        logger=MagicMock(),
        memory_interface=None
    )

@pytest.fixture
def firm(mock_decision_engine, firm_config, core_config):
    # Initialize Firm directly without BaseAgent patching
    f = Firm(
        core_config=core_config,
        engine=mock_decision_engine,
        specialization="FOOD",
        productivity_factor=1.0,
        config_dto=firm_config,
        initial_inventory=None,
        loan_market=None,
        sector="FOOD",
        personality=None
    )

    # Manually hydrate wallet for testing (since we are not using full simulation loop)
    f.wallet.load_balances({DEFAULT_CURRENCY: 1000.0})

    # Mock settlement system for internal order tests
    f.settlement_system = MagicMock()
    f.settlement_system.transfer.return_value = True

    return f

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
    order = Order(
        agent_id=1, side="SET_TARGET", item_id="target", quantity=50.0,
        price_limit=0.0, market_id="internal"
    )
    firm._execute_internal_order(order, None, 0)
    assert firm.production_state.production_target == 50.0

    # INVEST_AUTOMATION
    # Use real engines, but mock settlement system to succeed
    # And mock government for transfer destination
    gov = MagicMock()
    gov.id = 999

    # Ensure wallet has funds
    firm.wallet.load_balances({DEFAULT_CURRENCY: 2000.0})

    order_auto = Order(
        agent_id=1, side="INVEST_AUTOMATION", item_id="automation", quantity=1.0,
        price_limit=0.0, market_id="internal",
        monetary_amount={'amount': 100.0, 'currency': DEFAULT_CURRENCY}
    )

    # Execute
    firm._execute_internal_order(order_auto, gov, 0)

    # Verify state change
    # automation_level should have increased
    # logic: gained = amount / cost_per_pct = 100.0 / 100.0 = 1.0
    # production_state.automation_level += 1.0
    assert firm.production_state.automation_level > 0.0

    # Verify transaction generated via settlement system call
    firm.settlement_system.transfer.assert_called()
    args = firm.settlement_system.transfer.call_args
    # call_args is ((sender, recipient, amount, reason), {currency: ...})
    # or just args if positional.
    # firm code: transfer(self, government, amount, "Automation", currency=DEFAULT_CURRENCY)

    call_args = args[0]
    call_kwargs = args[1]

    assert call_args[0] == firm
    assert call_args[1] == gov
    assert call_args[2] == 100.0
    assert call_args[3] == "Automation"
    assert call_kwargs.get('currency', DEFAULT_CURRENCY) == DEFAULT_CURRENCY


def test_generate_transactions_delegation(firm):
    # This tests that engines are called. Since we can't easily mock internal engines
    # (they are instantiated inside __init__), we can verify the OUTPUT of generate_transactions.

    # Setup state for payroll
    firm.hr_state.employees = [] # No employees, so no payroll tx

    # Setup state for finance
    firm.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 100.0}
    firm.finance_state.cost_this_turn = {DEFAULT_CURRENCY: 50.0}

    market_context = {"exchange_rates": {DEFAULT_CURRENCY: 1.0}, "fiscal_policy": MagicMock(corporate_tax_rate=0.2)}
    gov = MagicMock()
    gov.id = 999
    registry = MagicMock()

    txs = firm.generate_transactions(
        government=gov,
        market_data={},
        shareholder_registry=registry,
        current_time=0,
        market_context=market_context
    )

    # We expect some transactions (holding cost, maintenance fee) if configured
    # Config has maintenance fee = 5.0
    # Wallet has money.

    # Check for maintenance fee transaction
    # Since we are using real FinanceEngine, we need to check if maintenance fee is generated
    # maintenance fee is in generate_financial_transactions

    maintenance_tx = next((tx for tx in txs if tx.item_id == "firm_maintenance"), None)
    assert maintenance_tx is not None
    assert maintenance_tx.price == 5.0

def test_generate_transactions_payroll_integration(firm):
    """
    Test that Firm correctly orchestrates HREngine results.
    """
    # Setup Employee
    emp = MagicMock(spec=IEmployeeDataProvider)
    emp.id = 101
    emp.employer_id = firm.id
    emp.is_employed = True
    emp.labor_skill = 1.0
    emp.education_level = 0.0
    emp.labor_income_this_tick = 0.0

    firm.hr_state.employees = [emp]
    firm.hr_state.employee_wages = {101: 20.0}

    # Setup Wallet
    firm.wallet.load_balances({DEFAULT_CURRENCY: 1000.0})

    # Mock Government
    gov = MagicMock()
    gov.id = 999

    # Mock Fiscal Policy
    fiscal_policy = MagicMock()
    fiscal_policy.corporate_tax_rate = 0.2
    fiscal_policy.income_tax_rate = 0.1
    fiscal_policy.survival_cost = 10.0
    fiscal_policy.government_agent_id = 999

    market_context = {
        "exchange_rates": {DEFAULT_CURRENCY: 1.0},
        "fiscal_policy": fiscal_policy
    }

    # Execute
    transactions = firm.generate_transactions(
        government=gov,
        market_data={},
        shareholder_registry=MagicMock(),
        current_time=100,
        market_context=market_context
    )

    # Verify Transactions
    wage_tx = next((tx for tx in transactions if tx.item_id == "labor_wage"), None)
    assert wage_tx is not None
    assert wage_tx.price == 18.0 # 20 - 10% tax

    # Verify Employee Update (Orchestrator action)
    assert emp.labor_income_this_tick == 18.0

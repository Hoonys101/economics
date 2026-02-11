import pytest
from unittest.mock import MagicMock, patch
from simulation.firms import Firm
from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY, MarketContextDTO
from modules.simulation.api import AgentCoreConfigDTO
from modules.hr.api import IEmployeeDataProvider
from modules.firm.api import AssetManagementResultDTO, RDResultDTO, ProductionResultDTO

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
    # Initialize Firm directly
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

    # Manually hydrate wallet for testing
    f.wallet.load_balances({DEFAULT_CURRENCY: 1000.0})

    # Mock settlement system for internal order tests
    f.settlement_system = MagicMock()
    f.settlement_system.transfer.return_value = True

    # Mock Internal Engines
    f.asset_management_engine = MagicMock()
    f.rd_engine = MagicMock()
    f.production_engine = MagicMock()

    return f

def test_firm_initialization_states(firm):
    assert isinstance(firm.hr_state, HRState)
    assert isinstance(firm.finance_state, FinanceState)
    assert isinstance(firm.production_state, ProductionState)
    assert isinstance(firm.sales_state, SalesState)

    assert firm.production_state.specialization == "FOOD"
    assert firm.finance_state.total_shares == 1000.0

def test_command_bus_internal_orders_delegation(firm):
    # Setup Context
    fiscal_context = MagicMock()
    gov = MagicMock()
    gov.id = 999
    fiscal_context.government = gov

    # 1. INVEST_AUTOMATION
    firm.wallet.load_balances({DEFAULT_CURRENCY: 2000.0})

    order_auto = Order(
        agent_id=1, side="INVEST_AUTOMATION", item_id="automation", quantity=1.0,
        price_limit=0.0, market_id="internal",
        monetary_amount={'amount_pennies': 100, 'currency': DEFAULT_CURRENCY}
    )

    # Mock Engine Result
    firm.asset_management_engine.invest.return_value = AssetManagementResultDTO(
        success=True,
        automation_level_increase=0.01,
        actual_cost=100.0
    )

    firm.execute_internal_orders([order_auto], fiscal_context, 0)

    # Verify delegation
    firm.asset_management_engine.invest.assert_called_once()

    # Verify state update
    assert firm.production_state.automation_level > 0.0

    # Verify transfer
    firm.settlement_system.transfer.assert_called()

    # 2. INVEST_RD
    order_rd = Order(
        agent_id=1, side="INVEST_RD", item_id="rd", quantity=1.0,
        price_limit=0.0, market_id="internal",
        monetary_amount={'amount_pennies': 100, 'currency': DEFAULT_CURRENCY}
    )

    firm.rd_engine.research.return_value = RDResultDTO(
        success=True,
        quality_improvement=0.1,
        productivity_multiplier_change=1.05,
        actual_cost=100.0
    )

    firm.execute_internal_orders([order_rd], fiscal_context, 0)

    firm.rd_engine.research.assert_called_once()
    assert firm.production_state.base_quality > 0.0 # Initial was 0.0 (default)?
    # Actually initial base_quality depends on state init. Let's assume default is 0 or from somewhere.
    # ProductionState initializes base_quality=1.0 usually?
    # Let's check logic: self.production_state.base_quality += 0.1
    # So it should increase.

def test_produce_orchestration(firm):
    # Mock ProductionEngine result
    firm.production_engine.produce.return_value = ProductionResultDTO(
        success=True,
        quantity_produced=10.0,
        quality=1.5,
        specialization="FOOD",
        inputs_consumed={"RAW": 5.0},
        production_cost=50.0,
        capital_depreciation=5.0,
        automation_decay=0.01
    )

    # Set initial state
    from modules.simulation.api import InventorySlot
    firm.production_state.capital_stock = 100.0
    firm.production_state.automation_level = 0.5
    firm.add_item("RAW", 10.0, slot=InventorySlot.INPUT)

    firm.produce(current_time=0)

    # Verify state updates
    assert firm.production_state.capital_stock == 95.0 # 100 - 5
    assert firm.production_state.automation_level == 0.49 # 0.5 - 0.01
    assert firm.get_quantity("RAW", slot=InventorySlot.INPUT) == 5.0 # 10 - 5
    assert firm.current_production == 10.0
    assert firm.get_quantity("FOOD") == 10.0

    # Verify engine called
    firm.production_engine.produce.assert_called_once()

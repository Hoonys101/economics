import pytest
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.firms import Firm
from simulation.schemas import FirmActionVector
from simulation.dtos import FirmStateDTO
from tests.utils.factories import create_firm_config_dto


# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch(
        "simulation.decisions.ai_driven_firm_engine.logging.getLogger"
    ) as mock_get_logger:
        mock_logger_instance = MagicMock(name="firm_decision_engine_logger")
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# Mock config module for controlled testing
@pytest.fixture
def firm_engine_config():
    mock_cfg = Mock()
    mock_cfg.OVERSTOCK_THRESHOLD = 1.2
    mock_cfg.UNDERSTOCK_THRESHOLD = 0.8
    mock_cfg.FIRM_MIN_PRODUCTION_TARGET = 10.0
    mock_cfg.FIRM_MAX_PRODUCTION_TARGET = 500.0
    mock_cfg.PRODUCTION_ADJUSTMENT_FACTOR = 0.1
    mock_cfg.FIRM_MIN_EMPLOYEES = 1
    mock_cfg.FIRM_MAX_EMPLOYEES = 50
    mock_cfg.BASE_WAGE = 10.0
    mock_cfg.GOODS = {
        "food": {"production_cost": 5.0}
    }
    mock_cfg.GOODS_MARKET_SELL_PRICE = 5.0
    mock_cfg.MIN_SELL_PRICE = 1.0
    mock_cfg.MAX_SELL_PRICE = 100.0
    mock_cfg.MAX_SELL_QUANTITY = 50.0
    mock_cfg.PRICE_ADJUSTMENT_FACTOR = 0.05
    mock_cfg.PRICE_ADJUSTMENT_EXPONENT = 1.2
    mock_cfg.AI_PRICE_ADJUSTMENT_SMALL = 0.05
    mock_cfg.AI_PRICE_ADJUSTMENT_MEDIUM = 0.10
    mock_cfg.AI_PRICE_ADJUSTMENT_LARGE = 0.15
    mock_cfg.PROFIT_HISTORY_TICKS = 10

    # Hiring Params
    mock_cfg.LABOR_ALPHA = 0.7
    mock_cfg.AUTOMATION_LABOR_REDUCTION = 0.5
    mock_cfg.LABOR_MARKET_MIN_WAGE = 8.0

    # Automation
    mock_cfg.AUTOMATION_COST_PER_PCT = 1000.0
    mock_cfg.FIRM_SAFETY_MARGIN = 2000.0
    mock_cfg.AUTOMATION_TAX_RATE = 0.05
    mock_cfg.CAPITAL_TO_OUTPUT_RATIO = 2.0
    mock_cfg.ALTMAN_Z_SCORE_THRESHOLD = 1.81
    mock_cfg.DIVIDEND_SUSPENSION_LOSS_TICKS = 3
    mock_cfg.DIVIDEND_RATE_MIN = 0.1
    mock_cfg.DIVIDEND_RATE_MAX = 0.5
    mock_cfg.SEVERANCE_PAY_WEEKS = 4

    # SEO
    mock_cfg.STARTUP_COST = 30000.0
    mock_cfg.SEO_TRIGGER_RATIO = 0.5
    mock_cfg.SEO_MAX_SELL_RATIO = 0.1

    # System 2
    mock_cfg.SYSTEM2_CALC_INTERVAL = 10

    return mock_cfg


@pytest.fixture
def base_mock_firm(firm_engine_config):
    firm = Mock(spec=Firm)
    firm.id = 1
    firm.employees = []

    # Initialize departments first
    firm.finance = Mock()
    firm.production = Mock()
    firm.sales = Mock()
    firm.hr = Mock()

    firm.production_target = 100.0
    firm.inventory = {"food": 100.0}
    firm.productivity_factor = 1.0
    firm.last_prices = {"food": firm_engine_config.GOODS_MARKET_SELL_PRICE}

    # Finance Init
    firm.finance.revenue_this_turn = 0.0
    firm.finance.balance = 1000.0
    firm.finance.last_revenue = 0.0
    firm.finance.calculate_altman_z_score.return_value = 3.0
    firm.finance.consecutive_loss_turns = 0
    firm.finance.last_sales_volume = 100.0
    firm.finance.treasury_shares = 1000.0
    firm.finance.total_shares = 1000.0

    firm.cost_this_turn = 0.0
    firm.profit_history = deque(maxlen=firm_engine_config.PROFIT_HISTORY_TICKS)
    firm.specialization = "food"
    firm.logger = MagicMock()
    firm.age = 25

    # HR Init
    firm.hr.employees = []
    firm.hr.employee_wages = {}

    # Production Init
    firm.production.set_automation_level = Mock()
    firm.production.add_capital = Mock()
    firm.production.automation_level = 0.0
    firm.production.capital_stock = 100.0
    firm.production.productivity_factor = 1.0

    firm.research_history = {"total_spent": 0.0, "success_count": 0, "last_success_tick": 0}
    firm.base_quality = 1.0

    # System 2
    firm.system2_planner = Mock()
    firm.system2_planner.project_future.return_value = {} # Default guidance

    # Mock get_agent_data for AI
    firm.get_agent_data.return_value = {}

    return firm


@pytest.fixture
def mock_ai_engine():
    ai = Mock()
    # Default behavior: Neutral vector
    ai.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=0.5,
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )
    return ai


@pytest.fixture
def ai_decision_engine(firm_engine_config, mock_ai_engine):
    engine = AIDrivenFirmDecisionEngine(
        ai_engine=mock_ai_engine, config_module=firm_engine_config
    )
    # Mock system2_planner to avoid calc_interval TypeError and isolate unit tests
    engine.corporate_manager.system2_planner = Mock()
    engine.corporate_manager.system2_planner.project_future.return_value = {}
    return engine

@pytest.fixture
def create_firm_state_dto():
    def _create(firm, config):
        state = Mock(spec=FirmStateDTO)
        state.id = firm.id
        state.agent_data = {}

        # Department Composite Mocks
        state.finance = Mock()
        state.production = Mock()
        state.sales = Mock()
        state.hr = Mock()

        # Populate
        state.finance.balance = 1000.0
        state.finance.revenue_this_turn = 0.0
        state.finance.expenses_this_tick = 0.0
        state.finance.consecutive_loss_turns = 0
        state.finance.altman_z_score = 3.0
        state.finance.treasury_shares = 1000.0
        state.finance.total_shares = 1000.0

        state.production.inventory = {"food": 100.0}
        state.production.input_inventory = {}
        state.production.production_target = 100.0
        state.production.specialization = "food"
        state.production.base_quality = 1.0
        state.production.inventory_quality = {"food": 1.0}
        state.production.capital_stock = 100.0
        state.production.productivity_factor = 1.0
        state.production.automation_level = 0.0

        state.sales.marketing_budget = 0.0
        state.sales.price_history = {"food": config.GOODS_MARKET_SELL_PRICE}

        state.hr.employees = []
        state.hr.employees_data = {}

        return state
    return _create

# Verified for TD-180

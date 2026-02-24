import sys
from unittest.mock import Mock, MagicMock, patch
import pytest

# Mock missing dependencies for CI/Sandbox environments
for module_name in ["numpy", "yaml", "joblib", "sklearn", "sklearn.linear_model", "sklearn.feature_extraction", "sklearn.preprocessing", "websockets", "streamlit", "pydantic", "fastapi", "fastapi.testclient", "uvicorn", "httpx", "starlette", "starlette.websockets", "starlette.status"]:
    if module_name in sys.modules:
        continue
    try:
        __import__(module_name)
    except ImportError:
        mock = MagicMock()
        # IMPORTANT: Setting __path__ = [] allows the mock to be treated as a package,
        # supporting submodule imports like 'websockets.asyncio'.
        mock.__path__ = []  # Ensure it is treated as a package
        mock.__spec__ = None # Ensure it satisfies import system expectations

        if module_name == "numpy":
            mock.bool_ = bool
            mock.float64 = float
            mock.max.return_value = 0

            def _mock_array_factory(*args, **kwargs):
                m = MagicMock()
                m.shape = (0,)
                return m

            mock.zeros.side_effect = _mock_array_factory
            mock.array.side_effect = _mock_array_factory

        if module_name == "yaml":
            mock.safe_load.return_value = {}

        if module_name == "pydantic":
            # Mock BaseModel to allow inheritance
            mock.BaseModel = MagicMock
            mock.Field = MagicMock(return_value=None)
            mock.validator = MagicMock(return_value=lambda x: x)

        sys.modules[module_name] = mock

import config
from simulation.agents.government import Government
from modules.finance.system import FinanceSystem
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY
from modules.finance.api import ISettlementSystem, IMonetaryAuthority

@pytest.fixture(autouse=True)
def mock_platform_lock_manager(request):
    """Mocks PlatformLockManager methods globally to prevent file locking during tests."""
    # Allow tests to opt-out of this mock (e.g., unit tests for the lock manager itself)
    if request.node.get_closest_marker("no_lock_mock"):
        yield
        return

    # Patch the methods on the class itself to handle all import variations
    with patch('modules.platform.infrastructure.lock_manager.PlatformLockManager.acquire') as mock_acquire, \
         patch('modules.platform.infrastructure.lock_manager.PlatformLockManager.release') as mock_release:
        yield

@pytest.fixture(autouse=True)
def mock_fcntl():
    """Mocks fcntl to prevent file locking during tests."""
    # We patch the fcntl module used in initializer.py
    # If the system doesn't have fcntl, it might be None, so we patch carefully.
    # Note: With mock_platform_lock_manager, this might be redundant but safe to keep for now.
    import simulation.initialization.initializer
    with patch('simulation.initialization.initializer.fcntl', create=True) as mock_fcntl:
        if mock_fcntl:
            mock_fcntl.flock = Mock()
            mock_fcntl.LOCK_EX = 2
            mock_fcntl.LOCK_NB = 4
        yield mock_fcntl

@pytest.fixture
def mock_config():
    """Provides a mock config object for testing."""
    # Use MagicMock with spec=config to enforce interface fidelity
    mock_config = MagicMock(spec=config)

    # Attributes existing in config.py (verified or assumed based on usage)
    mock_config.INCOME_TAX_RATE = 0.1
    mock_config.CORPORATE_TAX_RATE = 0.2
    mock_config.SALES_TAX_RATE = 0.05
    mock_config.TICKS_PER_YEAR = 100
    mock_config.CB_INFLATION_TARGET = 0.02
    mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    mock_config.TAX_BRACKETS = []
    mock_config.STARTUP_GRACE_PERIOD_TICKS = 24
    mock_config.ALTMAN_Z_SCORE_THRESHOLD = 1.81
    mock_config.BAILOUT_REPAYMENT_RATIO = 0.5

    # Attributes likely not in config.py (Legacy/Hidden)
    mock_config.WEALTH_TAX_BRACKETS = [(100000, 0.01)]
    mock_config.CAPITAL_GAINS_TAX_RATE = 0.1
    mock_config.GOVERNMENT_SPENDING_INTERVAL = 10
    mock_config.DEBT_CEILING_GDP_RATIO = 2.0
    mock_config.FISCAL_POLICY_ADJUSTMENT_SPEED = 0.1
    mock_config.AUTO_COUNTER_CYCLICAL_ENABLED = True
    mock_config.FISCAL_SENSITIVITY_ALPHA = 0.5
    mock_config.DEBT_RISK_PREMIUM_TIERS = {1.2: 0.05, 0.9: 0.02, 0.6: 0.005}
    mock_config.BOND_MATURITY_TICKS = 400
    mock_config.QE_INTERVENTION_YIELD_THRESHOLD = 0.10
    mock_config.BAILOUT_PENALTY_PREMIUM = 0.05

    # New Fiscal Policy Constants (WO-IMPL-CONFIG-SCALING)
    mock_config.FISCAL_TAX_RATE_MIN = 0.05
    mock_config.FISCAL_TAX_RATE_MAX = 0.60
    mock_config.DEBT_CEILING_HARD_LIMIT_RATIO = 1.5

    return mock_config

@pytest.fixture
def mock_tracker():
    """Provides a mock economic tracker."""
    tracker = Mock()
    return tracker

@pytest.fixture
def mock_central_bank(mock_tracker, mock_config):
    """Provides a mock CentralBank."""
    # Using a real instance might be better if its logic is simple
    # but for now, a mock is sufficient.
    cb = Mock()
    cb.get_base_rate.return_value = 0.02
    return cb

@pytest.fixture
def mock_bank():
    """Provides a mock commercial Bank."""
    bank = Mock()
    bank._assets = 5000000.0
    return bank

@pytest.fixture
def finance_system(mock_central_bank, mock_bank, mock_config):
    """Provides a mocked FinanceSystem attached to a mock government."""
    # We create a mock government shell first for the FinanceSystem constructor
    mock_gov_shell = Mock()
    system = FinanceSystem(mock_gov_shell, mock_central_bank, mock_bank, mock_config)
    # Spy on the real methods so we can assert calls if needed
    system.issue_treasury_bonds = MagicMock(wraps=system.issue_treasury_bonds)
    # Unconditionally wrap grant_bailout_loan (it exists, deprecated or not)
    system.grant_bailout_loan = MagicMock(wraps=system.grant_bailout_loan)
    system.evaluate_solvency = MagicMock(wraps=system.evaluate_solvency)
    return system

@pytest.fixture
def government(mock_config, mock_tracker, finance_system):
    """
    Provides a Government agent instance with a mocked FinanceSystem.
    The FinanceSystem itself has mocked dependencies (Bank, CentralBank).
    """
    # Refactored Government constructor no longer takes tracker or initial_assets
    gov = Government(id=1, config_module=mock_config)
    # Set initial assets directly using a literal, avoiding non-existent config attribute
    gov._assets = 1000000.0

    # Replace the real finance system with our mocked one
    gov.finance_system = finance_system
    # The FinanceSystem was created with a shell, now we link it to the real government instance
    gov.finance_system.government = gov

    # Inject Mock SettlementSystem (Strict)
    # Uses ISettlementSystem to ensure Government only accesses standard methods
    gov.settlement_system = MagicMock(spec=ISettlementSystem)
    gov.settlement_system.transfer.return_value = True

    return gov

@pytest.fixture
def settlement_system():
    """Provides a SettlementSystem instance."""
    from simulation.systems.settlement_system import SettlementSystem
    return SettlementSystem()

@pytest.fixture
def strict_settlement_mock():
    """Provides a strict mock of the basic Settlement System."""
    return MagicMock(spec=ISettlementSystem)

@pytest.fixture
def strict_monetary_authority_mock():
    """Provides a strict mock of the Monetary Authority."""
    return MagicMock(spec=IMonetaryAuthority)

@pytest.fixture
def config_manager(mock_config, tmp_path):
    """Provides a ConfigManager instance."""
    from modules.common.config.impl import ConfigManagerImpl
    return ConfigManagerImpl(config_dir=tmp_path, legacy_config=mock_config)

@pytest.fixture
def default_market_context():
    """Provides a default MarketContextDTO fixture."""
    return MarketContextDTO(
        exchange_rates={DEFAULT_CURRENCY: 1.0, "EUR": 1.1},
        benchmark_rates={"cpi": 1.0, "central_bank_rate": 0.05}
    )

# ============================================================================
# 🌟 Golden Fixture Support (Auto-Generated Mocks from Real Data)
# ============================================================================
# Usage:
#   1. Run simulation and harvest: python scripts/fixture_harvester.py
#   2. Use in tests: def test_something(golden_households, golden_firms): ...
# ============================================================================

import os
from pathlib import Path

GOLDEN_FIXTURES_DIR = Path(__file__).parent / "integration" / "goldens"


def _get_golden_loader(fixture_name: str = "demo_fixture.json"):
    """Helper to load a golden fixture file."""
    from scripts.fixture_harvester import GoldenLoader
    
    fixture_path = GOLDEN_FIXTURES_DIR / fixture_name
    if not fixture_path.exists():
        return None
    return GoldenLoader.load(str(fixture_path))


@pytest.fixture
def golden_households():
    """
    Provides household mocks loaded from golden fixture data.
    Falls back to empty list if no fixture exists.
    
    Usage:
        def test_household_behavior(golden_households):
            assert len(golden_households) > 0
            assert golden_households[0].assets > 0
    """
    loader = _get_golden_loader()
    if loader is None:
        return []
    return loader.create_household_mocks()


@pytest.fixture
def golden_firms():
    """
    Provides firm mocks loaded from golden fixture data.
    Falls back to empty list if no fixture exists.
    
    Usage:
        def test_firm_behavior(golden_firms):
            firm = golden_firms[0]
            snapshot = firm.get_financial_snapshot()
            assert snapshot["total_assets"] > 0
    """
    loader = _get_golden_loader()
    if loader is None:
        return []
    return loader.create_firm_mocks()


@pytest.fixture
def golden_config():
    """
    Provides config mock loaded from golden fixture data.
    Falls back to None if no fixture exists.
    """
    loader = _get_golden_loader()
    if loader is None:
        return None
    return loader.create_config_mock()

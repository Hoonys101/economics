import sys
from unittest.mock import Mock, MagicMock, patch
import pytest

# Mock missing dependencies for CI/Sandbox environments
for module_name in ["numpy", "yaml", "joblib", "sklearn", "sklearn.linear_model", "sklearn.feature_extraction", "sklearn.preprocessing"]:
    try:
        __import__(module_name)
    except ImportError:
        sys.modules[module_name] = MagicMock()

from simulation.agents.government import Government
from modules.finance.system import FinanceSystem

@pytest.fixture(autouse=True)
def mock_fcntl():
    """Mocks fcntl to prevent file locking during tests."""
    # We patch the fcntl module used in initializer.py
    # If the system doesn't have fcntl, it might be None, so we patch carefully.
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
    config = Mock()
    config.GOVERNMENT_INITIAL_ASSETS = 1000000.0
    config.INCOME_TAX_RATE = 0.1
    config.CORPORATE_TAX_RATE = 0.2
    config.SALES_TAX_RATE = 0.05
    config.WEALTH_TAX_BRACKETS = [(100000, 0.01)]
    config.CAPITAL_GAINS_TAX_RATE = 0.1
    config.GOVERNMENT_SPENDING_INTERVAL = 10
    config.DEBT_CEILING_GDP_RATIO = 2.0
    config.FISCAL_POLICY_ADJUSTMENT_SPEED = 0.1
    config.AUTO_COUNTER_CYCLICAL_ENABLED = True
    config.TICKS_PER_YEAR = 100
    config.FISCAL_SENSITIVITY_ALPHA = 0.5
    config.CB_INFLATION_TARGET = 0.02
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.TAX_BRACKETS = []

    # For FinanceSystem
    config.STARTUP_GRACE_PERIOD_TICKS = 24
    config.ALTMAN_Z_SCORE_THRESHOLD = 1.81
    config.DEBT_RISK_PREMIUM_TIERS = {1.2: 0.05, 0.9: 0.02, 0.6: 0.005}
    config.BOND_MATURITY_TICKS = 400
    config.QE_INTERVENTION_YIELD_THRESHOLD = 0.10
    config.BAILOUT_PENALTY_PREMIUM = 0.05
    config.BAILOUT_REPAYMENT_RATIO = 0.5

    return config

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
    gov._assets = mock_config.GOVERNMENT_INITIAL_ASSETS

    # Replace the real finance system with our mocked one
    gov.finance_system = finance_system
    # The FinanceSystem was created with a shell, now we link it to the real government instance
    gov.finance_system.government = gov

    # Inject Mock SettlementSystem
    gov.settlement_system = Mock()
    gov.settlement_system.transfer.return_value = True

    return gov

@pytest.fixture
def settlement_system():
    """Provides a SettlementSystem instance."""
    from simulation.systems.settlement_system import SettlementSystem
    return SettlementSystem()

@pytest.fixture
def config_manager(mock_config, tmp_path):
    """Provides a ConfigManager instance."""
    from modules.common.config.impl import ConfigManagerImpl
    return ConfigManagerImpl(config_dir=tmp_path, legacy_config=mock_config)

@pytest.fixture
def default_market_context():
    """Provides a default MarketContextDTO fixture."""
    from modules.system.api import DEFAULT_CURRENCY
    return {
        "exchange_rates": {DEFAULT_CURRENCY: 1.0, "EUR": 1.1},
        "benchmark_rates": {"cpi": 1.0, "central_bank_rate": 0.05}
    }

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

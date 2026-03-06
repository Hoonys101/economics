import sys
from unittest.mock import Mock, MagicMock, patch
import pytest
import time
import os

# HOTFIX: Resolve Pytest 9.0.2 NameError in unraisableexception.py
try:
    import _pytest.unraisableexception
    if hasattr(_pytest.unraisableexception, "cleanup") and not hasattr(_pytest.unraisableexception, "gc_collect_iterations_key"):
        # Inject the missing key to prevent NameError during teardown
        from _pytest.stash import StashKey
        _pytest.unraisableexception.gc_collect_iterations_key = StashKey[int]()
        print("DEBUG: [conftest.py] Applied hotfix for _pytest.unraisableexception.gc_collect_iterations_key")
except (ImportError, AttributeError):
    pass

from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.agents.central_bank import CentralBank
from simulation.bank import Bank
from mem_observer import observer

print(f"DEBUG: [conftest.py] Root conftest loading at {time.strftime('%H:%M:%S')}")

import importlib.util

# Mock missing dependencies for CI/Sandbox environments
# Note: "numpy" is included here to allow collection in envs where it's missing.
# However, if numpy is missing, tests relying on actual array operations will fail at runtime.
# This loop only mocks if the module cannot be imported.
for module_name in ["yaml", "joblib", "sklearn", "sklearn.linear_model", "sklearn.feature_extraction", "sklearn.preprocessing", "websockets", "streamlit", "pydantic", "fastapi", "fastapi.testclient", "uvicorn", "httpx", "starlette", "starlette.websockets", "starlette.status", "numpy"]:
    if module_name in sys.modules:
        continue

    # We use importlib.util.find_spec to quickly check if a module exists.
    # We only check the base module to avoid performance issues.
    base_module = module_name.split(".")[0]

    # Note: find_spec might not work perfectly for all namespace packages, but works well for most missing ones
    try:
        spec = importlib.util.find_spec(base_module)
        if spec is not None:
            # It's installed, let the real import happen later.
            continue
    except ValueError:
        # ValueError: sklearn.__spec__ is None (can happen if it is already partially loaded/mocked incorrectly)
        # We will fallback to the import test
        try:
            __import__(module_name)
            continue
        except ImportError:
            pass

    # ShallowModuleMock restricts deep mock chaining on standard attribute access
    # while supporting module import behaviors (__path__, __spec__).
    class ShallowModuleMock(MagicMock):
        def __getattr__(self, name):
            if name.startswith("_"):
                return super().__getattr__(name)
            # Create a TERMINAL mock that does NOT chain further
            mock_obj = Mock(return_value=None)  # Mock, not MagicMock
            object.__setattr__(self, name, mock_obj)
            return mock_obj

    mock = ShallowModuleMock()
    # IMPORTANT: Setting __path__ = [] allows the mock to be treated as a package,
    # supporting submodule imports like 'websockets.asyncio'.
    mock.__path__ = []  # Ensure it is treated as a package
    mock.__spec__ = None # Ensure it satisfies import system expectations
    mock.__name__ = module_name # Prevent AttributeError for __name__

    if module_name == "yaml":
        mock.safe_load.return_value = {}

    if module_name == "pydantic":
        # Mock BaseModel to allow inheritance
        mock.BaseModel = MagicMock
        mock.Field = MagicMock(return_value=None)
        mock.validator = MagicMock(return_value=lambda x: x)

    if module_name == "numpy":
        # Create a mock bool_ class for isinstance checks
        class MockBool(int): pass
        mock.bool_ = MockBool
        # Avoid strictly typing with list which breaks numpy attribute access.
        # However, to prevent runaway Mock trees on arithmetic, you can configure return values
        # if specific tests exhibit infinite chaining, though MagicMock defaults are usually fine
        # if not returning `self`.

    sys.modules[module_name] = mock

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Take a memory snapshot before each test."""
    observer.take_snapshot(f"PRE_{item.name}")

print(f"DEBUG: [conftest.py] Import phase complete at {time.strftime('%H:%M:%S')}")

import config
from simulation.agents.government import Government
from modules.finance.system import FinanceSystem
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY
from modules.finance.api import ISettlementSystem, IMonetaryAuthority, ILiquidityOracle

# def pytest_collect_file(file_path, parent):
#     """Log file collection progress to help debug hangs."""
#     if file_path.suffix == ".py":
#         print(f"DEBUG: [pytest] Collecting: {file_path}")



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
    tracker = Mock(spec=EconomicIndicatorTracker)
    return tracker

@pytest.fixture
def mock_central_bank(mock_tracker, mock_config):
    """Provides a mock CentralBank."""
    # Using a real instance might be better if its logic is simple
    # but for now, a mock is sufficient.
    cb = Mock(spec=CentralBank)
    cb.get_base_rate.return_value = 0.02
    return cb

@pytest.fixture
def mock_bank():
    """Provides a mock commercial Bank."""
    bank = Mock(spec=Bank)
    bank._assets = 5000000.0
    bank.base_rate = 0.05
    return bank

@pytest.fixture
def finance_system(mock_central_bank, mock_bank, mock_config):
    """Provides a mocked FinanceSystem attached to a mock government."""
    # We create a mock government shell first for the FinanceSystem constructor
    mock_gov_shell = Mock()
    # FinanceSystem uses weakref internally for government.
    # We must keep a strong reference to mock_gov_shell alive so the weakref doesn't die.
    system = FinanceSystem(mock_gov_shell, mock_central_bank, mock_bank, mock_config)
    system._gov_strong_ref = mock_gov_shell  # Prevent garbage collection of the shell

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
    import weakref
    gov.finance_system._government_ref = weakref.ref(gov)

    # Inject Mock SettlementSystem (Strict)
    # Uses ISettlementSystem to ensure Government only accesses standard methods
    gov.settlement_system = MagicMock(spec=ISettlementSystem)
    gov.settlement_system.transfer.return_value = True

    return gov

@pytest.fixture
def settlement_system():
    """Provides a SettlementSystem instance with a mocked Oracle."""
    from simulation.systems.settlement_system import SettlementSystem

    # Create a strict mock for the Oracle
    mock_oracle = MagicMock(spec=ILiquidityOracle)
    # Default behavior: Solvent and Rich
    mock_oracle.check_solvency.return_value = True
    mock_oracle.get_live_balance.return_value = 1_000_000_000 # 10M

    return SettlementSystem(liquidity_oracle=mock_oracle)

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

# ============================================================================
# 🗑️ Global Teardown Hook (Memory Leak Fix)
# ============================================================================
import gc
import weakref

class MockRegistry:
    """Tracks instantiated mocks to prevent GC scanning overhead."""
    _active_mocks = weakref.WeakSet()

    @classmethod
    def register(cls, mock_obj):
        if isinstance(mock_obj, (Mock, MagicMock)):
            cls._active_mocks.add(mock_obj)
        return mock_obj

    @classmethod
    def reset_all(cls):
        for m in list(cls._active_mocks):
            try:
                m.reset_mock()
            except Exception:
                pass
        cls._active_mocks.clear()

# AUTOMATION: Hook into unittest.mock.patch to auto-register
import unittest.mock

# Create an object proxy patch rather than fully overwriting unittest.mock.patch
# Overwriting unittest.mock.patch completely breaks pytest-mock since it tries to access attributes on it
class PatchWrapper:
    def __init__(self, original_patch):
        self._original_patch = original_patch

    def __call__(self, *args, **kwargs):
        p = self._original_patch(*args, **kwargs)
        _orig_start = p.start
        def _wrapped_start(*s_args, **s_kwargs):
            mock_obj = _orig_start(*s_args, **s_kwargs)
            MockRegistry.register(mock_obj)
            return mock_obj
        p.start = _wrapped_start
        return p

    def __getattr__(self, item):
        return getattr(self._original_patch, item)

unittest.mock.patch = PatchWrapper(unittest.mock.patch)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    """
    Defensively clear global singleton registries and force garbage collection
    to prevent state leaks across test executions.
    """
    MockRegistry.reset_all()

    # Force garbage collection to remove cyclic references
    # Throttled GC: Only run every 5 tests to reduce overhead and prevent teardown instability
    if not hasattr(pytest, "_test_counter"):
        pytest._test_counter = 0
    pytest._test_counter += 1
    
    if pytest._test_counter % 5 == 0:
        gc.collect(1)

    # Try to clear global singleton registries
    try:
        from _internal.registry.api import mission_registry
        from _internal.registry.fixed_commands import fixed_registry
        if hasattr(mission_registry, '_missions') and hasattr(mission_registry._missions, 'clear'):
            mission_registry._missions.clear()
        if hasattr(fixed_registry, '_commands') and hasattr(fixed_registry._commands, 'clear'):
            fixed_registry._commands.clear()
    except (ImportError, AttributeError):
        pass

    # Take post-test snapshot and report delta
    observer.take_snapshot(f"POST_{item.name}")
    observer.report_delta(f"PRE_{item.name}", f"POST_{item.name}")

@pytest.fixture
def mock_world_state():
    """Provides a global mocked WorldState with IWorldStateMetricsProvider methods pre-configured."""
    from modules.system.api import IWorldStateMetricsProvider
    from modules.simulation.dtos.api import MoneySupplyDTO
    from modules.simulation.api import EconomicIndicatorsDTO
    mock = MagicMock(spec=IWorldStateMetricsProvider)

    mock.calculate_total_money.return_value = MoneySupplyDTO(
        total_m2_pennies=1000000,
        system_debt_pennies=0,
        currency="USD"
    )
    mock.get_economic_indicators.return_value = EconomicIndicatorsDTO(
        gdp=100.0,
        cpi=1.0,
        unemployment_rate=5.0
    )
    mock.get_market_panic_index.return_value = 0.0

    return mock

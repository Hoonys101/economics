import pytest
from _typeshed import Incomplete
from collections.abc import Generator

start_time: Incomplete
mock: Incomplete

class MockBool(int): ...

def mock_platform_lock_manager(request) -> Generator[None]:
    """Mocks PlatformLockManager methods globally to prevent file locking during tests."""
def mock_fcntl() -> Generator[Incomplete]:
    """Mocks fcntl to prevent file locking during tests."""
@pytest.fixture
def mock_config():
    """Provides a mock config object for testing."""
@pytest.fixture
def mock_tracker():
    """Provides a mock economic tracker."""
@pytest.fixture
def mock_central_bank(mock_tracker, mock_config):
    """Provides a mock CentralBank."""
@pytest.fixture
def mock_bank():
    """Provides a mock commercial Bank."""
@pytest.fixture
def finance_system(mock_central_bank, mock_bank, mock_config):
    """Provides a mocked FinanceSystem attached to a mock government."""
@pytest.fixture
def government(mock_config, mock_tracker, finance_system):
    """
    Provides a Government agent instance with a mocked FinanceSystem.
    The FinanceSystem itself has mocked dependencies (Bank, CentralBank).
    """
@pytest.fixture
def settlement_system():
    """Provides a SettlementSystem instance with a mocked Oracle."""
@pytest.fixture
def strict_settlement_mock():
    """Provides a strict mock of the basic Settlement System."""
@pytest.fixture
def strict_monetary_authority_mock():
    """Provides a strict mock of the Monetary Authority."""
@pytest.fixture
def config_manager(mock_config, tmp_path):
    """Provides a ConfigManager instance."""
@pytest.fixture
def default_market_context():
    """Provides a default MarketContextDTO fixture."""

GOLDEN_FIXTURES_DIR: Incomplete

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
@pytest.fixture
def golden_firms():
    '''
    Provides firm mocks loaded from golden fixture data.
    Falls back to empty list if no fixture exists.
    
    Usage:
        def test_firm_behavior(golden_firms):
            firm = golden_firms[0]
            snapshot = firm.get_financial_snapshot()
            assert snapshot["total_assets"] > 0
    '''
@pytest.fixture
def golden_config():
    """
    Provides config mock loaded from golden fixture data.
    Falls back to None if no fixture exists.
    """

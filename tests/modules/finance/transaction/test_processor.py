import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List

from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.dtos.settlement_dtos import SettlementResultDTO
from modules.system.api import DEFAULT_CURRENCY

# ==============================================================================
# Mocks & Fixtures
# ==============================================================================

@dataclass
class MockState:
    transactions: List[Transaction]
    agents: dict
    inactive_agents: dict
    government: MagicMock
    settlement_system: MagicMock
    taxation_system: MagicMock
    stock_market: MagicMock
    real_estate_units: list
    market_data: dict
    logger: MagicMock
    time: int
    bank: MagicMock
    central_bank: MagicMock
    shareholder_registry: MagicMock
    effects_queue: list

@pytest.fixture
def mock_handler():
    handler = MagicMock(spec=ITransactionHandler)
    handler.handle.return_value = True
    return handler

@pytest.fixture
def processor():
    config = MagicMock()
    return TransactionProcessor(config)

@pytest.fixture
def state():
    return MockState(
        transactions=[],
        agents={},
        inactive_agents={},
        government=MagicMock(),
        settlement_system=MagicMock(),
        taxation_system=MagicMock(),
        stock_market=MagicMock(),
        real_estate_units=[],
        market_data={},
        logger=MagicMock(),
        time=1,
        bank=MagicMock(),
        central_bank=MagicMock(),
        shareholder_registry=MagicMock(),
        effects_queue=[]
    )

# ==============================================================================
# Tests
# ==============================================================================

def test_processor_dispatch_success(processor, state, mock_handler):
    # Setup
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1,
        total_pennies=1000
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock(), 2: MagicMock()}

    processor.register_handler("goods", mock_handler)

    # Execute
    results = processor.execute(state)

    # Verify
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].amount_settled == 1000.0 # total_pennies

    mock_handler.handle.assert_called_once()
    args, _ = mock_handler.handle.call_args
    assert args[0] == tx # tx passed correctly

def test_processor_dispatch_legacy_price(processor, state, mock_handler):
    """Test fallback to quantity * price if total_pennies is 0."""
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="apple", quantity=2, price=10.0,
        market_id="goods", transaction_type="goods", time=1,
        total_pennies=0 # Legacy case
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock(), 2: MagicMock()}

    processor.register_handler("goods", mock_handler)

    results = processor.execute(state)

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].amount_settled == 20.0 # 2 * 10.0

def test_processor_handler_failure(processor, state, mock_handler):
    """Test that if handler returns False, result is failure."""
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock(), 2: MagicMock()}

    mock_handler.handle.return_value = False
    processor.register_handler("goods", mock_handler)

    results = processor.execute(state)

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].amount_settled == 0.0

def test_processor_handler_exception(processor, state, mock_handler):
    """Test that if handler raises exception, it is caught and result is failure."""
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock(), 2: MagicMock()}

    mock_handler.handle.side_effect = Exception("Boom")
    processor.register_handler("goods", mock_handler)

    results = processor.execute(state)

    assert len(results) == 1
    assert results[0].success is False
    # Should log error
    state.logger.error.assert_called_once()
    assert "Boom" in str(state.logger.error.call_args)

def test_processor_public_manager(processor, state):
    """Test Public Manager routing."""
    tx = Transaction(
        buyer_id=1, seller_id="PUBLIC_MANAGER", item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1,
        total_pennies=500
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock()} # Buyer exists

    pm_handler = MagicMock(spec=ITransactionHandler)
    pm_handler.handle.return_value = True
    processor.register_public_manager_handler(pm_handler)

    results = processor.execute(state)

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].amount_settled == 500.0

    pm_handler.handle.assert_called_once()

def test_processor_public_manager_fail_missing_buyer(processor, state):
    """Test Public Manager routing fails/skips if buyer missing."""
    tx = Transaction(
        buyer_id=999, seller_id="PUBLIC_MANAGER", item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1
    )
    state.transactions = [tx]
    state.agents = {} # Buyer missing

    pm_handler = MagicMock(spec=ITransactionHandler)
    processor.register_public_manager_handler(pm_handler)

    # Fallback to standard dispatch because _handle_public_manager returns None
    # No standard handler -> Warning
    results = processor.execute(state)

    assert len(results) == 0 # No result appended because skipped or warned
    state.logger.warning.assert_called_once_with("No handler for tx type: goods")
    pm_handler.handle.assert_not_called()

def test_processor_public_manager_exception(processor, state):
    """Test exception handling in PM handler."""
    tx = Transaction(
        buyer_id=1, seller_id="PUBLIC_MANAGER", item_id="apple", quantity=1, price=10.0,
        market_id="goods", transaction_type="goods", time=1
    )
    state.transactions = [tx]
    state.agents = {1: MagicMock()}

    pm_handler = MagicMock(spec=ITransactionHandler)
    pm_handler.handle.side_effect = Exception("PM Boom")
    processor.register_public_manager_handler(pm_handler)

    results = processor.execute(state)

    assert len(results) == 1
    assert results[0].success is False
    # Since we use context.logger (which is state.logger), we can verify the call
    state.logger.error.assert_called_once()
    assert "PM Boom" in str(state.logger.error.call_args)

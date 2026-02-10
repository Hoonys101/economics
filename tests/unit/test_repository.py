import pytest
import sqlite3

from simulation.db.database import DatabaseManager
from simulation.db.schema import create_tables
from simulation.db.repository import SimulationRepository
from simulation.dtos import (
    TransactionData,
    AgentStateData,
    MarketHistoryData,
    EconomicIndicatorData,
)
from modules.system.api import DEFAULT_CURRENCY


# Use an in-memory database for testing
@pytest.fixture
def test_repo():
    """Provides a SimulationRepository instance with an in-memory SQLite DB."""
    # This ensures that for each test function, we get a fresh in-memory database
    conn = sqlite3.connect(":memory:")
    create_tables(conn)

    # The repository will use this connection via the DatabaseManager singleton
    # We need to monkeypatch the singleton to use our in-memory connection
    original_conn = (
        DatabaseManager._instance._conn if DatabaseManager._instance else None
    )
    if DatabaseManager._instance is None:
        DatabaseManager._instance = DatabaseManager()
    DatabaseManager._instance._conn = conn

    repo = SimulationRepository()
    yield repo

    # Teardown: close the connection and reset the singleton
    conn.close()
    DatabaseManager._instance._conn = original_conn


def test_save_and_get_simulation_run(test_repo: SimulationRepository):
    """Test saving and retrieving a simulation run."""
    description = "Test Run"
    config_hash = "testhash123"

    run_id = test_repo.runs.save_simulation_run(config_hash, description)
    assert run_id is not None
    assert run_id > 0

    # The repository doesn't have a get method, let's query directly for verification
    cursor = test_repo.conn.cursor()
    cursor.execute("SELECT * FROM simulation_runs WHERE run_id = ?", (run_id,))
    run_data = cursor.fetchone()

    assert run_data is not None
    assert run_data[0] == run_id
    assert run_data[3] == description
    assert run_data[4] == config_hash


def test_save_and_get_agent_state(test_repo: SimulationRepository):
    """Test saving and retrieving an agent's state."""
    agent_state_data = AgentStateData(
        run_id=1,
        time=1,
        agent_id=101,
        agent_type="Household",
        assets=100.0,
        is_active=True,
        is_employed=True,
        employer_id=201,
        needs_survival=0.5,
        needs_labor=0.8,
        inventory_food=10.0,
        current_production=None,
        num_employees=None,
    )
    test_repo.agents.save_agent_state(agent_state_data)

    retrieved_states = test_repo.agents.get_agent_states(
        agent_id=101, start_tick=1, end_tick=1
    )
    assert len(retrieved_states) == 1

    retrieved_state = retrieved_states[0]
    assert retrieved_state["agent_id"] == 101
    assert retrieved_state["assets"] == 100.0 # Changed from 1000.0 to 100.0 to match DTO
    assert retrieved_state["inventory_food"] == 10.0


def test_save_and_get_transaction(test_repo: SimulationRepository):
    """Test saving and retrieving a transaction."""
    transaction_data = TransactionData(
        run_id=1,
        time=1,
        buyer_id=101,
        seller_id=201,
        item_id="food",
        quantity=5.0,
        price=10.0,
        currency=DEFAULT_CURRENCY,
        transaction_type="Goods",
        market_id="goods_market",
    )
    test_repo.markets.save_transaction(transaction_data)

    retrieved_txs = test_repo.markets.get_transactions(
        start_tick=1, end_tick=1, market_id="goods_market"
    )
    assert len(retrieved_txs) == 1

    retrieved_tx = retrieved_txs[0]
    assert retrieved_tx["buyer_id"] == 101
    assert retrieved_tx["item_id"] == "food"
    assert retrieved_tx["price"] == 10.0


def test_save_and_get_economic_indicators(test_repo: SimulationRepository):
    """Test saving and retrieving economic indicators."""
    indicator_data = EconomicIndicatorData(
        run_id=1,
        time=1,
        unemployment_rate=0.05,
        avg_wage=15.0,
        food_avg_price=10.0,
        food_trade_volume=100.0,
        avg_goods_price=12.0,
        total_production=500.0,
        total_consumption=450.0,
        total_household_assets=100000.0,
        total_firm_assets=200000.0,
        total_food_consumption=200.0,
        total_inventory=1000.0,
    )
    test_repo.analytics.save_economic_indicator(indicator_data)

    retrieved_indicators = test_repo.analytics.get_economic_indicators(start_tick=1, end_tick=1)
    assert len(retrieved_indicators) == 1

    retrieved_indicator = retrieved_indicators[0]
    assert retrieved_indicator["unemployment_rate"] == 0.05
    assert retrieved_indicator["total_production"] == 500.0


def test_indexes_created(test_repo: SimulationRepository):
    """Test that performance indexes are created."""
    cursor = test_repo.conn.cursor()
    cursor.execute("PRAGMA index_list('economic_indicators')")
    indexes = cursor.fetchall()
    # Check if 'idx_economic_indicators_time' is present
    # index_list returns tuples like (seq, name, unique, origin, partial)
    index_names = [idx[1] for idx in indexes]
    assert "idx_economic_indicators_time" in index_names

    cursor.execute("PRAGMA index_list('transactions')")
    indexes = cursor.fetchall()
    index_names = [idx[1] for idx in indexes]
    assert "idx_transactions_time" in index_names

    cursor.execute("PRAGMA index_list('agent_states')")
    indexes = cursor.fetchall()
    index_names = [idx[1] for idx in indexes]
    assert "idx_agent_states_time" in index_names

    cursor.execute("PRAGMA index_list('market_history')")
    indexes = cursor.fetchall()
    index_names = [idx[1] for idx in indexes]
    assert "idx_market_history_time" in index_names

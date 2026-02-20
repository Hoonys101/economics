from unittest.mock import MagicMock, Mock
import sys
import os

# Add repo root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.systems.analytics_system import AnalyticsSystem
from simulation.systems.persistence_manager import PersistenceManager
from simulation.dtos import AgentStateData, TransactionData, EconomicIndicatorData
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.models import Transaction
from simulation.world_state import WorldState

def test_analytics_system_purity():
    # Setup
    analytics = AnalyticsSystem()
    mock_repo = MagicMock()
    persistence = PersistenceManager(run_id=1, config_module=MagicMock(), repository=mock_repo)

    # Mock WorldState
    world_state = MagicMock(spec=WorldState)
    world_state.run_id = 1
    world_state.time = 100

    # Mock Household
    hh = MagicMock(spec=Household)
    hh.id = 1
    hh.is_active = True
    hh.get_assets_by_currency.return_value = {"USD": 10000} # 100.00 -> 10000 pennies
    hh.is_employed = True
    hh.employer_id = 2
    hh.needs = {"survival": 0.5}
    hh.get_quantity.return_value = 5.0 # Food

    # Mock Snapshot for Purity
    mock_snapshot = MagicMock()
    mock_snapshot.econ_state.inventory = {"food": 5.0}
    mock_snapshot.econ_state.is_employed = True
    mock_snapshot.econ_state.employer_id = 2
    mock_snapshot.bio_state.needs = {"survival": 0.5, "labor_need": 0.2}
    hh.create_snapshot_dto.return_value = mock_snapshot

    hh.config = MagicMock()
    hh.config.HOURS_PER_TICK = 24.0
    hh.config.SHOPPING_HOURS = 2.0

    # Mock Firm
    firm = MagicMock(spec=Firm)
    firm.id = 2
    firm.is_active = True
    firm.get_assets_by_currency.return_value = {"USD": 500000} # 5000.00 -> 500000 pennies
    firm.get_quantity.return_value = 20.0 # Food inventory
    firm.current_production = 100.0
    # Firm uses get_state_dto
    mock_firm_state = MagicMock()
    mock_firm_state.hr.employees = [1, 3] # 2 employees
    mock_firm_state.production.inventory = {"food": 20.0}
    mock_firm_state.production.current_production = 100.0
    firm.get_state_dto.return_value = mock_firm_state

    world_state.agents = {1: hh, 2: firm}
    world_state.households = [hh]

    # Mock Transactions
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="food", quantity=1.0, price=10.0,
        market_id="goods", transaction_type="purchase", time=100, total_pennies=1000
    )
    world_state.transactions = [tx]

    # Mock Tracker
    mock_tracker = MagicMock()
    mock_tracker.get_latest_indicators.return_value = {
        "unemployment_rate": 0.05,
        "total_household_assets": 100000,
        "total_firm_assets": 500000
    }
    world_state.tracker = mock_tracker
    world_state.household_time_allocation = {1: 8.0}

    # Execution
    agent_states, txs, indicators, history = analytics.aggregate_tick_data(world_state)

    # Validation - Analytics Output
    assert len(agent_states) == 2

    hh_dto = next(d for d in agent_states if d.agent_id == 1)
    assert hh_dto.agent_type == "household"
    assert hh_dto.assets == {"USD": 10000}
    assert hh_dto.inventory_food == 5.0

    firm_dto = next(d for d in agent_states if d.agent_id == 2)
    assert firm_dto.agent_type == "firm"
    assert firm_dto.num_employees == 2

    assert len(txs) == 1
    assert txs[0].buyer_id == 1

    assert indicators.unemployment_rate == 0.05

    # Execution - Persistence Buffering
    persistence.buffer_data(agent_states, txs, indicators, history)

    assert len(persistence.agent_state_buffer) == 2
    assert len(persistence.transaction_buffer) == 1
    assert len(persistence.economic_indicator_buffer) == 1

    print("Analytics System Purity Verified")

if __name__ == "__main__":
    test_analytics_system_purity()

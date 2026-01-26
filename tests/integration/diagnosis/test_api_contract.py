
import pytest
from unittest.mock import MagicMock, patch
from app import app, _build_simulation_update_payload
from simulation.engine import Simulation

@pytest.fixture
def mock_sim_instance():
    sim = MagicMock(spec=Simulation)
    sim.households = []
    sim.firms = []
    sim.markets = {}
    sim.run_id = 1
    return sim

def test_api_payload_structure_gdp(mock_sim_instance):
    """Spec 3: API Payload 구조 및 GDP 매핑 검증"""
    with app.app_context():
        # Mocking get_repository is tricky because it's a global function in app.py
        # but _build_simulation_update_payload instantiates EconomicIndicatorsViewModel(repo)

        # We patch EconomicIndicatorsViewModel in app.py module
        with patch('app.EconomicIndicatorsViewModel') as MockVM:
            mock_vm_instance = MockVM.return_value

            # Setup expected return data
            # get_economic_indicators returns a list of dicts
            mock_vm_instance.get_economic_indicators.return_value = [
                {"total_consumption": 1234.56, "population": 100, "unemployment_rate": 5.0}
            ]

            # Setup other VM methods to avoid failures
            mock_vm_instance.get_wealth_distribution.return_value = {"labels": [], "data": []}
            mock_vm_instance.get_needs_distribution.return_value = {"household": {}, "firm": {}}
            mock_vm_instance.get_sales_by_good.return_value = {}
            mock_vm_instance.get_market_order_book.return_value = []

            # Mock repository call inside helper
            with patch('app.get_repository'):
                # Act
                payload = _build_simulation_update_payload(current_tick=1, sim_instance=mock_sim_instance)

                # Assert
                # 1. Check GDP mapping
                assert "gdp" in payload, "Payload must contain 'gdp' field"
                assert payload["gdp"] == 1234.56, f"Expected gdp 1234.56, got {payload['gdp']}"

                # 2. Check structure
                assert "market_update" in payload
                assert "chart_update" in payload

def test_api_payload_order_book_format(mock_sim_instance):
    """Spec 3: OrderBook 데이터 형식 검증"""
    with app.app_context():
        with patch('app.EconomicIndicatorsViewModel') as MockVM:
            mock_vm_instance = MockVM.return_value

            # Basic indicators needed for payload construction
            mock_vm_instance.get_economic_indicators.return_value = [{"total_consumption": 0}]
            mock_vm_instance.get_wealth_distribution.return_value = {}
            mock_vm_instance.get_needs_distribution.return_value = {"household": {}, "firm": {}}
            mock_vm_instance.get_sales_by_good.return_value = {}

            # Setup Order Book
            expected_orders = [
                {"type": "BID", "item_id": "food", "price": 10.0, "quantity": 5.0, "agent_id": 1},
                {"type": "ASK", "item_id": "food", "price": 12.0, "quantity": 5.0, "agent_id": 101}
            ]
            mock_vm_instance.get_market_order_book.return_value = expected_orders

            with patch('app.get_repository'):
                # Act
                payload = _build_simulation_update_payload(current_tick=1, sim_instance=mock_sim_instance)

                # Assert
                assert "market_update" in payload
                assert "open_orders" in payload["market_update"]

                open_orders = payload["market_update"]["open_orders"]
                assert isinstance(open_orders, list), "open_orders should be a list"
                assert len(open_orders) == 2
                assert open_orders[0]["type"] == "BID"
                assert open_orders[1]["price"] == 12.0

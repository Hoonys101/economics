import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from server import app

def test_websocket_endpoint():
    with patch("server.create_simulation") as mock_create:
        sim_instance = MagicMock()
        mock_create.return_value = sim_instance

        # Mock world state and components
        world_state = MagicMock()
        sim_instance.world_state = world_state
        sim_instance.run_tick = MagicMock()

        world_state.time = 1
        world_state.baseline_money_supply = 1000.0
        world_state.calculate_total_money.return_value = {"USD": 1000.0}

        # Tracker
        tracker = MagicMock()
        world_state.tracker = tracker
        tracker.get_latest_indicators.return_value = {"unemployment_rate": 5.0}
        tracker.get_m2_money_supply.return_value = 1000.0
        tracker.exchange_engine.get_all_rates.return_value = {"USD": 1.0}

        # Government
        gov = MagicMock()
        world_state.governments = [gov]
        gov.gdp_history = [100.0, 105.0]
        gov.sensory_data.inflation_sma = 0.02
        gov.sensory_data.gini_index = 0.3
        gov.ruling_party.name = "BLUE"
        gov.approval_rating = 0.6

        # Ledger
        ledger = MagicMock()
        gov.monetary_ledger = ledger
        ledger.total_money_issued = {"USD": 0.0}
        ledger.total_money_destroyed = {"USD": 0.0}

        # Mock other components to avoid attribute errors
        world_state.central_bank.base_rate = 0.05
        world_state.markets.get.return_value = MagicMock(interest_rate=0.04)

        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                data = websocket.receive_json()

                assert "tick" in data
                assert "timestamp" in data
                assert "system_integrity" in data
                assert "macro_economy" in data
                assert "monetary" in data
                assert "politics" in data

                assert data["tick"] == 1
                assert data["macro_economy"]["gdp_growth"] == 5.0
                assert data["system_integrity"]["m2_leak"] == 0.0
                assert data["politics"]["party"] == "BLUE"

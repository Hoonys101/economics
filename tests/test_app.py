import pytest
from unittest.mock import patch, MagicMock
import json

from app import app
import config


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {config.SECRET_TOKEN}"}


def test_get_config(client):
    """Test the GET /api/config endpoint."""
    rv = client.get("/api/config")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "NUM_HOUSEHOLDS" in data
    assert data["NUM_HOUSEHOLDS"] == config.NUM_HOUSEHOLDS


def test_set_config_valid_token(client, auth_headers):
    """Test the POST /api/config endpoint with a valid token."""
    data = {"NUM_HOUSEHOLDS": 50}
    rv = client.post(
        "/api/config",
        headers=auth_headers,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert config.NUM_HOUSEHOLDS == 50


def test_set_config_invalid_token(client):
    """Test the POST /api/config endpoint with an invalid token."""
    headers = {"Authorization": "Bearer invalid-token"}
    data = {"NUM_HOUSEHOLDS": 50}
    rv = client.post(
        "/api/config",
        headers=headers,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert rv.status_code == 401


def test_start_simulation(client, auth_headers):
    """Test the POST /api/simulation/start endpoint."""
    rv = client.post("/api/simulation/start", headers=auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"


def test_pause_simulation(client, auth_headers):
    """Test the POST /api/simulation/pause endpoint."""
    client.post("/api/simulation/start", headers=auth_headers)
    rv = client.post("/api/simulation/pause", headers=auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"


def test_stop_simulation(client, auth_headers):
    """Test the POST /api/simulation/stop endpoint."""
    client.post("/api/simulation/start", headers=auth_headers)
    rv = client.post("/api/simulation/stop", headers=auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"


def test_reset_simulation(client, auth_headers):
    """Test the POST /api/simulation/reset endpoint."""
    rv = client.post("/api/simulation/reset", headers=auth_headers)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"


@patch("app.get_repository")
def test_get_economic_indicators_api(mock_get_repository, client):
    """Test the GET /api/economic_indicators endpoint."""
    mock_repo = MagicMock()
    mock_repo.get_economic_indicators.return_value = [{"tick": 1, "gdp": 1000}]
    mock_get_repository.return_value = mock_repo

    rv = client.get("/api/economic_indicators")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 1
    assert data[0]["gdp"] == 1000


@patch("app.get_repository")
def test_get_market_history_api(mock_get_repository, client):
    """Test the GET /api/market_history/<market_id> endpoint."""
    mock_repo = MagicMock()
    mock_repo.get_market_history.return_value = [{"tick": 1, "price": 10}]
    mock_get_repository.return_value = mock_repo

    rv = client.get("/api/market_history/food_market")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 1
    assert data[0]["price"] == 10


@patch("app.get_repository")
def test_get_agent_state_api(mock_get_repository, client):
    """Test the GET /api/agent_state/<agent_id> endpoint."""
    mock_repo = MagicMock()
    mock_repo.get_agent_states.return_value = [{"tick": 1, "assets": 100}]
    mock_get_repository.return_value = mock_repo

    rv = client.get("/api/agent_state/1")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 1
    assert data[0]["assets"] == 100


@patch("app.get_repository")
def test_get_transactions_api(mock_get_repository, client):
    """Test the GET /api/market/transactions endpoint."""
    mock_repo = MagicMock()
    mock_repo.get_transactions.return_value = [{"tick": 1, "price": 10}]
    mock_get_repository.return_value = mock_repo

    rv = client.get("/api/market/transactions")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) == 1
    assert data[0]["price"] == 10
import pytest
from unittest.mock import MagicMock
from simulation.orchestration.agent_service import AgentService
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.simulation.api import IAgent

# Helper to attach attributes to mock since spec=Class prevents setting new attributes
def create_mock_household(id):
    h = MagicMock(spec=Household)
    h.id = id
    h.is_active = True
    h.total_wealth = 5000
    h.labor_income_this_tick = 200

    # Mocking internal state objects
    econ = MagicMock()
    econ.consumption_expenditure_this_tick_pennies = 150
    h._econ_state = econ

    bio = MagicMock()
    bio.needs = {"food": 0.5}
    h._bio_state = bio

    h.inventory = {"apple": 2}
    h.employer_id = 201
    h.current_wage = 1000
    h.age = 30

    return h

def create_mock_firm(id):
    f = MagicMock(spec=Firm)
    f.id = id
    f.is_active = True
    f.total_wealth = 10000

    fin = MagicMock()
    fin.revenue_this_turn = {"USD": 500}
    fin.expenses_this_tick = {"USD": 300}
    f.finance_state = fin

    hr = MagicMock()
    hr.employees = [MagicMock(), MagicMock()]
    f.hr_state = hr

    f.sector = "FOOD"
    f.current_production = 50.0

    return f

@pytest.fixture
def mock_simulation():
    sim = MagicMock()
    sim.world_state = MagicMock()
    return sim

@pytest.fixture
def agent_service(mock_simulation):
    return AgentService(mock_simulation)

def test_get_agents_basic_empty(agent_service, mock_simulation):
    mock_simulation.world_state.agents = {}
    result = agent_service.get_agents_basic()
    assert result == []

def test_get_agents_basic_household(agent_service, mock_simulation):
    household = create_mock_household(101)
    mock_simulation.world_state.agents = {101: household}

    result = agent_service.get_agents_basic()
    assert len(result) == 1
    dto = result[0]
    assert dto.id == 101
    assert dto.type == "household"
    assert dto.wealth == 5000
    assert dto.income == 200
    assert dto.expense == 150

def test_get_agents_basic_firm(agent_service, mock_simulation):
    firm = create_mock_firm(201)
    mock_simulation.world_state.agents = {201: firm}

    result = agent_service.get_agents_basic()
    assert len(result) == 1
    dto = result[0]
    assert dto.id == 201
    assert dto.type == "firm"
    assert dto.wealth == 10000
    assert dto.income == 500
    assert dto.expense == 300

def test_get_agents_basic_inactive(agent_service, mock_simulation):
    agent = create_mock_household(101)
    agent.is_active = False

    mock_simulation.world_state.agents = {101: agent}

    result = agent_service.get_agents_basic()
    assert len(result) == 0

def test_get_agents_basic_limit(agent_service, mock_simulation):
    agents = {}
    for i in range(10):
        agents[i] = create_mock_household(i)

    mock_simulation.world_state.agents = agents

    result = agent_service.get_agents_basic(limit=5)
    assert len(result) == 5

def test_get_agent_detail_household(agent_service, mock_simulation):
    household = create_mock_household(101)
    mock_simulation.world_state.agents = {101: household}

    result = agent_service.get_agent_detail(101)
    assert result is not None
    assert result.id == 101
    assert result.age == 30
    assert result.needs == {"food": 0.5}
    assert result.inventory == {"apple": 2}
    assert result.current_wage == 1000

def test_get_agent_detail_firm(agent_service, mock_simulation):
    firm = create_mock_firm(201)
    mock_simulation.world_state.agents = {201: firm}

    result = agent_service.get_agent_detail(201)
    assert result is not None
    assert result.id == 201
    assert result.sector == "FOOD"
    assert result.employees_count == 2
    assert result.production == 50.0

def test_get_agent_detail_not_found(agent_service, mock_simulation):
    mock_simulation.world_state.agents = {}
    result = agent_service.get_agent_detail(999)
    assert result is None

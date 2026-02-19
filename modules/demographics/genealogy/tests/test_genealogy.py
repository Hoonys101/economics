import pytest
from unittest.mock import MagicMock
from modules.demographics.genealogy.service import GenealogyService
from modules.demographics.genealogy.dtos import AncestorDTO, DescendantDTO, GenealogyTreeDTO
from simulation.core_agents import Household
from modules.system.api import IAgentRegistry
from fastapi.testclient import TestClient
from fastapi import FastAPI
from modules.demographics.genealogy.router import router, get_genealogy_service

# Mock Agent Registry
class MockRegistry:
    def __init__(self, agents):
        self.agents = agents

    def get_agent(self, agent_id):
        return self.agents.get(agent_id)

    def get_all_financial_agents(self):
        return list(self.agents.values())

    def set_state(self, state):
        pass

@pytest.fixture
def mock_registry():
    # Setup a family tree
    # Grandparent (1) -> Parent (2) -> Child (3) -> Grandchild (4)

    # Grandparent
    gp = MagicMock(spec=Household)
    gp.id = 1
    gp.parent_id = None
    gp.children_ids = [2]
    gp.generation = 0
    gp.is_active = False # Dead
    gp.name = "Grandpa"

    # Parent
    p = MagicMock(spec=Household)
    p.id = 2
    p.parent_id = 1
    p.children_ids = [3]
    p.generation = 1
    p.is_active = True
    p.name = "Papa"

    # Child
    c = MagicMock(spec=Household)
    c.id = 3
    c.parent_id = 2
    c.children_ids = [4]
    c.generation = 2
    c.is_active = True
    c.name = "Junior"

    # Grandchild
    gc = MagicMock(spec=Household)
    gc.id = 4
    gc.parent_id = 3
    gc.children_ids = []
    gc.generation = 3
    gc.is_active = True
    gc.name = "Baby"

    agents = {1: gp, 2: p, 3: c, 4: gc}
    return MockRegistry(agents)

def test_get_ancestors(mock_registry):
    service = GenealogyService(mock_registry)

    # Test for Child (3) -> Should get Parent (2) and Grandparent (1)
    ancestors = service.get_ancestors(3)

    assert len(ancestors) == 2
    # Ancestor 0 should be Parent (gap 1)
    assert ancestors[0].id == 2
    assert ancestors[0].generation_gap == 1
    # Ancestor 1 should be Grandparent (gap 2)
    assert ancestors[1].id == 1
    assert ancestors[1].generation_gap == 2
    assert not ancestors[1].is_alive

def test_get_descendants(mock_registry):
    service = GenealogyService(mock_registry)

    # Test for Parent (2) -> Should get Child (3) and Grandchild (4)
    descendants = service.get_descendants(2)

    assert len(descendants) == 2
    # Order depends on BFS/DFS but BFS is implemented
    ids = [d.id for d in descendants]
    assert 3 in ids
    assert 4 in ids

    # Check gap
    d3 = next(d for d in descendants if d.id == 3)
    assert d3.generation_gap == 1

    d4 = next(d for d in descendants if d.id == 4)
    assert d4.generation_gap == 2

def test_get_tree(mock_registry):
    service = GenealogyService(mock_registry)

    # Test Tree from Parent (2) with depth 2
    # Tree starts at root (2) at depth 0.
    # Child (3) at depth 1.
    # Grandchild (4) at depth 2.
    # Service implementation continues if curr_depth < depth.
    # If depth=2:
    # 0 < 2 -> enqueue children (depth 1)
    # 1 < 2 -> enqueue children (depth 2)
    # 2 < 2 -> False. Don't enqueue children.
    # So grandchild (depth 2) is added to nodes, but its children are not processed.

    tree = service.get_tree(2, depth=2)

    assert tree.root_id == 2
    node_ids = [n.id for n in tree.nodes]
    assert 2 in node_ids
    assert 3 in node_ids
    assert 4 in node_ids

    assert len(tree.nodes) == 3

def test_api_endpoints(mock_registry):
    service = GenealogyService(mock_registry)

    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_genealogy_service] = lambda: service

    client = TestClient(app)

    # Test Ancestors
    resp = client.get("/genealogy/3/ancestors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == 2

    # Test Descendants
    resp = client.get("/genealogy/2/descendants")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    # Test Tree
    resp = client.get("/genealogy/2/tree")
    assert resp.status_code == 200
    data = resp.json()
    assert data["root_id"] == 2
    assert len(data["nodes"]) == 3

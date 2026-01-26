import pytest
import os
from modules.memory.V2.memory_manager import MemoryManager
from modules.memory.V2.storage.file_storage import FileStorage
from modules.memory.V2.dtos import QueryDTO
from tests.helpers.dto_factory import DTOFactory
from tests.mocks.mock_config import MockSimulationConfig

@pytest.fixture
def mock_config():
    return MockSimulationConfig()

@pytest.fixture
def memory_file(tmp_path):
    # Use tmp_path for test isolation
    d = tmp_path / "memory_test"
    d.mkdir()
    return str(d / "test_memory.json")

@pytest.fixture
def storage(memory_file):
    return FileStorage(filepath=memory_file)

@pytest.fixture
def memory_manager(storage):
    return MemoryManager(storage=storage)

class TestMemoryManager:
    def test_add_and_query_record(self, memory_manager):
        record = DTOFactory.create_memory_record(tick=1, agent_id=1, event_type="buy", data={"item": "food"})
        memory_manager.add_record(record)

        query = QueryDTO(agent_id=1)
        results = memory_manager.query_records(query)

        assert len(results) == 1
        assert results[0].agent_id == 1
        assert results[0].event_type == "buy"
        assert results[0].data["item"] == "food"

    def test_query_filtering(self, memory_manager):
        r1 = DTOFactory.create_memory_record(tick=1, agent_id=1, event_type="buy")
        r2 = DTOFactory.create_memory_record(tick=2, agent_id=2, event_type="buy")
        r3 = DTOFactory.create_memory_record(tick=3, agent_id=1, event_type="sell")

        memory_manager.add_record(r1)
        memory_manager.add_record(r2)
        memory_manager.add_record(r3)

        # Filter by agent
        assert len(memory_manager.query_records(QueryDTO(agent_id=1))) == 2
        # Filter by event type
        assert len(memory_manager.query_records(QueryDTO(event_type="buy"))) == 2
        # Filter by tick
        assert len(memory_manager.query_records(QueryDTO(start_tick=2))) == 2 # 2 and 3

    def test_persistence(self, memory_file):
        # Create one manager, save data
        storage1 = FileStorage(filepath=memory_file)
        mgr1 = MemoryManager(storage=storage1)
        mgr1.add_record(DTOFactory.create_memory_record(tick=10))

        # Create new manager with same file
        storage2 = FileStorage(filepath=memory_file)
        mgr2 = MemoryManager(storage=storage2)

        results = mgr2.query_records(QueryDTO())
        assert len(results) == 1
        assert results[0].tick == 10

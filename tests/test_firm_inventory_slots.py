import pytest
from unittest.mock import MagicMock
from simulation.firms import Firm
from modules.simulation.api import InventorySlot, AgentCoreConfigDTO
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.components.state.firm_state_models import ProductionState

@pytest.fixture
def firm():
    core_config = MagicMock(spec=AgentCoreConfigDTO)
    core_config.id = 1
    core_config.name = "TestFirm"
    core_config.logger = MagicMock()
    core_config.initial_needs = {}
    core_config.memory_interface = None
    core_config.value_orientation = "GROWTH" # Dummy

    config_dto = MagicMock(spec=FirmConfigDTO)
    config_dto.firm_min_production_target = 10.0
    config_dto.ipo_initial_shares = 1000
    config_dto.dividend_rate = 0.1
    config_dto.profit_history_ticks = 50
    config_dto.goods = {}

    firm = Firm(
        core_config=core_config,
        engine=MagicMock(),
        specialization="wood",
        productivity_factor=1.0,
        config_dto=config_dto
    )
    return firm

def test_add_item_main_slot(firm):
    firm.add_item("chair", 10.0, slot=InventorySlot.MAIN)
    assert firm.get_quantity("chair", slot=InventorySlot.MAIN) == 10.0
    assert firm.get_quantity("chair", slot=InventorySlot.INPUT) == 0.0

def test_add_item_input_slot(firm):
    firm.add_item("wood", 50.0, slot=InventorySlot.INPUT)
    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 50.0
    assert firm.get_quantity("wood", slot=InventorySlot.MAIN) == 0.0

def test_quality_averaging_main(firm):
    firm.add_item("chair", 10.0, quality=1.0, slot=InventorySlot.MAIN)
    firm.add_item("chair", 10.0, quality=2.0, slot=InventorySlot.MAIN)

    assert firm.get_quantity("chair", slot=InventorySlot.MAIN) == 20.0
    assert firm.get_quality("chair", slot=InventorySlot.MAIN) == 1.5

def test_quality_averaging_input(firm):
    firm.add_item("wood", 10.0, quality=1.0, slot=InventorySlot.INPUT)
    firm.add_item("wood", 10.0, quality=2.0, slot=InventorySlot.INPUT)

    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 20.0
    assert firm.get_quality("wood", slot=InventorySlot.INPUT) == 1.5
    # Ensure MAIN quality is unaffected (default 1.0)
    assert firm.get_quality("wood", slot=InventorySlot.MAIN) == 1.0

def test_remove_item_input(firm):
    firm.add_item("wood", 50.0, slot=InventorySlot.INPUT)
    result = firm.remove_item("wood", 20.0, slot=InventorySlot.INPUT)

    assert result is True
    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 30.0

def test_remove_item_input_insufficient(firm):
    firm.add_item("wood", 10.0, slot=InventorySlot.INPUT)
    result = firm.remove_item("wood", 20.0, slot=InventorySlot.INPUT)

    assert result is False
    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 10.0

def test_clear_inventory(firm):
    firm.add_item("chair", 10.0, slot=InventorySlot.MAIN)
    firm.add_item("wood", 50.0, slot=InventorySlot.INPUT)

    firm.clear_inventory(slot=InventorySlot.INPUT)

    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 0.0
    assert firm.get_quantity("chair", slot=InventorySlot.MAIN) == 10.0

    firm.clear_inventory(slot=InventorySlot.MAIN)
    assert firm.get_quantity("chair", slot=InventorySlot.MAIN) == 0.0

def test_facade_property(firm):
    firm.add_item("wood", 50.0, slot=InventorySlot.INPUT)
    assert firm.input_inventory["wood"] == 50.0

    # Check that it returns a copy
    firm.input_inventory["wood"] = 0.0
    assert firm.get_quantity("wood", slot=InventorySlot.INPUT) == 50.0

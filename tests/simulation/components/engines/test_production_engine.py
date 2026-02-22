import pytest
from unittest.mock import MagicMock
from simulation.components.engines.production_engine import ProductionEngine
from modules.firm.api import ProductionInputDTO, FirmSnapshotDTO
from modules.simulation.dtos.api import ProductionStateDTO, HRStateDTO
from modules.simulation.dtos.api import FirmConfigDTO

@pytest.fixture
def production_engine():
    return ProductionEngine()

@pytest.fixture
def firm_snapshot():
    snapshot = MagicMock(spec=FirmSnapshotDTO)
    snapshot.id = 1 # ID needed for AgentID

    # Config
    config = MagicMock(spec=FirmConfigDTO)
    config.labor_alpha = 0.5
    config.automation_labor_reduction = 0.5
    config.labor_elasticity_min = 0.1
    config.capital_depreciation_rate = 0.1
    config.goods = {
        "FOOD": {
            "quality_sensitivity": 0.5,
            "inputs": {"RAW_MAT": 2.0}
        }
    }
    snapshot.config = config

    # Production State
    prod = MagicMock(spec=ProductionStateDTO)
    prod.capital_stock = 100.0
    prod.automation_level = 0.2
    prod.production_target = 100.0
    prod.productivity_factor = 1.0
    prod.base_quality = 1.0
    prod.specialization = "FOOD"
    prod.input_inventory = {"RAW_MAT": 1000.0}
    prod.inventory = {} # Finished goods inventory
    snapshot.production = prod

    # HR State
    hr = MagicMock(spec=HRStateDTO)
    hr.employees_data = {
        1: {"skill": 2.0},
        2: {"skill": 2.0}
    }
    snapshot.hr = hr

    return snapshot

def test_produce_success(production_engine, firm_snapshot):
    input_dto = ProductionInputDTO(firm_snapshot=firm_snapshot, productivity_multiplier=1.0)

    result = production_engine.produce(input_dto)

    assert result.success
    # Check depreciation
    # 100.0 * 0.1 = 10.0
    assert result.capital_depreciation == 10.0

    # Check automation decay
    # 0.2 * 0.005 = 0.001
    assert result.automation_decay == pytest.approx(0.001)

    # Check production amount
    # Effective capital = 100 - 10 = 90
    # Effective automation = 0.2 - 0.001 = 0.199
    # Alpha = 0.5 * (1 - (0.199 * 0.5)) = 0.5 * (1 - 0.0995) = 0.5 * 0.9005 = 0.45025
    # Beta = 1 - 0.45025 = 0.54975
    # Labor Skill = 4.0 (2+2)
    # Qty = 1.0 * (4.0 ** 0.45025) * (90 ** 0.54975)

    assert result.quantity_produced > 0.0

    # Check Inputs Consumed
    # inputs: RAW_MAT 2.0 per unit
    expected_consumption = result.quantity_produced * 2.0
    assert result.inputs_consumed["RAW_MAT"] == pytest.approx(expected_consumption)

def test_produce_input_constraint(production_engine, firm_snapshot):
    firm_snapshot.production.input_inventory = {"RAW_MAT": 10.0}

    input_dto = ProductionInputDTO(firm_snapshot=firm_snapshot, productivity_multiplier=1.0)

    result = production_engine.produce(input_dto)

    # Max possible = 10.0 / 2.0 = 5.0
    assert result.quantity_produced == 5.0
    assert result.inputs_consumed["RAW_MAT"] == 10.0

def test_produce_no_employees(production_engine, firm_snapshot):
    firm_snapshot.hr.employees_data = {}

    input_dto = ProductionInputDTO(firm_snapshot=firm_snapshot, productivity_multiplier=1.0)

    result = production_engine.produce(input_dto)

    assert result.quantity_produced == 0.0
    assert result.inputs_consumed == {}

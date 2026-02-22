import pytest
from unittest.mock import MagicMock
from simulation.components.engines.production_engine import ProductionEngine
from modules.firm.api import ProductionInputDTO, FirmSnapshotDTO
from modules.simulation.dtos.api import FirmConfigDTO, ProductionStateDTO, HRStateDTO, FinanceStateDTO, SalesStateDTO

def test_production_integer_depreciation():
    engine = ProductionEngine()

    # Setup
    config = MagicMock(spec=FirmConfigDTO)
    config.capital_depreciation_rate = 0.015 # 1.5%
    config.labor_alpha = 0.5
    config.automation_labor_reduction = 0.5
    config.labor_elasticity_min = 0.1
    config.goods = {"WIDGET": {"quality_sensitivity": 0.5}}

    prod_state = MagicMock(spec=ProductionStateDTO)
    prod_state.capital_stock = 100000 # 100,000 pennies
    prod_state.automation_level = 0.0
    prod_state.production_target = 100.0
    prod_state.specialization = "WIDGET"
    prod_state.base_quality = 1.0
    prod_state.productivity_factor = 1.0
    prod_state.input_inventory = {}
    prod_state.inventory = {}

    hr_state = MagicMock(spec=HRStateDTO)
    hr_state.employees_data = {1: {"skill": 1.0}}

    snapshot = MagicMock(spec=FirmSnapshotDTO)
    snapshot.id = 1
    snapshot.config = config
    snapshot.production = prod_state
    snapshot.hr = hr_state

    input_dto = ProductionInputDTO(
        firm_snapshot=snapshot,
        productivity_multiplier=1.0
    )

    result = engine.produce(input_dto)

    # Expected depreciation: floor(100000 * 0.015) = 1500
    # Or using basis points: floor(100000 * 150 / 10000) = 1500
    assert result.capital_depreciation == 1500
    assert isinstance(result.capital_depreciation, int)

def test_production_deterministic_output():
    engine = ProductionEngine()

    config = MagicMock(spec=FirmConfigDTO)
    config.capital_depreciation_rate = 0.0
    config.labor_alpha = 0.5
    config.automation_labor_reduction = 0.0
    config.labor_elasticity_min = 0.1
    config.goods = {"WIDGET": {"quality_sensitivity": 0.0}}

    prod_state = MagicMock(spec=ProductionStateDTO)
    prod_state.capital_stock = 10000
    prod_state.automation_level = 0.0
    prod_state.production_target = 100.0
    prod_state.specialization = "WIDGET"
    prod_state.base_quality = 1.0
    prod_state.productivity_factor = 1.0
    prod_state.input_inventory = {}
    prod_state.inventory = {}

    hr_state = MagicMock(spec=HRStateDTO)
    # 1 employee, skill 1.0
    hr_state.employees_data = {1: {"skill": 1.0}}

    snapshot = MagicMock(spec=FirmSnapshotDTO)
    snapshot.id = 1
    snapshot.config = config
    snapshot.production = prod_state
    snapshot.hr = hr_state

    input_dto = ProductionInputDTO(
        firm_snapshot=snapshot,
        productivity_multiplier=1.0
    )

    # Logic:
    # labor = 1.0
    # capital = 10000
    # alpha = 0.5, beta = 0.5
    # output = 1.0 * (1.0^0.5) * (10000^0.5) = 1.0 * 1.0 * 100.0 = 100.0

    result = engine.produce(input_dto)

    assert result.quantity_produced == 100.0
    assert result.quantity_produced.is_integer() # Should be float but integer value

def test_production_deterministic_floor():
    """Test that output is floored if fractional."""
    engine = ProductionEngine()

    config = MagicMock(spec=FirmConfigDTO)
    config.capital_depreciation_rate = 0.0
    config.labor_alpha = 0.5
    config.automation_labor_reduction = 0.0
    config.labor_elasticity_min = 0.1
    config.goods = {"WIDGET": {"quality_sensitivity": 0.0}}

    prod_state = MagicMock(spec=ProductionStateDTO)
    prod_state.capital_stock = 100 # sqrt(100) = 10
    prod_state.automation_level = 0.0
    prod_state.production_target = 100.0
    prod_state.specialization = "WIDGET"
    prod_state.base_quality = 1.0
    prod_state.productivity_factor = 1.0
    prod_state.input_inventory = {}
    prod_state.inventory = {}

    hr_state = MagicMock(spec=HRStateDTO)
    # Labor 1.5. sqrt(1.5) ~= 1.2247
    hr_state.employees_data = {1: {"skill": 1.5}}

    snapshot = MagicMock(spec=FirmSnapshotDTO)
    snapshot.id = 1
    snapshot.config = config
    snapshot.production = prod_state
    snapshot.hr = hr_state

    input_dto = ProductionInputDTO(
        firm_snapshot=snapshot,
        productivity_multiplier=1.0
    )

    # Output = 1.0 * sqrt(1.5) * sqrt(100) = 1.2247 * 10 = 12.247
    # Floor(12.247) = 12

    result = engine.produce(input_dto)

    assert result.quantity_produced == 12.0

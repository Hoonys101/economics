import pytest
from unittest.mock import MagicMock
from simulation.components.engines.asset_management_engine import AssetManagementEngine
from modules.firm.api import AssetManagementInputDTO, FirmSnapshotDTO
from modules.simulation.dtos.api import FirmConfigDTO
from modules.simulation.dtos.api import ProductionStateDTO

@pytest.fixture
def asset_mgmt_engine():
    return AssetManagementEngine()

@pytest.fixture
def firm_snapshot():
    snapshot = MagicMock(spec=FirmSnapshotDTO)

    # Mock Config
    config = MagicMock(spec=FirmConfigDTO)
    config.automation_cost_per_pct = 100.0
    config.capital_to_output_ratio = 2.0
    snapshot.config = config

    # Mock Production State
    production = MagicMock(spec=ProductionStateDTO)
    production.automation_level = 0.5
    production.capital_stock = 100.0
    snapshot.production = production

    return snapshot

def test_invest_automation_success(asset_mgmt_engine, firm_snapshot):
    input_dto = AssetManagementInputDTO(
        firm_snapshot=firm_snapshot,
        investment_type="AUTOMATION",
        investment_amount=10000 # Should give 1% automation (0.01)
    )

    result = asset_mgmt_engine.invest(input_dto)

    assert result.success
    assert result.actual_cost == 10000
    assert result.automation_level_increase == pytest.approx(0.01)
    assert result.capital_stock_increase == 0.0

def test_invest_automation_max_cap(asset_mgmt_engine, firm_snapshot):
    firm_snapshot.production.automation_level = 0.99

    input_dto = AssetManagementInputDTO(
        firm_snapshot=firm_snapshot,
        investment_type="AUTOMATION",
        investment_amount=20000 # 2% -> exceed 1.0
    )

    result = asset_mgmt_engine.invest(input_dto)

    assert result.success
    assert result.automation_level_increase == pytest.approx(0.01) # Capped at 1.0 - 0.99
    # In my implementation, I capped the increase but consumed full amount.
    assert result.actual_cost == 20000

def test_invest_capex_success(asset_mgmt_engine, firm_snapshot):
    # efficiency = 1.0 / 2.0 = 0.5
    input_dto = AssetManagementInputDTO(
        firm_snapshot=firm_snapshot,
        investment_type="CAPEX",
        investment_amount=100.0
    )

    result = asset_mgmt_engine.invest(input_dto)

    assert result.success
    assert result.actual_cost == 100.0
    assert result.capital_stock_increase == pytest.approx(50.0) # 100 * 0.5
    assert result.automation_level_increase == 0.0

def test_invest_negative_amount(asset_mgmt_engine, firm_snapshot):
    input_dto = AssetManagementInputDTO(
        firm_snapshot=firm_snapshot,
        investment_type="CAPEX",
        investment_amount=-10.0
    )

    result = asset_mgmt_engine.invest(input_dto)

    assert not result.success
    assert "positive" in result.message

def test_invest_unknown_type(asset_mgmt_engine, firm_snapshot):
    input_dto = AssetManagementInputDTO(
        firm_snapshot=firm_snapshot,
        investment_type="UNKNOWN",
        investment_amount=100.0
    )

    result = asset_mgmt_engine.invest(input_dto)

    assert not result.success
    assert "Unknown investment type" in result.message

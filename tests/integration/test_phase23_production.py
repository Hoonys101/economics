import pytest
import logging
from unittest.mock import MagicMock
from simulation.firms import Firm
from simulation.systems.technology_manager import TechnologyManager
from simulation.systems.technology_manager import TechNode
from simulation.components.production_department import ProductionDepartment

class MockConfig:
    # Firm Defaults
    FIRM_MIN_PRODUCTION_TARGET = 10.0
    FIRM_PRODUCTIVITY_FACTOR = 1.0
    INITIAL_FIRM_LIQUIDITY_NEED = 100.0

    # Production
    LABOR_ALPHA = 0.5 # Simplified
    LABOR_ELASTICITY_MIN = 0.3
    AUTOMATION_LABOR_REDUCTION = 0.5
    CAPITAL_DEPRECIATION_RATE = 0.0
    GOODS = {
        "basic_food": {
            "id": "basic_food",
            "quality_sensitivity": 0.0,
            "inputs": {}
        }
    }

    # Tech
    TECH_FERTILIZER_UNLOCK_TICK = 50
    TECH_DIFFUSION_RATE = 0.05

    # Others
    IPO_INITIAL_SHARES = 1000.0
    DIVIDEND_RATE = 0.3
    BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD = 5
    ASSETS_CLOSURE_THRESHOLD = -1000.0
    FIRM_CLOSURE_TURNS_THRESHOLD = 10
    PROFIT_HISTORY_TICKS = 50

def create_test_firm(id, config):
    firm = Firm(
        id=id,
        initial_capital=1000.0,
        initial_liquidity_need=100.0,
        specialization="basic_food",
        productivity_factor=1.0,
        decision_engine=MagicMock(),
        value_orientation="wealth",
        config_module=config,
        initial_inventory={},
        logger=logging.getLogger(f"firm_{id}"),
        sector="FOOD",
        is_visionary=False
    )
    # Setup for production
    firm.hr = MagicMock()
    firm.hr.employees = [MagicMock()] # 1 employee
    firm.hr.get_total_labor_skill.return_value = 10.0
    firm.hr.get_avg_skill.return_value = 1.0

    firm.capital_stock = 100.0
    firm.automation_level = 0.0

    return firm

def test_production_boost_from_fertilizer_tech():
    config = MockConfig()
    logger = logging.getLogger("test_integration")

    tech_manager = TechnologyManager(config, logger)

    firm_A = create_test_firm(1, config)
    firm_B = create_test_firm(2, config)

    # Ensure identical initial state
    assert firm_A.productivity_factor == firm_B.productivity_factor

    # Unlock tech
    tech_node = tech_manager.tech_tree["TECH_AGRI_CHEM_01"]
    tech_node.is_unlocked = True
    tech_manager.active_techs.append(tech_node.id)

    # Adopt for Firm A
    tech_manager._adopt(firm_A.id, tech_node)

    # Produce
    # Tick doesn't matter much for this logic unless depreciation is high
    tick = 100

    # Firm A Production
    prod_A = firm_A.production.produce(tick, tech_manager)

    # Firm B Production
    prod_B = firm_B.production.produce(tick, tech_manager)

    print(f"Production A: {prod_A}")
    print(f"Production B: {prod_B}")

    # Assertions
    assert prod_B > 0
    assert prod_A == pytest.approx(prod_B * 3.0, rel=0.01)

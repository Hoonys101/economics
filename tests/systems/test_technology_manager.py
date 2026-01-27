import pytest
import logging
from unittest.mock import MagicMock
from simulation.systems.technology_manager import TechnologyManager
from simulation.systems.tech.api import FirmTechInfoDTO

class MockConfig:
    TECH_FERTILIZER_UNLOCK_TICK = 50
    TECH_DIFFUSION_RATE = 0.05

@pytest.fixture
def tech_manager():
    config = MockConfig()
    logger = logging.getLogger("test_tech_manager")
    return TechnologyManager(config, logger)

def test_effective_diffusion_rate(tech_manager):
    # Base rate is 0.05
    # Formula: base * (1 + min(1.5, 0.5 * (HCI - 1.0)))

    # Case 1: HCI = 1.0 -> Boost = 0 -> Rate = 0.05
    tech_manager.human_capital_index = 1.0
    rate = tech_manager._get_effective_diffusion_rate(0.05)
    assert rate == 0.05

    # Case 2: HCI = 3.0 -> Boost = 0.5 * 2.0 = 1.0 -> Rate = 0.05 * 2.0 = 0.10
    tech_manager.human_capital_index = 3.0
    rate = tech_manager._get_effective_diffusion_rate(0.05)
    assert rate == pytest.approx(0.10)

    # Case 3: HCI = 5.0 -> Boost = 0.5 * 4.0 = 2.0 -> capped at 1.5 -> Rate = 0.05 * 2.5 = 0.125
    tech_manager.human_capital_index = 5.0
    rate = tech_manager._get_effective_diffusion_rate(0.05)
    assert rate == pytest.approx(0.125)

def test_unlock_and_visionary_adoption(tech_manager):
    firms = [
        {"id": 1, "sector": "FOOD", "is_visionary": True},
        {"id": 2, "sector": "FOOD", "is_visionary": False},
        {"id": 3, "sector": "MANUFACTURING", "is_visionary": True},
    ]

    # Tick 49: No unlock
    tech_manager.update(49, firms, 1.0)
    assert not tech_manager.active_techs

    # Tick 50: Unlock
    tech_manager.update(50, firms, 1.0)
    assert "TECH_AGRI_CHEM_01" in tech_manager.active_techs

    # Check adoption
    # Firm 1 (Visionary, Food) -> Should adopt
    assert tech_manager.has_adopted(1, "TECH_AGRI_CHEM_01")
    # Firm 2 (Non-Visionary, Food) -> Should NOT adopt immediately
    assert not tech_manager.has_adopted(2, "TECH_AGRI_CHEM_01")
    # Firm 3 (Visionary, Manufacturing) -> Should NOT adopt (wrong sector)
    assert not tech_manager.has_adopted(3, "TECH_AGRI_CHEM_01")

def test_diffusion_over_time(tech_manager):
    firms = [
        {"id": 2, "sector": "FOOD", "is_visionary": False},
    ]

    # Unlock first
    tech_manager.update(50, firms, 1.0)

    # Force high diffusion rate for test reliability or mock random
    # With rate 0.05, probability of NOT adopting in 200 ticks is very low.

    adopted = False
    for i in range(200):
        tech_manager.update(51 + i, firms, 1.0)
        if tech_manager.has_adopted(2, "TECH_AGRI_CHEM_01"):
            adopted = True
            break

    assert adopted

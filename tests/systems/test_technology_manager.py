import pytest
from unittest.mock import MagicMock
from simulation.systems.technology_manager import TechnologyManager, TechNode
from simulation.systems.tech.api import FirmTechInfoDTO


class TestTechnologyManager:
    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        mock_config.TECH_FERTILIZER_UNLOCK_TICK = 30  # Updated default
        mock_config.TECH_DIFFUSION_RATE = 0.10  # Updated default
        return mock_config

    @pytest.fixture
    def manager(self, config):
        return TechnologyManager(config, MagicMock())

    def test_effective_diffusion_rate(self, manager):
        # Base rate = 0.10 (Updated from 0.05)
        # HCI = 1.0 -> Boost = 0 -> Rate = 0.10
        manager.human_capital_index = 1.0
        assert manager._get_effective_diffusion_rate(0.10) == 0.10

        # HCI = 3.0 -> 0.5 * 2.0 = 1.0 -> Boost = 1.0 -> Rate = 0.10 * 2.0 = 0.20
        manager.human_capital_index = 3.0
        assert manager._get_effective_diffusion_rate(0.10) == 0.20

        # HCI = 5.0 -> 0.5 * 4.0 = 2.0 -> Boost = min(1.5, 2.0) = 1.5 -> Rate = 0.10 * 2.5 = 0.25
        manager.human_capital_index = 5.0
        assert manager._get_effective_diffusion_rate(0.10) == 0.25

    def test_unlock_and_visionary_adoption(self, manager):
        # Setup Tech
        tech_id = "TECH_AGRI_CHEM_01"
        tech = manager.tech_tree[tech_id]
        tech.unlock_tick = 30  # Updated check
        tech.sector = "FOOD"

        # Setup Firms DTO
        firms = [
            FirmTechInfoDTO(id=1, sector="FOOD", is_visionary=True),
            FirmTechInfoDTO(id=2, sector="FOOD", is_visionary=False),
            FirmTechInfoDTO(id=3, sector="MANUFACTURING", is_visionary=True),
        ]

        # Tick 29: No unlock
        manager.update(29, firms, 1.0)
        assert not tech.is_unlocked
        assert not manager.has_adopted(1, tech_id)

        # Tick 30: Unlock
        manager.update(30, firms, 1.0)
        assert tech.is_unlocked

        # Visionary Check
        # Firm 1 (Food, Visionary) should adopt
        assert manager.has_adopted(1, tech_id)
        # Firm 2 (Food, Not Visionary) should NOT adopt immediately
        assert not manager.has_adopted(2, tech_id)
        # Firm 3 (Mfg, Visionary) should NOT adopt due to sector mismatch
        assert not manager.has_adopted(3, tech_id)

    def test_diffusion_over_time(self, manager):
        # Setup Tech
        tech_id = "TECH_AGRI_CHEM_01"
        tech = manager.tech_tree[tech_id]
        tech.unlock_tick = 30
        tech.diffusion_rate = 0.0  # No diffusion initially

        firms = [
            FirmTechInfoDTO(id=1, sector="FOOD", is_visionary=False),
        ]

        # Unlock it first (needs unlock call)
        # Note: _unlock_tech also iterates firms, but firm 1 is not visionary, so it won't adopt there.
        manager.update(30, firms, 1.0)
        assert not manager.has_adopted(1, tech_id)  # Not visionary, and diffusion 0%

        # Now enable diffusion
        tech.diffusion_rate = 1.0
        manager.update(31, firms, 1.0)

        assert manager.has_adopted(1, tech_id)

    def test_productivity_multiplier(self, manager):
        # Setup Tech
        tech_id = "TECH_AGRI_CHEM_01"
        tech = manager.tech_tree[tech_id]
        tech.multiplier = 3.0

        # Before adoption
        assert manager.get_productivity_multiplier(1) == 1.0

        # Adopt
        manager._adopt(1, tech)

        # After adoption
        assert manager.get_productivity_multiplier(1) == 3.0

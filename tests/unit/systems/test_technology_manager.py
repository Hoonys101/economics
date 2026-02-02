import pytest
from unittest.mock import MagicMock
from simulation.systems.technology_manager import TechnologyManager, TechNode
from simulation.systems.tech.api import FirmTechInfoDTO

class TestTechnologyManager:
    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        mock_config.TECH_FERTILIZER_UNLOCK_TICK = 30 # Updated default
        mock_config.TECH_DIFFUSION_RATE = 0.10       # Updated default
        mock_config.TECH_UNLOCK_COST_THRESHOLD = 5000.0
        mock_config.TECH_UNLOCK_PROB_CAP = 1.0 # Guarantee unlock for test if threshold met
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

    def test_unlock_mechanism(self, manager):
        # Setup Tech
        tech_id = "TECH_AGRI_CHEM_01"
        tech = manager.tech_tree[tech_id]
        tech.cost_threshold = 100.0
        tech.sector = "FOOD"

        # Setup Firms DTO
        firms = [
            FirmTechInfoDTO(id=1, sector="FOOD", current_rd_investment=60.0),
            FirmTechInfoDTO(id=2, sector="FOOD", current_rd_investment=60.0), # Total 120 > 100
            FirmTechInfoDTO(id=3, sector="MANUFACTURING", current_rd_investment=0.0),
        ]

        # Tick 29: Update
        # Ratio = 120 / 100 = 1.2. Prob = 1.0 (capped)
        manager.update(30, firms, 1.0)

        # It should unlock
        assert tech.is_unlocked

        # Visionary logic removed, so NO immediate adoption expected unless random diffusion happened.
        # But diffusion happens in the same update.
        # If diffusion rate is > 0, some might adopt.
        # To strictly test unlock only, we can set diffusion rate to 0.

    def test_diffusion_over_time(self, manager):
        # Setup Tech
        tech_id = "TECH_AGRI_CHEM_01"
        tech = manager.tech_tree[tech_id]
        tech.diffusion_rate = 0.0 # No diffusion initially
        tech.is_unlocked = True   # Force unlock

        firms = [
            FirmTechInfoDTO(id=1, sector="FOOD", current_rd_investment=0.0),
        ]

        manager.active_techs.append(tech_id) # Manually activate

        manager.update(30, firms, 1.0)
        assert not manager.has_adopted(1, tech_id) # Diffusion 0%

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

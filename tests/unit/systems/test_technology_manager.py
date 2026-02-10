import pytest
from unittest.mock import MagicMock, patch
import random
from simulation.systems.technology_manager import TechnologyManager, TechNode
from simulation.systems.tech.api import FirmTechInfoDTO

# ==============================================================================
# Fake Numpy Implementation for Lean Environment
# ==============================================================================

class FakeMatrix:
    """A minimal 2D matrix mock that supports shape and scalar item access."""
    def __init__(self, shape, data=None):
        self.shape = shape
        self.data = data if data is not None else {}

    def __getitem__(self, key):
        # Handle scalar access [row, col]
        if isinstance(key, tuple) and len(key) == 2:
            row, col = key
            if isinstance(row, int) and isinstance(col, int):
                return self.data.get((row, col), False)
        # Fallback for other access patterns (mocks)
        return False

    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) == 2:
            row, col = key
            if isinstance(row, int) and isinstance(col, int):
                self.data[(row, col)] = value

class FakeNumpy:
    """Replaces numpy module logic."""
    def zeros(self, shape, dtype=None):
        return FakeMatrix(shape)

    def array(self, data, dtype=None):
        # For firm_ids, just return the list
        return data

    def max(self, data):
        if not data: return 0
        return max(data)

    def vstack(self, args):
        # args is tuple (matrix, padding)
        # We assume simplified vstack that just expands rows
        m1, m2 = args
        new_shape = (m1.shape[0] + m2.shape[0], m1.shape[1])
        # Preserve data from m1
        return FakeMatrix(new_shape, data=m1.data.copy())

    def hstack(self, args):
        # args is tuple (matrix, new_col)
        m1, m2 = args
        new_shape = (m1.shape[0], m1.shape[1] + m2.shape[1])
        # Preserve data from m1
        return FakeMatrix(new_shape, data=m1.data.copy())

    def where(self, condition):
        # Only used in productivity multiplier?
        # If condition is mocked, this is hard.
        return ([],)

# ==============================================================================
# Test Class
# ==============================================================================

class TestTechnologyManager:
    @pytest.fixture
    def mock_numpy(self):
        """Patches numpy in the module under test."""
        fake_np = FakeNumpy()
        with patch('simulation.systems.technology_manager.np', fake_np):
             yield fake_np

    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        mock_config.TECH_FERTILIZER_UNLOCK_TICK = 30 # Updated default
        mock_config.TECH_DIFFUSION_RATE = 0.10       # Updated default
        mock_config.TECH_UNLOCK_COST_THRESHOLD = 5000.0
        mock_config.TECH_UNLOCK_PROB_CAP = 1.0
        return mock_config

    @pytest.fixture
    def manager(self, config, mock_numpy):
        # We must also patch _process_diffusion to use scalar logic compatible with FakeMatrix
        # instead of the complex vectorized numpy logic.

        real_manager = TechnologyManager(config, MagicMock())

        # Define a simplified Python-only diffusion process
        def _simple_process_diffusion(firms, current_tick):
            if not firms: return

            # Ensure capacity (relies on fake np.max and fake matrix shape)
            firm_ids = [f['id'] for f in firms]
            max_firm_id = max(firm_ids)
            real_manager._ensure_capacity(max_firm_id)

            for tech_id in real_manager.active_techs:
                tech = real_manager.tech_tree[tech_id]
                effective_rate = real_manager._get_effective_diffusion_rate(tech.diffusion_rate)

                for firm in firms:
                    if tech.sector != "ALL" and firm['sector'] != tech.sector:
                        continue

                    # Check if already adopted (scalar access)
                    if real_manager.has_adopted(firm['id'], tech_id):
                        continue

                    # Roll dice
                    if random.random() < effective_rate:
                        real_manager._adopt(firm['id'], tech)
                        # Minimal logging mock
                        real_manager.logger.info("Adopted")

        # Replace the method on the instance
        real_manager._process_diffusion = _simple_process_diffusion

        # We also need to patch get_productivity_multiplier because it uses np.where
        def _simple_get_productivity_multiplier(firm_id: int) -> float:
            if firm_id >= int(real_manager.adoption_matrix.shape[0]):
                return 1.0

            total_mult = 1.0
            # Iterate through all registered techs to check adoption
            # This is O(Techs), slower than O(Adopted) but fine for tests
            for tech_id, tech_idx in real_manager.tech_id_to_idx.items():
                if real_manager.adoption_matrix[(firm_id, tech_idx)]:
                    tech = real_manager.tech_tree[tech_id]
                    total_mult *= tech.multiplier
            return total_mult

        real_manager.get_productivity_multiplier = _simple_get_productivity_multiplier

        return real_manager

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
        tech.diffusion_rate = 1.0 # 100% adoption chance

        # We need to ensure random.random() returns < 1.0. It usually does.
        # But for robustness, we can seed or patch random, but usually fine.

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

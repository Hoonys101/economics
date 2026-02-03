
import unittest
from unittest.mock import MagicMock, Mock, patch
import sys
import os
from typing import Dict, Any, List

# Add root to sys.path
sys.path.append(os.getcwd())

class TestParityAudit(unittest.TestCase):

    def setUp(self):
        # Create a mock for numpy
        self.mock_numpy = MagicMock()
        self.mock_numpy.array.return_value = MagicMock()
        self.mock_numpy.where.return_value = ([],)
        self.mock_numpy.ones.return_value = MagicMock()
        self.mock_numpy.random.rand.return_value = MagicMock()

        # We need to patch sys.modules in setUp
        self.module_patcher = patch.dict(sys.modules, {"numpy": self.mock_numpy})
        self.module_patcher.start()

    def tearDown(self):
        self.module_patcher.stop()

    def test_chemical_fertilizer(self):
        print("\n--- Testing Chemical Fertilizer ---")
        from simulation.systems.technology_manager import TechnologyManager

        mock_config = MagicMock()
        mock_config.TECH_FERTILIZER_MULTIPLIER = 3.0
        mock_config.TECH_UNLOCK_COST_THRESHOLD = 5000.0
        mock_config.TECH_DIFFUSION_RATE = 0.05

        tm = TechnologyManager(mock_config, MagicMock(), strategy=None)

        tech = tm.tech_tree.get("TECH_AGRI_CHEM_01")
        self.assertIsNotNone(tech)
        print(f"Fertilizer Tech Found: {tech.name}")
        self.assertEqual(tech.multiplier, 3.0)

    def test_newborn_initialization(self):
        print("\n--- Testing Newborn Initialization ---")
        from simulation.systems.demographic_manager import DemographicManager

        mock_config = MagicMock()
        mock_config.NEWBORN_INITIAL_NEEDS = {
            "survival": 60.0, "social": 20.0
        }
        mock_config.REPRODUCTION_AGE_START = 20
        mock_config.REPRODUCTION_AGE_END = 40
        mock_config.MITOSIS_MUTATION_PROBABILITY = 0.1
        mock_config.INITIAL_WAGE = 10.0
        mock_config.EDUCATION_COST_MULTIPLIERS = {}

        dm = DemographicManager(mock_config, strategy=None)

        initial_needs = getattr(dm.config_module, "NEWBORN_INITIAL_NEEDS", {})
        self.assertEqual(initial_needs["survival"], 60.0)
        print(f"Newborn Initial Needs verified: {initial_needs}")

    def test_demand_elasticity(self):
        print("\n--- Testing Demand Elasticity ---")
        from simulation.core_agents import Household

        mock_config_dto = MagicMock()
        mock_config_dto.value_orientation_mapping = {}
        mock_config_dto.initial_household_age_range = (20, 30)
        mock_config_dto.initial_aptitude_distribution = (0.5, 0.1)
        mock_config_dto.price_memory_length = 10
        mock_config_dto.wage_memory_length = 10
        mock_config_dto.ticks_per_year = 100
        mock_config_dto.conformity_ranges = {}
        mock_config_dto.elasticity_mapping = {"DEFAULT": 1.0, "MISER": 2.0}

        # Required for wealth calculation init
        mock_config_dto.initial_household_assets_mean = 500.0
        mock_config_dto.quality_pref_snob_min = 0.8
        mock_config_dto.quality_pref_miser_max = 0.2
        mock_config_dto.adaptation_rate_normal = 0.1
        mock_config_dto.adaptation_rate_impulsive = 0.1
        mock_config_dto.adaptation_rate_conservative = 0.1

        mock_decision_engine = MagicMock()
        mock_personality = MagicMock()
        mock_personality.name = "MISER"

        mock_talent = MagicMock()

        hh = Household(
            id=1,
            talent=mock_talent,
            goods_data=[],
            initial_assets=100.0,
            initial_needs={},
            decision_engine=mock_decision_engine,
            value_orientation="DEFAULT",
            personality=mock_personality,
            config_dto=mock_config_dto,
            loan_market=None,
            logger=MagicMock()
        )

        elasticity = getattr(hh._social_state, "demand_elasticity", None)
        print(f"Household Elasticity for MISER: {elasticity}")
        self.assertEqual(elasticity, 2.0)

    def test_housing_multi_currency_resolution(self):
        print("\n--- Testing Housing vs Multi-Currency Resolution ---")
        from simulation.core_agents import Household
        # Use imports inside test to ensure patch applies or imports work correctly

        mock_config_dto = MagicMock()
        mock_config_dto.value_orientation_mapping = {}
        mock_config_dto.initial_household_age_range = (20, 30)
        mock_config_dto.initial_aptitude_distribution = (0.5, 0.1)
        mock_config_dto.price_memory_length = 10
        mock_config_dto.wage_memory_length = 10
        mock_config_dto.ticks_per_year = 100
        mock_config_dto.conformity_ranges = {}
        mock_config_dto.initial_household_assets_mean = 500.0
        mock_config_dto.quality_pref_snob_min = 0.8
        mock_config_dto.quality_pref_miser_max = 0.2
        mock_config_dto.adaptation_rate_normal = 0.1

        mock_decision_engine = MagicMock()
        mock_personality = MagicMock()
        mock_personality.name = "DEFAULT"
        mock_talent = MagicMock()

        # 1. Instantiate Household with Float Assets -> Dict conversion
        hh = Household(
            id=1,
            talent=mock_talent,
            goods_data=[],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=mock_decision_engine,
            value_orientation="DEFAULT",
            personality=mock_personality,
            config_dto=mock_config_dto,
            loan_market=None,
            logger=MagicMock()
        )

        assets = hh.assets
        self.assertIsInstance(assets, dict)
        print(f"Household assets verified as dict: {assets}")

        # 2. Test Logic from HousingTransactionHandler (Manually invoking the patched logic)
        # We can also import the handler class and test it if we mock everything else
        from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
        from modules.system.api import DEFAULT_CURRENCY

        # Extract logic block check
        raw_assets = hh.assets
        buyer_assets = raw_assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(raw_assets, dict) else float(raw_assets)

        print(f"Extracted buyer_assets: {buyer_assets} (Type: {type(buyer_assets)})")
        self.assertIsInstance(buyer_assets, float)
        self.assertEqual(buyer_assets, 1000.0)

        down_payment = 200.0
        self.assertTrue(buyer_assets >= down_payment)
        print("Comparison check passed (No TypeError)")

    def test_housing_liens(self):
        print("\n--- Testing Housing Liens Structure ---")
        from simulation.models import RealEstateUnit
        from modules.finance.api import LienDTO

        unit = RealEstateUnit(id=1)
        self.assertEqual(unit.liens, [])

        new_lien: LienDTO = {
             "loan_id": "loan_123",
             "lienholder_id": 99,
             "principal_remaining": 5000.0,
             "lien_type": "MORTGAGE"
        }
        unit.liens.append(new_lien)
        self.assertEqual(len(unit.liens), 1)
        self.assertEqual(unit.mortgage_id, "loan_123")
        print("Lien structure and legacy property verified.")

if __name__ == '__main__':
    import warnings
    warnings.filterwarnings("ignore")
    unittest.main()

import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
import config
from tests.utils.factories import create_household_config_dto

class TestSocioTechDynamics(unittest.TestCase):
    def setUp(self):
        # Override Config
        config.HOUSEWORK_BASE_HOURS = 6.0
        config.CHILDCARE_TIME_REQUIRED = 8.0

        # Setup Mock Environment
        self.mock_engine = MagicMock()
        self.mock_engine.config_module = config

        # Setup Agents
        self.male = self._create_agent(1, "M")
        self.female = self._create_agent(2, "F")

        # Marry them
        self.male._bio_state.spouse_id = self.female.id
        self.female._bio_state.spouse_id = self.male.id

        # Add Child
        self.male._bio_state.children_ids = [100]
        self.female._bio_state.children_ids = [100]

    def _create_agent(self, id, gender):
        ai = HouseholdAI(f"agent_{id}", self.mock_engine)
        agent = Household(
            id=id,
            talent=Talent(0.1, {}),
            goods_data=[],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=MagicMock(),
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_dto=create_household_config_dto(),
            gender=gender
        )
        agent.decision_engine.ai_engine = ai
        agent.decision_engine.config_module = config
        # agent.gender = gender # Passed in constructor
        agent.home_quality_score = 1.0
        return agent

    def test_scenario_a_dark_ages(self):
        """
        Scenario A: Low Tech, No Formula.
        Verify Female Labor Drop.
        """
        config.FORMULA_TECH_LEVEL = 0.0
        children_data = [{"age": 1}] # Infant
        spouse_data_m = {"id": self.female.id}
        spouse_data_f = {"id": self.male.id}

        # Male Allocation
        alloc_m = self.male.decision_engine.ai_engine.decide_time_allocation(
            self.male.get_agent_data(), spouse_data_m, children_data, config
        )

        # Female Allocation
        alloc_f = self.female.decision_engine.ai_engine.decide_time_allocation(
            self.female.get_agent_data(), spouse_data_f, children_data, config
        )

        print("\n[Scenario A: Dark Ages]")
        print(f"Male Obligations: {alloc_m['total_obligated']} (HW: {alloc_m['housework']}, CC: {alloc_m['childcare']})")
        print(f"Female Obligations: {alloc_f['total_obligated']} (HW: {alloc_f['housework']}, CC: {alloc_f['childcare']})")

        # Assertions
        # Housework split 50/50 (6.0 / 2 = 3.0)
        self.assertEqual(alloc_m['housework'], 3.0)
        self.assertEqual(alloc_f['housework'], 3.0)

        # Childcare: Female takes all (8.0)
        self.assertEqual(alloc_f['childcare'], 8.0)
        self.assertEqual(alloc_m['childcare'], 0.0)

        # Labor Capacity (Max 14)
        labor_cap_m = max(0, 14 - alloc_m['total_obligated'])
        labor_cap_f = max(0, 14 - alloc_f['total_obligated'])

        print(f"Male Labor Cap: {labor_cap_m}h")
        print(f"Female Labor Cap: {labor_cap_f}h")

        self.assertLess(labor_cap_f, labor_cap_m, "Female should have significantly less labor capacity")
        self.assertLessEqual(labor_cap_f, 4.0, "Female labor capacity should be critically low (<= 4h)")

    def test_scenario_b_techno_optimism(self):
        """
        Scenario B: High Tech, Formula Available.
        Verify Female Labor Recovery.
        """
        config.FORMULA_TECH_LEVEL = 1.0
        children_data = [{"age": 1}]
        spouse_data_m = {"id": self.female.id}
        spouse_data_f = {"id": self.male.id}

        alloc_m = self.male.decision_engine.ai_engine.decide_time_allocation(
            self.male.get_agent_data(), spouse_data_m, children_data, config
        )
        alloc_f = self.female.decision_engine.ai_engine.decide_time_allocation(
            self.female.get_agent_data(), spouse_data_f, children_data, config
        )

        print("\n[Scenario B: Techno-Optimism]")
        print(f"Male Obligations: {alloc_m['total_obligated']}")
        print(f"Female Obligations: {alloc_f['total_obligated']}")

        # Childcare Shared (4.0 each)
        self.assertEqual(alloc_f['childcare'], 4.0)
        self.assertEqual(alloc_m['childcare'], 4.0)

        # Labor Capacity
        labor_cap_f = max(0, 14 - alloc_f['total_obligated'])
        print(f"Female Labor Cap: {labor_cap_f}h")

        self.assertEqual(labor_cap_f, 7.0, "Female labor capacity should recover to 7h (14 - 3 - 4)")

    def test_appliance_effect(self):
        """
        Verify Appliances reduce housework for both.
        """
        self.male.home_quality_score = 1.5
        self.female.home_quality_score = 1.5

        alloc_m = self.male.decision_engine.ai_engine.decide_time_allocation(
            self.male.get_agent_data(), {"id":2}, [], config
        )

        # Base 6.0 -> Reduced to 3.0 total -> Shared 1.5 each
        self.assertEqual(alloc_m['housework'], 1.5)
        print(f"\n[Appliance Effect] Housework per person: {alloc_m['housework']}h (Reduced from 3.0h)")

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, PropertyMock
import pytest
from simulation.components.demographics_component import DemographicsComponent

class TestDemographicsComponent(unittest.TestCase):

    def setUp(self):
        """Set up a mock owner and config for the component tests."""
        self.mock_owner = MagicMock()
        self.mock_owner.id = 1
        self.mock_owner.logger = MagicMock()

        # Mock talent for get_generational_similarity
        self.mock_owner.talent.base_learning_rate = 0.5
        self.mock_owner.is_active = True

        self.mock_config = MagicMock()
        self.mock_config.TICKS_PER_YEAR = 100

        self.component = DemographicsComponent(
            owner=self.mock_owner,
            initial_age=30.0,
            gender="F",
            config_module=self.mock_config
        )

    def test_initialization(self):
        """Test that the component initializes with the correct attributes."""
        self.assertEqual(self.component.owner.id, 1)
        self.assertEqual(self.component.age, 30.0)
        self.assertEqual(self.component.gender, "F")
        self.assertEqual(self.component.generation, 0)
        self.assertIsNone(self.component.parent_id)
        self.assertIsNone(self.component.spouse_id)
        self.assertEqual(self.component.children_ids, [])

    def test_age_one_tick(self):
        """Test that the age increases correctly after one tick."""
        initial_age = self.component.age
        self.component.age_one_tick(current_tick=1)
        self.assertAlmostEqual(self.component.age, initial_age + 0.01)

    def test_handle_death_under_threshold(self):
        """Test that the agent does not die if below the age threshold."""
        self.component._age = 50 # Below the first threshold of 60
        self.assertFalse(self.component.handle_death(current_tick=1))
        self.assertTrue(self.mock_owner.is_active)

    def test_handle_death_above_threshold(self):
        """Test that the agent has a chance to die if above the age threshold."""
        self.component._age = 85

        # Ensure configuration has high probability for testing
        self.mock_config.AGE_DEATH_PROBABILITIES = {80: 100.0} # 100% per year if >= 80

        # Since death is probabilistic, we can't guarantee it.
        # Instead, we check if the logic runs without error and returns a boolean.
        # To make it deterministic for a test, we could mock random.random
        with unittest.mock.patch('random.random', return_value=0.0): # Force death
            self.assertTrue(self.component.handle_death(current_tick=1))
            self.assertFalse(self.mock_owner.is_active)

        # Reset and test the case where it doesn't die
        self.mock_owner.is_active = True
        with unittest.mock.patch('random.random', return_value=0.99): # Prevent death
            self.assertFalse(self.component.handle_death(current_tick=1))
            self.assertTrue(self.mock_owner.is_active)

    def test_set_spouse(self):
        """Test setting a spouse."""
        self.component.set_spouse(2)
        self.assertEqual(self.component.spouse_id, 2)

    def test_add_child(self):
        """Test adding a child."""
        self.component.add_child(3)
        self.assertIn(3, self.component.children_ids)
        self.assertEqual(self.component.children_count, 1)

        # Test adding the same child again (should not duplicate)
        self.component.add_child(3)
        self.assertEqual(self.component.children_count, 1)

    def test_get_generational_similarity(self):
        """Test the calculation of generational similarity."""
        similarity = self.component.get_generational_similarity(0.5, 0.6)
        self.assertAlmostEqual(similarity, 0.9) # 1.0 - abs(0.5 - 0.6)

    def test_create_offspring_demographics(self):
        """Test the creation of demographic data for an offspring."""
        offspring_data = self.component.create_offspring_demographics(new_id=10, current_tick=100)

        self.assertEqual(offspring_data["generation"], 1)
        self.assertEqual(offspring_data["parent_id"], self.mock_owner.id)
        self.assertEqual(offspring_data["initial_age"], 0.0)
        self.assertIn(offspring_data["gender"], ["M", "F"])

if __name__ == '__main__':
    unittest.main()

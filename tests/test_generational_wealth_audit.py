import unittest
from unittest.mock import MagicMock, patch
from simulation.systems.generational_wealth_audit import GenerationalWealthAudit
from simulation.core_agents import Household

class TestGenerationalWealthAudit(unittest.TestCase):
    def setUp(self):
        self.config_module = MagicMock()
        self.audit = GenerationalWealthAudit(self.config_module)

    def create_mock_household(self, id, assets, generation):
        mock_household = MagicMock()
        mock_household.id = id
        mock_household.assets = assets
        mock_household.generation = generation
        mock_household.is_active = True
        return mock_household

    @patch('logging.Logger.info')
    def test_run_audit(self, mock_log_info):
        # Create mock agents
        agent1 = self.create_mock_household(1, 1000, 1)
        agent2 = self.create_mock_household(2, 2000, 2)
        agent3 = self.create_mock_household(3, 3000, 1)

        agents = [agent1, agent2, agent3]

        # Run the audit
        self.audit.run_audit(agents, 100)

        # Check if the logger was called
        self.assertTrue(mock_log_info.called)

        # Check the log message
        expected_log_message = "GENERATIONAL_WEALTH_AUDIT | Tick: 100 | Total Wealth: 6000.00 | Total Agents: 3\n"
        expected_log_message += "  - Gen 1: 2 agents, Total Wealth: 4000.00 (66.67%), Avg Wealth: 2000.00\n"
        expected_log_message += "  - Gen 2: 1 agents, Total Wealth: 2000.00 (33.33%), Avg Wealth: 2000.00"

        # Get the actual log message
        actual_log_message = mock_log_info.call_args[0][0]

        # Normalize the log messages for comparison
        normalized_expected = ' '.join(expected_log_message.split())
        normalized_actual = ' '.join(actual_log_message.split())

        self.assertEqual(normalized_expected, normalized_actual)

    @patch('logging.Logger.info')
    def test_run_audit_no_agents(self, mock_log_info):
        # Run the audit with no agents
        self.audit.run_audit([], 100)

        # Check if the logger was called
        self.assertTrue(mock_log_info.called)

        # Check the log message
        expected_log_message = "GENERATIONAL_WEALTH_AUDIT | No active agents to audit."

        # Get the actual log message
        actual_log_message = mock_log_info.call_args[0][0]

        self.assertEqual(expected_log_message, actual_log_message)


if __name__ == '__main__':
    unittest.main()

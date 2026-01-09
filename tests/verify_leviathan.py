import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import logging
from collections import deque

# Ensure path is correct for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.agents.government import Government
from simulation.ai.government_ai import GovernmentAI
from simulation.ai.enums import PoliticalParty
from simulation.core_agents import Household
import config

class TestLeviathan(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.config = config
        self.config.INCOME_TAX_RATE = 0.1
        self.config.CORPORATE_TAX_RATE = 0.2
        self.config.TAX_RATE_BASE = 0.1
        self.config.TAX_BRACKETS = []
        self.config.GOVERNMENT_STIMULUS_ENABLED = True

        self.gov = Government(id=1, initial_assets=10000.0, config_module=self.config)

        # Mock households
        self.households = []
        for i in range(10):
            h = MagicMock(spec=Household)
            h.id = i
            h.is_active = True
            h.approval_rating = 1 # Start happy
            h.needs = {"survival": 20.0}
            self.households.append(h)

    def test_opinion_aggregation(self):
        """Test if Government aggregates household approval correctly."""
        # 5 Happy, 5 Unhappy
        for i in range(5):
            self.households[i].approval_rating = 1
        for i in range(5, 10):
            self.households[i].approval_rating = 0

        self.gov.update_public_opinion(self.households)

        self.assertEqual(self.gov.approval_rating, 0.5)
        self.assertEqual(len(self.gov.public_opinion_queue), 1)
        self.assertEqual(self.gov.perceived_public_opinion, 0.5)

    def test_opinion_lag(self):
        """Test if Perceived Public Opinion lags by 4 ticks (or queue size)."""
        # Tick 1: 1.0
        for h in self.households: h.approval_rating = 1
        self.gov.update_public_opinion(self.households) # Q: [1.0]
        self.assertEqual(self.gov.perceived_public_opinion, 1.0)

        # Tick 2: 0.0
        for h in self.households: h.approval_rating = 0
        self.gov.update_public_opinion(self.households) # Q: [1.0, 0.0]
        self.assertEqual(self.gov.perceived_public_opinion, 1.0) # Still sees old

        # Tick 3: 0.0
        self.gov.update_public_opinion(self.households) # Q: [1.0, 0.0, 0.0]
        self.assertEqual(self.gov.perceived_public_opinion, 1.0)

        # Tick 4: 0.0
        self.gov.update_public_opinion(self.households) # Q: [1.0, 0.0, 0.0, 0.0]
        self.assertEqual(self.gov.perceived_public_opinion, 1.0)

        # Tick 5: 0.0 -> Queue pops
        self.gov.update_public_opinion(self.households) # Q: [0.0, 0.0, 0.0, 0.0]
        self.assertEqual(self.gov.perceived_public_opinion, 0.0) # Finally sees drop

    def test_election_flip(self):
        """Test if Government flips party on low approval at election tick."""
        self.gov.perceived_public_opinion = 0.4 # Below 0.5
        self.gov.ruling_party = PoliticalParty.BLUE

        self.gov.check_election(100)

        self.assertEqual(self.gov.ruling_party, PoliticalParty.RED)
        self.assertNotEqual(self.gov.ruling_party, PoliticalParty.BLUE)

        # Next election, if opinion still low, flip back
        self.gov.check_election(200)
        self.assertEqual(self.gov.ruling_party, PoliticalParty.BLUE)

    def test_ai_policy_execution(self):
        """Test if AI actions translate to policy changes based on Party."""
        market_data = {"total_production": 100.0}

        # Case 1: BLUE Party + Expansion
        self.gov.ruling_party = PoliticalParty.BLUE
        self.gov.corporate_tax_rate = 0.2
        self.gov.firm_subsidy_budget_multiplier = 1.0

        # Force AI to choose EXPAND (Action 0)
        with patch.object(self.gov.ai, 'decide_policy', return_value=0):
            self.gov.make_policy_decision(market_data, 1)

        # Expect Corp Tax Cut, Subsidy Increase
        self.assertLess(self.gov.corporate_tax_rate, 0.2)
        self.assertGreater(self.gov.firm_subsidy_budget_multiplier, 1.0)

        # Case 2: RED Party + Expansion
        self.gov.ruling_party = PoliticalParty.RED
        self.gov.income_tax_rate = 0.1
        self.gov.welfare_budget_multiplier = 1.0

        with patch.object(self.gov.ai, 'decide_policy', return_value=0):
            self.gov.make_policy_decision(market_data, 1)

        # Expect Income Tax Cut, Welfare Increase
        self.assertLess(self.gov.income_tax_rate, 0.1)
        self.assertGreater(self.gov.welfare_budget_multiplier, 1.0)

if __name__ == '__main__':
    unittest.main()

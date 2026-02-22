import sys
import os
import unittest
from unittest.mock import MagicMock, PropertyMock
import logging

# Ensure root is in path
sys.path.append(os.getcwd())

from simulation.systems.lifecycle.marriage_system import MarriageSystem
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState
from modules.finance.api import ISettlementSystem
from modules.common.interfaces import IPropertyOwner
from simulation.models import RealEstateUnit
from modules.system.api import DEFAULT_CURRENCY

class TestMarriageSystem(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("TestMarriage")
        self.settlement = MagicMock(spec=ISettlementSystem)
        self.system = MarriageSystem(self.settlement, self.logger)
        # Ensure probability is 100% for test
        self.system.marriage_chance = 1.0

    def test_marriage_merger(self):
        # 1. Setup Agents
        # Agent A: Male, 30, Rich (Head)
        # Agent B: Female, 28, Poor (Spouse)

        agent_a = MagicMock(spec=Household)
        agent_a.id = 101
        agent_a.is_active = True
        agent_a.spouse_id = None
        agent_a.gender = "M"
        agent_a.age = 30.0
        agent_a.total_wealth = 100000 # Richer
        agent_a.balance_pennies = 50000
        agent_a.portfolio = MagicMock()
        agent_a.inventory = {}
        agent_a.owned_properties = [1]
        agent_a.children_ids = []
        agent_a.residing_property_id = 1
        agent_a.is_homeless = False

        # Mock Internal States for Wave 4 logic
        agent_a._econ_state = MagicMock()
        agent_a._econ_state.wallet = MagicMock()
        agent_a._bio_state = MagicMock()
        agent_a._bio_state.is_active = True
        agent_a._bio_state.gender = "M"
        agent_a._bio_state.sex = "M"
        agent_a._bio_state.children_ids = []
        agent_a._bio_state.spouse_id = None


        # Configure owned_properties behavior as list
        # We need a real list to append/remove
        agent_a_props = [1]
        agent_b_props = [2]

        type(agent_a).owned_properties = PropertyMock(return_value=agent_a_props)

        agent_b = MagicMock(spec=Household)
        type(agent_b).owned_properties = PropertyMock(return_value=agent_b_props)
        agent_b.id = 102
        agent_b.is_active = True
        agent_b.spouse_id = None
        agent_b.gender = "F"
        agent_b.age = 28.0
        agent_b.total_wealth = 10000 # Poorer
        agent_b.balance_pennies = 5000
        agent_b.portfolio = MagicMock()
        agent_b.inventory = {"apple": 10.0}
        agent_b.children_ids = [201]
        agent_b.residing_property_id = 2
        agent_b.is_homeless = False

        # Mock Internal States
        agent_b._econ_state = MagicMock()
        agent_b._econ_state.wallet = MagicMock()
        agent_b._bio_state = MagicMock()
        agent_b._bio_state.is_active = True
        agent_b._bio_state.gender = "F"
        agent_b._bio_state.sex = "F"
        agent_b._bio_state.children_ids = [201]
        agent_b._bio_state.spouse_id = None


        # Mock Methods
        agent_a.add_item = MagicMock()
        # Mock add_property to append to our local list
        agent_a.add_property = MagicMock(side_effect=lambda pid: agent_a_props.append(pid))
        agent_a.add_child = MagicMock()

        agent_b.remove_property = MagicMock(side_effect=lambda pid: agent_b_props.remove(pid))
        agent_b.clear_inventory = MagicMock()

        # Mock Portfolio
        agent_b.portfolio.holdings = {1: MagicMock()}

        # Setup State
        state = MagicMock(spec=SimulationState)
        state.time = 100
        state.households = [agent_a, agent_b]

        # Real Estate Units
        unit1 = MagicMock(spec=RealEstateUnit)
        unit1.id = 1
        unit1.owner_id = 101

        unit2 = MagicMock(spec=RealEstateUnit)
        unit2.id = 2
        unit2.owner_id = 102

        state.real_estate_units = [unit1, unit2]

        # Execute
        self.system.execute(state)

        # Assertions

        # 1. Asset Transfer
        self.settlement.transfer.assert_called_with(
            debit_agent=agent_b,
            credit_agent=agent_a,
            amount=5000,
            memo="MARRIAGE_MERGER",
            tick=100,
            currency=DEFAULT_CURRENCY
        )

        # 2. Portfolio Merger
        agent_a.portfolio.merge.assert_called_with(agent_b.portfolio)
        assert len(agent_b.portfolio.holdings) == 0

        # 3. Inventory
        agent_a.add_item.assert_called_with("apple", 10.0)
        agent_b.clear_inventory.assert_called()

        # 4. Property
        assert unit2.owner_id == 101 # Transferred to A
        assert 2 in agent_a_props # Added to A
        assert 2 not in agent_b_props # Removed from B

        # 5. Children
        agent_a.add_child.assert_called_with(201)

        # 6. State
        assert agent_a.spouse_id == 102
        assert agent_b.spouse_id == 101
        assert agent_b.is_active == False
        assert agent_b.residing_property_id == agent_a.residing_property_id # Moved in

if __name__ == "__main__":
    unittest.main()

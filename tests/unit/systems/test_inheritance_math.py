import unittest
from unittest.mock import MagicMock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.settlement_system import SettlementSystem
from simulation.core_agents import Household
from simulation.portfolio import Portfolio

class TestInheritanceLeak(unittest.TestCase):
    def test_floating_point_contamination(self):
        # Setup
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.0
        config.INHERITANCE_DEDUCTION = 10000.0

        manager = InheritanceManager(config)
        settlement_system = SettlementSystem(logger=MagicMock())

        simulation = MagicMock()
        simulation.settlement_system = settlement_system
        simulation.stock_market = None
        simulation.real_estate_units = []
        simulation.time = 1

        gov = MagicMock()
        gov.id = 999

        # Deceased
        deceased = MagicMock()
        deceased.id = 1
        deceased._econ_state = MagicMock()
        deceased._econ_state.assets = 100.00
        deceased._econ_state.portfolio = Portfolio(1)
        deceased._bio_state = MagicMock()
        deceased._bio_state.is_active = False
        deceased._bio_state.children_ids = [10, 11, 12]

        # Heirs
        heir1 = MagicMock()
        heir1.id = 10
        heir1._bio_state = MagicMock()
        heir1._bio_state.is_active = True
        heir1.deposit = MagicMock()

        heir2 = MagicMock()
        heir2.id = 11
        heir2._bio_state = MagicMock()
        heir2._bio_state.is_active = True
        heir2.deposit = MagicMock()

        heir3 = MagicMock()
        heir3.id = 12
        heir3._bio_state = MagicMock()
        heir3._bio_state.is_active = True
        heir3.deposit = MagicMock()

        simulation.agents = {10: heir1, 11: heir2, 12: heir3}

        # Execute
        manager.process_death(deceased, gov, simulation)

        # Verify Contamination
        args1 = heir1.deposit.call_args[0][0]
        args2 = heir2.deposit.call_args[0][0]
        args3 = heir3.deposit.call_args[0][0]

        print(f"Heir 1: {args1}")
        print(f"Heir 2: {args2}")
        print(f"Heir 3: {args3}")

        self.assertEqual(args1, round(args1, 2), "Amounts should be clean (2 decimal places)")

        self.assertEqual(args1, 33.33)
        self.assertEqual(args2, 33.33)
        self.assertEqual(args3, 33.34)
        self.assertAlmostEqual(args1 + args2 + args3, 100.00)

if __name__ == "__main__":
    unittest.main()

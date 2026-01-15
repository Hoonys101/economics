import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.models import RealEstateUnit, Transaction
from simulation.systems.housing_system import HousingSystem
import config
from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
from simulation.ai.enums import Personality

class MockRepository:
    def save_simulation_run(self, *args, **kwargs):
        return 1
    def close(self):
        pass
    def update_simulation_run_end_time(self, run_id):
        pass

class TestMonetaryIntegrity(unittest.TestCase):

    def test_government_asset_sale(self):
        # 1. Setup
        buyer = Household(
            id=1,
            initial_assets=200000,
            config_module=config,
            talent=1,
            goods_data=[],
            initial_needs={},
            decision_engine=RuleBasedHouseholdDecisionEngine(config, None),
            value_orientation="MAINSTREAM",
            personality=Personality.BALANCED
        )

        sim = Simulation(
            households=[buyer],
            firms=[],
            ai_trainer=None,
            repository=MockRepository(),
            config_module=config,
            goods_data=[]
        )

        gov = sim.government
        gov.assets = 0

        property_unit = RealEstateUnit(id=101, owner_id=0, estimated_value=150000)
        sim.real_estate_units.append(property_unit)

        housing_system = HousingSystem(config)

        # 2. The Transaction
        sale_price = 150000
        tx = Transaction(
            buyer_id=1,
            seller_id=0,
            item_id="unit_101",
            price=sale_price,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=sim.time
        )

        initial_money_destroyed = gov.total_money_destroyed

        # 3. Process
        housing_system.process_transaction(tx, sim)

        # 4. Assertions
        self.assertEqual(buyer.assets, 200000 - sale_price, "Buyer's assets were not correctly deducted.")

        expected_money_destroyed = initial_money_destroyed + sale_price
        self.assertEqual(gov.total_money_destroyed, expected_money_destroyed, "Government's total_money_destroyed was not updated correctly.")

        self.assertEqual(gov.assets, 0, "Government's assets should not increase from asset sales that destroy money.")

        self.assertEqual(property_unit.owner_id, buyer.id, "Property ownership was not transferred.")

if __name__ == '__main__':
    unittest.main()

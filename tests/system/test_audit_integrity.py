
import sys
import os
import unittest
from unittest.mock import MagicMock, ANY, patch

# Adjust path to allow imports
sys.path.append(os.getcwd())

from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.handlers.inheritance_handler import InheritanceHandler
from simulation.systems.handlers.public_manager_handler import PublicManagerTransactionHandler
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from modules.system.api import DEFAULT_CURRENCY

class TestEconomicIntegrityAudit(unittest.TestCase):
    def setUp(self):
        DemographicManager._instance = None # Reset Singleton
        self.config = MagicMock()
        self.config.TICKS_PER_YEAR = 100
        self.config.REPRODUCTION_AGE_START = 18
        self.config.REPRODUCTION_AGE_END = 50
        self.config.INITIAL_WAGE = 10.0
        self.config.MITOSIS_MUTATION_PROBABILITY = 0.0
        # Mock other config needed for Household init
        self.config.MAX_WORK_HOURS = 16
        self.config.HOURS_PER_TICK = 24
        self.config.EDUCATION_COST_MULTIPLIERS = {0: 1.0}

        self.logger = MagicMock()
        self.settlement_system = MagicMock()
        self.taxation_system = MagicMock()
        self.government = MagicMock()
        self.government.id = 1

    @patch('simulation.systems.demographic_manager.HouseholdFactory')
    @patch('simulation.systems.demographic_manager.Household')
    @patch('simulation.systems.demographic_manager.create_config_dto')
    def test_birth_gift_rounding(self, mock_create_config, mock_household_cls, mock_household_factory_cls):
        """
        Verify that birth gift is calculated in pennies (integer).
        """
        # Setup Mock Factory
        mock_factory_instance = mock_household_factory_cls.return_value

        dm = DemographicManager(config_module=self.config)

        # Inject mock factory into the instance if needed, or rely on patch
        # Since dm.__init__ instantiates HouseholdFactory, we mock the class before init or patch it.
        # Here we patched the class, so dm.household_factory will be a Mock.
        dm.settlement_system = self.settlement_system
        dm.logger = self.logger

        simulation = MagicMock()
        simulation.next_agent_id = 100
        simulation.time = 0
        simulation.ai_trainer = MagicMock()
        simulation.markets = {}
        simulation.goods_data = {}
        simulation.agents = {}

        # Mock Child creation
        mock_child = MagicMock()
        mock_child.id = 100
        mock_child.gender = "Female"
        mock_household_cls.return_value = mock_child
        mock_factory_instance.create_newborn.return_value = mock_child

        # Parent with integer assets (10000 pennies = 100.00 dollars)
        parent = MagicMock()
        parent.id = 10
        parent.age = 30
        parent.wallet = MagicMock()
        parent.wallet.get_balance.return_value = 10000
        parent.get_balance.return_value = 10000
        parent.talent = MagicMock()
        parent.personality = MagicMock()
        parent.value_orientation = "NEUTRAL"
        parent.risk_aversion = 0.5
        parent.generation = 1
        parent.children_ids = []

        birth_requests = [parent]

        # Debug print
        print(f"DEBUG: parent.age={parent.age}, type={type(parent.age)}")
        print(f"DEBUG: config.REPRODUCTION_AGE_START={self.config.REPRODUCTION_AGE_START}, type={type(self.config.REPRODUCTION_AGE_START)}")

        # Execute
        dm.process_births(simulation, birth_requests)

        # Expected Gift: 10% of 10000 = 1000 pennies
        args = self.settlement_system.transfer.call_args
        if args:
            # args[0] are positional args: (debit, credit, amount, memo)
            amount = args[0][2]
            self.assertEqual(amount, 1000)
            self.assertIsInstance(amount, int)
        else:
            self.fail("No transfer call detected")

    def test_inheritance_distribution(self):
        """
        Verify that inheritance distribution transfers full amount to heir (no dust sweep).
        """
        handler = InheritanceHandler()

        deceased = MagicMock()
        deceased.id = 99
        deceased.wallet = MagicMock()
        deceased.wallet.get_balance.return_value = 10005
        deceased.get_balance.return_value = 10005

        heir = MagicMock()
        heir.id = 101

        tx = Transaction(
            buyer_id=deceased.id,
            seller_id=-1,
            item_id="estate_distribution",
            quantity=1.0,
            price=10000,
            market_id="system",
            transaction_type="inheritance_distribution",
            time=0,
            metadata={"heir_ids": [heir.id]}
        , total_pennies=10000)

        context = TransactionContext(
            agents={101: heir},
            inactive_agents={},
            government=self.government,
            settlement_system=self.settlement_system,
            taxation_system=self.taxation_system,
            stock_market=None,
            real_estate_units=[],
            market_data={},
            config_module=self.config,
            logger=self.logger,
            time=0,
            bank=None,
            central_bank=None,
            public_manager=None,
            transaction_queue=[]
        )

        # Mock settle_atomic
        def mock_settle_atomic(debit, credits, tick):
            return True

        self.settlement_system.settle_atomic.side_effect = mock_settle_atomic

        handler.handle(tx, deceased, None, context)

        # Verify call args
        call_args = self.settlement_system.settle_atomic.call_args
        self.assertIsNotNone(call_args)

        credits = call_args[0][1]

        # Expect:
        # 1. Heir gets 10005 (Full amount)
        # 2. No dust sweep to government

        heir_credit = next((c for c in credits if c[0] == heir), None)
        gov_credit = next((c for c in credits if c[0] == self.government), None)

        self.assertIsNotNone(heir_credit)
        self.assertEqual(heir_credit[1], 10005)

        self.assertIsNone(gov_credit, "No dust sweep expected for single heir")

    def test_public_manager_tax_atomicity(self):
        """
        Verify Public Manager sales collect tax using settle_atomic.
        """
        handler = PublicManagerTransactionHandler()

        pm = MagicMock()
        pm.id = "PUBLIC_MANAGER"

        buyer = MagicMock()
        buyer.id = 50

        tx = Transaction(
            buyer_id=buyer.id,
            seller_id=pm.id,
            item_id="basic_food",
            quantity=10,
            price=500, # Total 5000 pennies
            market_id="system",
            transaction_type="goods", # Taxable
            time=0
        , total_pennies=5000)

        context = TransactionContext(
            agents={},
            inactive_agents={},
            government=self.government,
            settlement_system=self.settlement_system,
            taxation_system=self.taxation_system,
            stock_market=None,
            real_estate_units=[],
            market_data={},
            config_module=self.config,
            logger=self.logger,
            time=0,
            bank=None,
            central_bank=None,
            public_manager=pm,
            transaction_queue=[]
        )

        # Setup tax calculation
        mock_intent = MagicMock()
        mock_intent.amount = 250 # 5% of 5000
        mock_intent.reason = "sales_tax"
        mock_intent.payer_id = buyer.id
        self.taxation_system.calculate_tax_intents.return_value = [mock_intent]

        handler.handle(tx, buyer, pm, context)

        # Verify usage of settle_atomic
        self.assertTrue(self.settlement_system.settle_atomic.called)
        self.assertFalse(self.settlement_system.transfer.called)

        # Check credits
        call_args = self.settlement_system.settle_atomic.call_args
        credits = call_args[0][1]

        pm_credit = next((c for c in credits if c[0] == pm), None)
        gov_credit = next((c for c in credits if c[0] == self.government), None)

        self.assertIsNotNone(pm_credit)
        self.assertEqual(pm_credit[1], 5000)

        self.assertIsNotNone(gov_credit)
        self.assertEqual(gov_credit[1], 250)

if __name__ == '__main__':
    unittest.main()

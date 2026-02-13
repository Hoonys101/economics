import unittest
from unittest.mock import MagicMock, Mock
from simulation.systems.handlers.escheatment_handler import EscheatmentHandler
from simulation.systems.handlers.inheritance_handler import InheritanceHandler
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import IFinancialAgent

class TestEscheatmentHandler(unittest.TestCase):
    def setUp(self):
        self.handler = EscheatmentHandler()
        self.buyer = Mock(spec=IFinancialAgent) # Deceased
        self.buyer.id = 1
        self.buyer.get_balance.return_value = 100

        self.government = Mock()
        self.government.id = 999

        self.settlement_system = Mock()
        self.settlement_system.settle_atomic = Mock()
        self.settlement_system.settle_atomic.return_value = True

        self.context = TransactionContext(
            agents={1: self.buyer, 999: self.government},
            inactive_agents={},
            government=self.government,
            settlement_system=self.settlement_system,
            taxation_system=Mock(),
            stock_market=None,
            real_estate_units=[],
            market_data=Mock(),
            config_module=Mock(),
            logger=MagicMock(),
            time=100,
            bank=Mock(),
            central_bank=Mock(),
            public_manager=Mock(),
            transaction_queue=[]
        )

        self.tx = Transaction(
            buyer_id=1,
            seller_id=999,
            item_id="escheatment",
            quantity=1,
            price=0,
            market_id="system",
            transaction_type="escheatment",
            time=100
        )

    def test_escheatment_with_financial_agent(self):
        """Test escheatment using IFinancialAgent interface."""
        result = self.handler.handle(self.tx, self.buyer, self.government, self.context)

        self.assertTrue(result)
        self.settlement_system.settle_atomic.assert_called_once()
        args, _ = self.settlement_system.settle_atomic.call_args
        debit_agent, credits, tick = args

        self.assertEqual(debit_agent, self.buyer)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0][0], self.government)
        self.assertEqual(credits[0][1], 100)
        self.assertIsInstance(credits[0][1], int)

    def test_escheatment_with_float_assets_dict(self):
        """Test escheatment with legacy dict assets containing float."""
        buyer = Mock()
        buyer.id = 2
        buyer.assets = {DEFAULT_CURRENCY: 200.5} # Float
        # Not spec=IFinancialAgent, so fallback to .assets

        self.context.agents[2] = buyer
        self.tx.buyer_id = 2

        result = self.handler.handle(self.tx, buyer, self.government, self.context)

        self.assertTrue(result)
        self.settlement_system.settle_atomic.assert_called_once()
        args, _ = self.settlement_system.settle_atomic.call_args
        _, credits, _ = args

        amount = credits[0][1]
        self.assertEqual(amount, 200) # Truncated to int
        self.assertIsInstance(amount, int)

    def test_escheatment_with_float_assets_legacy(self):
        """Test escheatment with legacy float assets attribute."""
        buyer = Mock()
        buyer.id = 3
        buyer.assets = 300.9 # Float

        self.context.agents[3] = buyer
        self.tx.buyer_id = 3

        result = self.handler.handle(self.tx, buyer, self.government, self.context)

        self.assertTrue(result)
        self.settlement_system.settle_atomic.assert_called_once()
        args, _ = self.settlement_system.settle_atomic.call_args
        _, credits, _ = args

        amount = credits[0][1]
        self.assertEqual(amount, 300) # Truncated to int
        self.assertIsInstance(amount, int)


class TestInheritanceHandler(unittest.TestCase):
    def setUp(self):
        self.handler = InheritanceHandler()
        self.deceased = Mock(spec=IFinancialAgent)
        self.deceased.id = 1
        self.deceased.get_balance.return_value = 100

        self.heir1 = Mock()
        self.heir1.id = 2
        self.heir2 = Mock()
        self.heir2.id = 3

        self.government = Mock()
        self.government.id = 999

        self.settlement_system = Mock()
        self.settlement_system.settle_atomic = Mock()
        self.settlement_system.settle_atomic.return_value = True

        self.context = TransactionContext(
            agents={1: self.deceased, 2: self.heir1, 3: self.heir2, 999: self.government},
            inactive_agents={},
            government=self.government,
            settlement_system=self.settlement_system,
            taxation_system=Mock(),
            stock_market=None,
            real_estate_units=[],
            market_data=Mock(),
            config_module=Mock(),
            logger=MagicMock(),
            time=100,
            bank=Mock(),
            central_bank=Mock(),
            public_manager=Mock(),
            transaction_queue=[]
        )

        self.tx = Transaction(
            buyer_id=1,
            seller_id=None,
            item_id="inheritance",
            quantity=1,
            price=0,
            market_id="system",
            transaction_type="inheritance_distribution",
            time=100,
            metadata={"heir_ids": [2, 3]}
        )

    def test_distribution_equal_split(self):
        """Test equal distribution among heirs."""
        # 100 / 2 = 50 each

        result = self.handler.handle(self.tx, self.deceased, None, self.context)

        self.assertTrue(result)
        self.settlement_system.settle_atomic.assert_called_once()
        args, _ = self.settlement_system.settle_atomic.call_args
        debit_agent, credits, _ = args

        self.assertEqual(debit_agent, self.deceased)
        self.assertEqual(len(credits), 2)

        self.assertEqual(credits[0][0], self.heir1)
        self.assertEqual(credits[0][1], 50)
        self.assertEqual(credits[1][0], self.heir2)
        self.assertEqual(credits[1][1], 50)

    def test_distribution_remainder(self):
        """Test distribution with remainder (e.g. 100 / 3)."""
        # Add 3rd heir
        heir3 = Mock()
        heir3.id = 4
        self.context.agents[4] = heir3
        self.tx.metadata["heir_ids"].append(4)

        # 100 / 3 = 33. Remainder 1.
        # Heir 1: 33
        # Heir 2: 33
        # Heir 3: 34

        result = self.handler.handle(self.tx, self.deceased, None, self.context)

        self.assertTrue(result)
        args, _ = self.settlement_system.settle_atomic.call_args
        _, credits, _ = args

        self.assertEqual(len(credits), 3)
        self.assertEqual(credits[0][1], 33)
        self.assertEqual(credits[1][1], 33)
        self.assertEqual(credits[2][1], 34)

        total = sum(c[1] for c in credits)
        self.assertEqual(total, 100)

    def test_missing_heirs_fallback(self):
        """Test fallback to government if all heirs are missing."""
        # Set heir_ids to non-existent agents
        self.tx.metadata["heir_ids"] = [99, 100]

        result = self.handler.handle(self.tx, self.deceased, None, self.context)

        self.assertTrue(result)
        args, _ = self.settlement_system.settle_atomic.call_args
        _, credits, _ = args

        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0][0], self.government)
        self.assertEqual(credits[0][1], 100)
        self.assertEqual(credits[0][2], "escheatment_fallback")

    def test_partial_missing_heirs(self):
        """Test distribution if some heirs are missing."""
        # Heir 1 exists, Heir 99 missing
        self.tx.metadata["heir_ids"] = [2, 99]

        # Count = 1 (only heir 1)
        # 100 / 1 = 100
        # Heir 1 gets 100

        result = self.handler.handle(self.tx, self.deceased, None, self.context)

        self.assertTrue(result)
        args, _ = self.settlement_system.settle_atomic.call_args
        _, credits, _ = args

        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0][0], self.heir1)
        self.assertEqual(credits[0][1], 100)

if __name__ == '__main__':
    unittest.main()

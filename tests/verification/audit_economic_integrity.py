
import unittest
from unittest.mock import MagicMock, ANY
from simulation.models import Transaction
from simulation.core_agents import Household
from modules.finance.transaction.handlers.goods import GoodsTransactionHandler
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.world_state import WorldState
from modules.finance.transaction.handlers.protocols import ISolvent, ITaxCollector, IConsumptionTracker

class TestEconomicIntegrity(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock()

    def test_sales_tax_atomicity_success(self):
        """
        Verifies that the refactored GoodsTransactionHandler uses settle_atomic,
        indicating true atomicity.
        """
        # Setup
        handler = GoodsTransactionHandler()

        mock_settlement = MagicMock()
        mock_settlement.settle_atomic.return_value = True

        mock_gov = MagicMock()
        mock_gov.id = 999

        mock_buyer = MagicMock(spec=IConsumptionTracker)
        mock_buyer.id = 1
        mock_buyer.assets = 1000

        mock_seller = MagicMock()
        mock_seller.id = 2

        mock_config = MagicMock()
        mock_config.SALES_TAX_RATE = 0.05

        mock_state = MagicMock()
        mock_state.settlement_system = mock_settlement
        mock_state.government = mock_gov
        mock_state.config_module = mock_config
        mock_state.logger = self.mock_logger

        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple",
            quantity=1, price=100, total_pennies=10000,
            market_id="goods", transaction_type="purchase", time=1
        )

        # Action
        result = handler.handle(tx, mock_buyer, mock_seller, mock_state)

        # Assert
        self.assertTrue(result)

        # Verify settle_atomic WAS called
        mock_settlement.settle_atomic.assert_called_once()

        # Check arguments (credits_list)
        args, kwargs = mock_settlement.settle_atomic.call_args
        # settle_atomic(self, debit_agent: IFinancialAgent, credits_list: List[Tuple[IFinancialAgent, int, str]], tick: int)

        # Depending on how it's called (args vs kwargs), we extract parameters
        if kwargs.get('debit_agent'):
            debit_agent = kwargs['debit_agent']
        else:
            debit_agent = args[0]

        if kwargs.get('credits_list'):
            credits_list = kwargs['credits_list']
        else:
            credits_list = args[1]

        self.assertEqual(debit_agent, mock_buyer)
        self.assertEqual(len(credits_list), 2) # Seller + Gov

        # Verify Seller Credit
        self.assertEqual(credits_list[0][0], mock_seller)
        # Verify Tax Credit
        self.assertEqual(credits_list[1][0], mock_gov)

        print("\n[Audit] GoodsTransactionHandler correctly uses settle_atomic (Atomic Transfer Verified).")

    def test_inheritance_leak_fixed(self):
        """
        Verifies that DemographicManager.register_death triggers asset redistribution
        via InheritanceManager.
        """
        # Setup
        demo_manager = DemographicManager()

        mock_world_state = MagicMock(spec=WorldState)
        mock_inheritance_manager = MagicMock(spec=InheritanceManager)
        mock_world_state.inheritance_manager = mock_inheritance_manager
        mock_world_state.government = MagicMock()

        demo_manager.set_world_state(mock_world_state)

        mock_agent = MagicMock(spec=Household)
        mock_agent.id = 101
        mock_agent.is_active = True
        mock_agent.gender = "M"

        # Action
        demo_manager.register_death(mock_agent, cause="TEST")

        # Assert
        self.assertFalse(mock_agent.is_active)

        # Verify InheritanceManager IS called
        mock_inheritance_manager.process_death.assert_called_once_with(
            deceased=mock_agent,
            government=mock_world_state.government,
            simulation=mock_world_state
        )
        print("\n[Audit] DemographicManager.register_death correctly triggers InheritanceManager (Leak Plugged).")

if __name__ == '__main__':
    unittest.main()

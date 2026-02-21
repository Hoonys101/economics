import pytest
from unittest.mock import MagicMock, patch
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from modules.government.taxation.system import TaxationSystem, TaxIntent
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from modules.system.api import DEFAULT_CURRENCY
from modules.household.dtos import EconStateDTO
from modules.simulation.api import AgentStateDTO

class TestEconomicIntegrity:

    @pytest.fixture
    def mock_context(self):
        context = MagicMock(spec=TransactionContext)
        context.government = MagicMock()
        context.government.id = 1
        context.settlement_system = MagicMock()
        context.taxation_system = MagicMock()
        context.market_data = {}
        context.time = 100
        context.config_module = MagicMock()
        return context

    @pytest.fixture
    def mock_agents(self):
        buyer = MagicMock()
        buyer.id = 101
        buyer.assets = 100000 # Pennies

        seller = MagicMock()
        seller.id = 102
        seller.assets = 50000 # Pennies

        return buyer, seller

    def test_sales_tax_atomicity_seller_paid(self, mock_context, mock_agents):
        """
        Verify that if a tax intent specifies the SELLER as the payer (e.g. VAT),
        the GoodsTransactionHandler correctly deducts it from the seller's proceeds
        instead of charging the buyer extra.
        Currently expected to FAIL or behave incorrectly (charging buyer).
        """
        buyer, seller = mock_agents
        handler = GoodsTransactionHandler()

        # Transaction: 100 units @ $1.00 = $100.00 (10000 pennies)
        tx = Transaction(
            buyer_id=buyer.id,
            seller_id=seller.id,
            item_id="test_good",
            quantity=100,
            price=1.0,
            total_pennies=10000,
            market_id="goods",
            transaction_type="goods",
            time=100
        )

        # Mock TaxationSystem to return a Seller-Paid Tax (e.g. 10% VAT)
        # Tax Amount: 1000 pennies ($10)
        # Payer: Seller
        intent = TaxIntent(
            payer_id=seller.id,
            payee_id=mock_context.government.id,
            amount=1000,
            reason="vat_tax"
        )
        mock_context.taxation_system.calculate_tax_intents.return_value = [intent]

        # Mock SettlementSystem to capture the credits passed to settle_atomic
        mock_context.settlement_system.settle_atomic.return_value = True

        success = handler.handle(tx, buyer, seller, mock_context)

        assert success

        # Verify settle_atomic calls
        # args[0]: debit_agent (buyer)
        # args[1]: credits_list
        call_args = mock_context.settlement_system.settle_atomic.call_args
        assert call_args is not None
        debit_agent, credits, tick = call_args[0]

        assert debit_agent == buyer

        # Analyze credits
        # We expect:
        # 1. Government gets 1000 pennies
        # 2. Seller gets 9000 pennies (Trade 10000 - Tax 1000)
        # OR
        # 1. Government gets 1000 pennies
        # 2. Seller gets 10000 pennies
        # AND Buyer pays 11000? NO. If seller pays, Buyer should pay 10000.

        gov_credit = next((amt for agent, amt, reason in credits if agent == mock_context.government), 0)
        seller_credit = next((amt for agent, amt, reason in credits if agent == seller), 0)

        assert gov_credit == 1000

        # FAILURE EXPECTATION:
        # Current implementation credits seller with FULL trade_value (10000).
        # And adds tax to total_cost for buyer?
        # If Payer is Seller, current implementation might still add it to buyer's debit list?
        # Let's see what happens.

        # If the implementation is "Buyer pays everything in credits list", then:
        # Buyer pays 1000 (Gov) + 10000 (Seller) = 11000.
        # But Tax was supposed to be paid by Seller from their proceeds.
        # So Buyer SHOULD pay 10000.
        # Seller SHOULD get 9000.
        # Gov SHOULD get 1000.

        # If current implementation is broken, Seller gets 10000.
        if seller_credit == 10000:
            pytest.fail("GoodsTransactionHandler failed to deduct tax from seller proceeds (Seller-Paid Tax Scenario).")

        assert seller_credit == 9000

    def test_inheritance_manager_unit_mismatch(self):
        """
        Verify InheritanceManager handles mixed units (Pennies vs Dollars) correctly.
        Currently expected to FAIL if it mixes units.
        """
        # Mock Deceased Agent
        deceased = MagicMock(spec=Household)
        deceased.id = 666
        # Mock EconState
        deceased._econ_state = MagicMock(spec=EconStateDTO)
        # Assets in Pennies (10000 = $100)
        deceased._econ_state.assets = {DEFAULT_CURRENCY: 10000}
        # Mock balance_pennies property
        deceased.balance_pennies = 10000

        deceased._econ_state.portfolio = MagicMock()
        deceased._econ_state.portfolio.holdings = {}
        deceased._bio_state = MagicMock()
        deceased._bio_state.children_ids = []

        # Mock Real Estate (in Dollars?)
        # We need to mock simulation state
        simulation = MagicMock()
        simulation.time = 100
        simulation.real_estate_units = []
        # Mock a property worth $500 (Dollars)
        prop = MagicMock()
        prop.owner_id = deceased.id
        prop.estimated_value = 500.0 # Dollars
        simulation.real_estate_units.append(prop)

        simulation.stock_market = MagicMock()
        simulation.stock_market.get_daily_avg_price.return_value = 0.0 # Simplify

        simulation.bank = None # Disable bank for this test

        simulation.transaction_processor = MagicMock()
        simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]

        simulation.agents = MagicMock()
        simulation.agents.get.return_value = deceased

        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.4
        config.INHERITANCE_DEDUCTION = 0.0 # No deduction to force tax

        manager = InheritanceManager(config)

        # Execute
        transactions = manager.process_death(deceased, MagicMock(), simulation)

        # Check Tax Transaction
        # Total Wealth = 10000 (Cash) + 50000 (Property) = 60000.
        # Tax = 24000.
        # Liquidation of property (45000) happens. Cash -> 55000.
        # Tax Paid = 24000.

        tax_tx = next((tx for tx in transactions if tx.item_id == "inheritance_tax"), None)
        assert tax_tx is not None

        if tax_tx.total_pennies == 4200:
            pytest.fail("InheritanceManager unit mismatch: Calculated tax on mixed Pennies/Dollars sum.")

        assert tax_tx.total_pennies == 24000

import pytest
from unittest.mock import MagicMock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.portfolio import Portfolio
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

class TestInheritanceManager:
    @pytest.fixture
    def setup_manager(self):
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.0 # Simplify tests by disabling tax for now
        config.INHERITANCE_DEDUCTION = 1000000.0 # High deduction to avoid tax
        manager = InheritanceManager(config)
        return manager

    @pytest.fixture
    def mocks(self):
        simulation = MagicMock()
        simulation.settlement_system = MagicMock()
        simulation.settlement_system.transfer.return_value = True # Default success
        simulation.stock_market = MagicMock()
        simulation.stock_market.get_daily_avg_price.return_value = 10.0
        simulation.government = MagicMock()
        simulation.government.id = 888888
        simulation.real_estate_units = []

        # TD-232: Mock TransactionProcessor
        simulation.transaction_processor = MagicMock()
        success_result = MagicMock()
        success_result.success = True
        simulation.transaction_processor.execute.return_value = [success_result]

        return simulation

    def create_household(self, id, assets=0.0):
        h = MagicMock(spec=Household)
        h.id = id
        h._econ_state = MagicMock()
        h._bio_state = MagicMock()
        h._econ_state.assets = assets
        h._econ_state.portfolio = Portfolio(id)
        h._econ_state.owned_properties = []
        h._bio_state.is_active = True
        h._bio_state.children_ids = []
        return h

    def test_distribution_transaction_generation(self, setup_manager, mocks):
        """Test Case 1: Verify correct distribution transaction is generated for heirs."""
        deceased = self.create_household(1, assets=10000.0)
        deceased._econ_state.portfolio.add("FIRM_A", 100, 10.0)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        deceased._bio_state.children_ids = [2, 3]

        mocks.agents = {2: heir1, 3: heir2}

        # Configure get_balance to return integer pennies
        mocks.settlement_system.get_balance.side_effect = lambda agent_id, currency: int(10000.0 * 100) if agent_id == 1 else 0

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Check for distribution txs
        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) == 2 # 2 heirs = 2 transactions now

        recipients = sorted([t.seller_id for t in dist_txs])
        assert recipients == [2, 3]

        # Check amounts (5000.0 each)
        for tx in dist_txs:
            assert tx.price == 5000.0

    def test_multiple_heirs_metadata(self, setup_manager, mocks):
        """Test Case 2: Verify distribution for multiple heirs (uneven split)."""
        deceased = self.create_household(1, assets=100.00)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        heir3 = self.create_household(4)
        deceased._bio_state.children_ids = [2, 3, 4]
        mocks.agents = {2: heir1, 3: heir2, 4: heir3}

        # 100.00 -> 10000 pennies
        mocks.settlement_system.get_balance.side_effect = lambda agent_id, currency: 10000 if agent_id == 1 else 0

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) == 3

        # 10000 / 3 = 3333 r 1
        # Heirs get: 33.33, 33.33, 33.34
        prices = sorted([t.price for t in dist_txs])
        assert prices[0] == 33.33
        assert prices[1] == 33.33
        assert prices[2] == 33.34

    def test_escheatment_when_no_heirs(self, setup_manager, mocks):
        """Test Case 3: Verify escheatment transaction when no heirs exist."""
        deceased = self.create_household(1, assets=1000.0)
        deceased._bio_state.children_ids = [] # No children

        # Logic uses cash < tax checks which use float assets first, then settlement system if heirs exist.
        # But for escheatment, the code uses `if cash > 0`.
        # The logic for escheatment is still largely legacy based on 'cash' float variable unless updated.
        # Let's check process_death implementation again.

        # It uses 'cash' (float) for escheatment condition.

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Expect Escheatment transactions
        escheat_cash = next((t for t in txs if t.item_id == "escheatment"), None)
        assert escheat_cash is not None
        assert escheat_cash.buyer_id == 1
        assert escheat_cash.seller_id == mocks.government.id

    def test_zero_assets_distribution(self, setup_manager, mocks):
        """Test Case 4: Verify transaction even with zero assets (process usually runs)."""
        deceased = self.create_household(1, assets=0.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mocks.agents = {2: heir1}

        mocks.settlement_system.get_balance.return_value = 0

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Optimization: No transaction for 0 assets
        dist_tx = next((t for t in txs if t.transaction_type == "inheritance_distribution"), None)
        assert dist_tx is None

    def test_tax_transaction_generation(self, setup_manager, mocks):
        """Test Case 5: Verify tax transaction if tax rate > 0."""
        # Enable tax
        setup_manager.config_module.INHERITANCE_TAX_RATE = 0.5
        setup_manager.config_module.INHERITANCE_DEDUCTION = 0.0

        deceased = self.create_household(1, assets=1000.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mocks.agents = {2: heir1}

        # Mock balance after tax deduction (1000 - 500 = 500)
        mocks.settlement_system.get_balance.return_value = 50000

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        tax_tx = next((t for t in txs if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        assert tax_tx.price == 500.0 # 50% of 1000

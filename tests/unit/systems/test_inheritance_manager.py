import pytest
from unittest.mock import MagicMock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.portfolio import Portfolio
from simulation.models import Transaction

class TestInheritanceManager:
    @pytest.fixture
    def setup_manager(self):
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.0 # Simplify tests by disabling tax for now
        config.INHERITANCE_DEDUCTION = 1000000.0 # High deduction to avoid tax
        manager = InheritanceManager(config)
        manager.transaction_processor = MagicMock() # Inject TP
        return manager

    @pytest.fixture
    def mocks(self):
        simulation = MagicMock()
        simulation.settlement_system = MagicMock()
        simulation.stock_market = MagicMock()
        simulation.stock_market.get_daily_avg_price.return_value = 10.0
        simulation.government = MagicMock()
        simulation.government.id = 0
        simulation.real_estate_units = []

        # Mock execute_settlement side effect to return receipts
        def side_effect(account_id, plan, tick):
            receipts = []
            for recipient, amount, memo, tx_type in plan:
                 meta = {"memo": memo}
                 receipts.append({
                     "buyer_id": recipient.id if hasattr(recipient, 'id') else 0,
                     "seller_id": account_id,
                     "item_id": "currency",
                     "quantity": amount,
                     "price": 1.0,
                     "market_id": "system",
                     "transaction_type": tx_type,
                     "time": tick,
                     "metadata": meta
                 })
            return receipts

        simulation.settlement_system.execute_settlement.side_effect = side_effect

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

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Check for distribution txs
        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) == 2

        # Verify buyers are heirs
        buyer_ids = {t.buyer_id for t in dist_txs}
        assert buyer_ids == {2, 3}

    def test_multiple_heirs_metadata(self, setup_manager, mocks):
        """Test Case 2: Verify metadata for multiple heirs."""
        deceased = self.create_household(1, assets=100.00)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        heir3 = self.create_household(4)
        deceased._bio_state.children_ids = [2, 3, 4]
        mocks.agents = {2: heir1, 3: heir2, 4: heir3}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) == 3
        buyer_ids = {t.buyer_id for t in dist_txs}
        assert buyer_ids == {2, 3, 4}

    def test_escheatment_when_no_heirs(self, setup_manager, mocks):
        """Test Case 3: Verify escheatment transaction when no heirs exist."""
        deceased = self.create_household(1, assets=1000.0)
        deceased._bio_state.children_ids = [] # No children

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Expect Escheatment transactions
        # Transaction type should be "escheatment" (set in process_death plan)
        escheat_tx = next((t for t in txs if t.transaction_type == "escheatment"), None)
        assert escheat_tx is not None
        assert escheat_tx.buyer_id == mocks.government.id # Recipient is Gov

    def test_zero_assets_distribution(self, setup_manager, mocks):
        """Test Case 4: Verify transaction even with zero assets (process usually runs)."""
        deceased = self.create_household(1, assets=0.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mocks.agents = {2: heir1}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # With 0 assets and no RE, expected result is empty transactions list
        assert len(txs) == 0

    def test_tax_transaction_generation(self, setup_manager, mocks):
        """Test Case 5: Verify tax transaction if tax rate > 0."""
        # Enable tax
        setup_manager.config_module.INHERITANCE_TAX_RATE = 0.5
        setup_manager.config_module.INHERITANCE_DEDUCTION = 0.0

        deceased = self.create_household(1, assets=1000.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mocks.agents = {2: heir1}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        tax_tx = next((t for t in txs if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        # Price should be 500
        assert tax_tx.quantity * tax_tx.price == 500.0

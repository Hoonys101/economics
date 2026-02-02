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
        return manager

    @pytest.fixture
    def mocks(self):
        simulation = MagicMock()
        simulation.settlement_system = MagicMock()

        # Configure create_settlement to return an account with deceased_agent_id
        def create_settlement_side_effect(agent_id, **kwargs):
            account = MagicMock()
            account.deceased_agent_id = agent_id
            return account
        simulation.settlement_system.create_settlement.side_effect = create_settlement_side_effect

        simulation.stock_market = MagicMock()
        simulation.stock_market.get_daily_avg_price.return_value = 10.0
        simulation.government = MagicMock()
        simulation.real_estate_units = []
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

    def _mock_execute_settlement(self, mocks):
        # Helper to make execute_settlement return valid receipts
        def side_effect(account_id, plan, tick):
            receipts = []
            for recipient, amount, memo, tx_type in plan:
                receipts.append({
                    "buyer_id": recipient.id if hasattr(recipient, 'id') else recipient,
                    "seller_id": account_id,
                    "item_id": "currency",
                    "quantity": amount,
                    "price": 1.0,
                    "market_id": "settlement",
                    "transaction_type": tx_type,
                    "time": tick,
                    "metadata": {"memo": memo, "executed": True}
                })
            return receipts
        mocks.settlement_system.execute_settlement.side_effect = side_effect

    def test_distribution_transaction_generation(self, setup_manager, mocks):
        """Test Case 1: Verify correct distribution transaction is generated for heirs."""
        self._mock_execute_settlement(mocks)

        deceased = self.create_household(1, assets=10000.0)
        deceased._econ_state.portfolio.add("FIRM_A", 100, 10.0)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        deceased._bio_state.children_ids = [2, 3]

        mocks.agents = {2: heir1, 3: heir2}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Check for distribution txs
        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) >= 2

        # Check IDs
        # Buyer should be Heir (Receiver)
        heir_ids = {t.buyer_id for t in dist_txs}
        assert 2 in heir_ids
        assert 3 in heir_ids

    def test_multiple_heirs_metadata(self, setup_manager, mocks):
        """Test Case 2: Verify transactions for multiple heirs."""
        self._mock_execute_settlement(mocks)

        deceased = self.create_household(1, assets=100.00)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        heir3 = self.create_household(4)
        deceased._bio_state.children_ids = [2, 3, 4]
        mocks.agents = {2: heir1, 3: heir2, 4: heir3}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        # Should have 3 cash distributions
        assert len(dist_txs) == 3

        heir_ids = {t.buyer_id for t in dist_txs}
        assert heir_ids == {2, 3, 4}

    def test_escheatment_when_no_heirs(self, setup_manager, mocks):
        """Test Case 3: Verify escheatment transaction when no heirs exist."""
        self._mock_execute_settlement(mocks)

        deceased = self.create_household(1, assets=1000.0)
        deceased._bio_state.children_ids = [] # No children

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # Expect Escheatment transactions
        escheat_cash = next((t for t in txs if t.transaction_type == "escheatment"), None)
        assert escheat_cash is not None
        assert escheat_cash.buyer_id == mocks.government.id # Gov receives
        # seller is deceased (account)
        assert escheat_cash.seller_id == 1

    def test_zero_assets_distribution(self, setup_manager, mocks):
        """Test Case 4: Verify transaction even with zero assets (process usually runs)."""
        self._mock_execute_settlement(mocks)

        deceased = self.create_household(1, assets=0.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mocks.agents = {2: heir1}

        txs = setup_manager.process_death(deceased, mocks.government, mocks)

        # No cash to distribute, so no cash transactions.
        dist_txs = [t for t in txs if t.transaction_type == "inheritance_distribution"]
        assert len(dist_txs) == 0

    def test_tax_transaction_generation(self, setup_manager, mocks):
        """Test Case 5: Verify tax transaction if tax rate > 0."""
        self._mock_execute_settlement(mocks)

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
        assert tax_tx.quantity == 500.0 # 50% of 1000

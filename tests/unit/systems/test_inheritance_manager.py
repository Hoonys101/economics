import pytest
from unittest.mock import MagicMock, Mock
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.portfolio import Portfolio
from simulation.models import Transaction
from modules.lifecycle.api import ISuccessionContext, DebtStatusDTO

class TestInheritanceManager:
    @pytest.fixture
    def setup_manager(self):
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.0 # Simplify tests by disabling tax for now
        config.INHERITANCE_DEDUCTION = 1000000.0 # High deduction to avoid tax
        manager = InheritanceManager(config)
        return manager

    @pytest.fixture
    def mock_context(self):
        context = MagicMock(spec=ISuccessionContext)
        context.current_tick = 100
        context.government_id = 999
        context.get_real_estate_units.return_value = []
        context.get_stock_price.return_value = 10.0
        context.get_debt_status.return_value = DebtStatusDTO(total_outstanding_pennies=0, loans=[])
        context.get_active_heirs.return_value = []

        # Mock transaction execution to always succeed
        success_result = MagicMock()
        success_result.success = True
        context.execute_transactions.return_value = [success_result]
        return context

    def create_household(self, id, assets=0.0):
        h = MagicMock(spec=Household)
        h.id = id
        h._econ_state = MagicMock()
        h._bio_state = MagicMock()
        h._econ_state.assets = assets
        h._econ_state.wallet = MagicMock()
        h._econ_state.wallet.owner_id = id  # Required for shared wallet check
        h._econ_state.portfolio = Portfolio(id)
        h._econ_state.owned_properties = []
        h._bio_state.is_active = True
        h._bio_state.children_ids = []
        return h

    def test_distribution_transaction_generation(self, setup_manager, mock_context):
        """Test Case 1: Verify correct distribution transaction is generated for heirs."""
        deceased = self.create_household(1, assets=10000.0)
        deceased._econ_state.portfolio.add("FIRM_A", 100, 10.0)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        deceased._bio_state.children_ids = [2, 3]

        mock_context.get_active_heirs.return_value = [heir1, heir2]

        txs = setup_manager.process_death(deceased, mock_context)

        # Check for distribution tx
        dist_tx = next((t for t in txs if t.transaction_type == "inheritance_distribution"), None)
        assert dist_tx is not None
        assert dist_tx.buyer_id == 1
        assert set(dist_tx.metadata.original_metadata["heir_ids"]) == {2, 3}
        assert dist_tx.market_id == "system"

    def test_multiple_heirs_metadata(self, setup_manager, mock_context):
        """Test Case 2: Verify metadata for multiple heirs."""
        deceased = self.create_household(1, assets=100.00)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        heir3 = self.create_household(4)
        deceased._bio_state.children_ids = [2, 3, 4]
        mock_context.get_active_heirs.return_value = [heir1, heir2, heir3]

        txs = setup_manager.process_death(deceased, mock_context)

        dist_tx = next((t for t in txs if t.transaction_type == "inheritance_distribution"), None)
        assert dist_tx is not None
        assert set(dist_tx.metadata.original_metadata["heir_ids"]) == {2, 3, 4}

    def test_escheatment_when_no_heirs(self, setup_manager, mock_context):
        """Test Case 3: Verify escheatment transaction when no heirs exist."""
        deceased = self.create_household(1, assets=1000.0)
        deceased._bio_state.children_ids = [] # No children
        mock_context.get_active_heirs.return_value = []

        txs = setup_manager.process_death(deceased, mock_context)

        # Expect Escheatment transactions
        escheat_cash = next((t for t in txs if t.item_id == "escheatment"), None)
        assert escheat_cash is not None
        assert escheat_cash.buyer_id == 1
        assert escheat_cash.seller_id == mock_context.government_id

    def test_zero_assets_distribution(self, setup_manager, mock_context):
        """Test Case 4: Verify transaction even with zero assets (process usually runs)."""
        deceased = self.create_household(1, assets=0.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mock_context.get_active_heirs.return_value = [heir1]

        txs = setup_manager.process_death(deceased, mock_context)

        # Optimization: No transaction for 0 assets
        dist_tx = next((t for t in txs if t.transaction_type == "inheritance_distribution"), None)
        assert dist_tx is None

    def test_tax_transaction_generation(self, setup_manager, mock_context):
        """Test Case 5: Verify tax transaction if tax rate > 0."""
        # Enable tax
        setup_manager.config_module.INHERITANCE_TAX_RATE = 0.5
        setup_manager.config_module.INHERITANCE_DEDUCTION = 0.0

        deceased = self.create_household(1, assets=1000.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mock_context.get_active_heirs.return_value = [heir1]

        txs = setup_manager.process_death(deceased, mock_context)

        tax_tx = next((t for t in txs if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        assert tax_tx.price == 500.0 # 50% of 1000

    def test_shared_wallet_guest_proportion(self, setup_manager, mock_context):
        """Test Case 6: Verify guest in shared wallet is taxed on their SHARE (e.g. 50%), not 0% or 100%."""
        # Setup: Deceased is a guest in Household 100's wallet (Balance: 1000)
        # Default share ratio is 0.5
        setup_manager.config_module.JOINT_ACCOUNT_SHARE = 0.5
        setup_manager.config_module.INHERITANCE_TAX_RATE = 0.1
        setup_manager.config_module.INHERITANCE_DEDUCTION = 0.0
        from modules.system.api import DEFAULT_CURRENCY

        deceased = self.create_household(1)
        deceased._econ_state.wallet.owner_id = 100 # Different owner -> Shared Wallet Guest
        deceased._econ_state.wallet.get_balance.return_value = 1000
        
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2]
        mock_context.get_active_heirs.return_value = [heir1]

        txs = setup_manager.process_death(deceased, mock_context)

        # Tax should be based on 50% of 1000 = 500. 10% tax on 500 = 50.
        tax_tx = next((t for t in txs if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        assert tax_tx.price == 50.0 # 10% of (1000 * 0.5)

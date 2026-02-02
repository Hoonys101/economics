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
        # h._econ_state.portfolio.to_legacy_dict() = {} # Removed
        h._econ_state.owned_properties = []
        h._bio_state.is_active = True
        h._bio_state.children_ids = []
        return h

    def test_even_split(self, setup_manager, mocks):
        """Test Case 1 (Even Split): 10,000 cash, 100 shares, 2 heirs."""
        deceased = self.create_household(1, assets=10000.0)
        deceased._econ_state.portfolio.add("FIRM_A", 100, 10.0)
        # deceased.shares_owned["FIRM_A"] = 100 # Removed

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        deceased._bio_state.children_ids = [2, 3] # Fixed

        mocks.agents = {2: heir1, 3: heir2}

        setup_manager.process_death(deceased, mocks.government, mocks)

        # Verify Cash
        # 10000 / 2 = 5000 each
        # Check calls to settlement.transfer
        # Expect 2 calls of 5000
        calls = mocks.settlement_system.transfer.call_args_list
        assert len(calls) == 2

        amounts = [c[0][2] for c in calls]
        assert amounts == [5000.0, 5000.0]

        # Verify Stocks
        # 100 / 2 = 50 each
        assert heir1._econ_state.portfolio.holdings["FIRM_A"].quantity == 50
        assert heir2._econ_state.portfolio.holdings["FIRM_A"].quantity == 50

        # Verify remainder not sent to government
        mocks.government.record_revenue.assert_not_called()

        # Verify cleanup
        assert len(deceased._econ_state.portfolio.holdings) == 0
        # assert len(deceased.shares_owned) == 0

    def test_uneven_split(self, setup_manager, mocks):
        """Test Case 2 (Uneven Split): 10,000.01 cash, 101 shares, 2 heirs."""
        deceased = self.create_household(1, assets=10000.01)
        deceased._econ_state.portfolio.add("FIRM_A", 101, 10.0)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        deceased._bio_state.children_ids = [2, 3] # Fixed
        mocks.agents = {2: heir1, 3: heir2}

        setup_manager.process_death(deceased, mocks.government, mocks)

        # Verify Cash
        # 10000.01 = 1000001 pennies
        # / 2 = 500000 pennies (5000.00) remainder 1 penny (0.01)
        # Heir 1: 5000.00
        # Heir 2: 5000.01

        calls = mocks.settlement_system.transfer.call_args_list
        # Filter for transfers to heirs (exclude potential tax/residual if any, though tax is 0)
        heir_calls = [c for c in calls if c[0][1] in [heir1, heir2]]
        assert len(heir_calls) == 2

        amounts = sorted([c[0][2] for c in heir_calls])
        assert amounts == [5000.00, 5000.01]

        # Verify Stocks
        # 101 / 2 = 50 remainder 1
        # Heir 1 gets 50? Heir 2 gets 50? Remainder distributed to first in loop (0 index)?
        # Implementation detail: loop through remainder.
        # total 101.
        q1 = heir1._econ_state.portfolio.holdings["FIRM_A"].quantity
        q2 = heir2._econ_state.portfolio.holdings["FIRM_A"].quantity
        assert q1 + q2 == 101
        assert abs(q1 - q2) == 1

        # Verify cleanup
        assert len(deceased._econ_state.portfolio.holdings) == 0
        # assert len(deceased.shares_owned) == 0

    def test_multiple_heirs(self, setup_manager, mocks):
        """Test Case 3 (Multiple Heirs): 100.00 cash, 10 shares, 3 heirs."""
        deceased = self.create_household(1, assets=100.00)
        deceased._econ_state.portfolio.add("FIRM_A", 10, 10.0)

        heir1 = self.create_household(2)
        heir2 = self.create_household(3)
        heir3 = self.create_household(4)
        deceased._bio_state.children_ids = [2, 3, 4] # Fixed
        mocks.agents = {2: heir1, 3: heir2, 4: heir3}

        setup_manager.process_death(deceased, mocks.government, mocks)

        # Cash: 10000 pennies / 3 = 3333 r 1
        # 33.33, 33.33, 33.34
        calls = mocks.settlement_system.transfer.call_args_list
        heir_calls = [c for c in calls if c[0][1] in [heir1, heir2, heir3]]
        amounts = sorted([c[0][2] for c in heir_calls])
        assert amounts == [33.33, 33.33, 33.34]

        # Stocks: 10 / 3 = 3 r 1
        # 3, 3, 4 (or 4, 3, 3 depending on distribution order)
        quantities = sorted([
            heir1._econ_state.portfolio.holdings["FIRM_A"].quantity,
            heir2._econ_state.portfolio.holdings["FIRM_A"].quantity,
            heir3._econ_state.portfolio.holdings["FIRM_A"].quantity
        ])
        assert quantities == [3, 3, 4]

    def test_zero_assets(self, setup_manager, mocks):
        """Test Case 4 (Zero Assets): 0 cash, 0 shares."""
        deceased = self.create_household(1, assets=0.0)
        heir1 = self.create_household(2)
        deceased._bio_state.children_ids = [2] # Fixed
        mocks.agents = {2: heir1}

        setup_manager.process_death(deceased, mocks.government, mocks)

        # No transfers
        mocks.settlement_system.transfer.assert_not_called()
        assert len(heir1._econ_state.portfolio.holdings) == 0

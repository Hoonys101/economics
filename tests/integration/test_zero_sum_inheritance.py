import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.dtos.settlement_dtos import EstateSettlementSaga
from simulation.core_agents import Household
from simulation.agents.government import Government

class MockAgent:
    def __init__(self, id, initial_cash, is_gov=False):
        self.id = id
        self.is_gov = is_gov
        self._econ_state = MagicMock()
        self._econ_state.assets = initial_cash
        self._bio_state = MagicMock()
        self._bio_state.children_ids = []
        self._bio_state.is_active = True
        self.portfolio = MagicMock()

        # Mock holdings
        self._econ_state.portfolio.holdings = {}

        # For remove_stock, we need it to return something if stock exists
        self.shares = {}

    def set_shares(self, firm_id, qty):
        self.shares[firm_id] = qty
        self._econ_state.portfolio.holdings[firm_id] = MagicMock(quantity=qty)

        # Setup remove_stock to return a mock share
        def remove(fid, q):
            if self.shares.get(fid, 0) >= q:
                self.shares[fid] -= q
                return MagicMock(quantity=q, acquisition_price=0)
            return None
        self._econ_state.portfolio.remove_stock.side_effect = remove

        # Setup add_stock (for Gov/Heir rollback)
        def add(share):
            pass
        self.portfolio.add_stock.side_effect = add
        self._econ_state.portfolio.add_stock.side_effect = add

    @property
    def assets(self):
        if self.is_gov:
             return getattr(self, '_assets', 0.0)
        return self._econ_state.assets

    @assets.setter
    def assets(self, value):
        if self.is_gov:
            self._assets = value
        else:
            self._econ_state.assets = value

    def deposit(self, amount):
        self.assets += amount

    def withdraw(self, amount):
        self.assets -= amount


class TestZeroSumInheritance:
    def test_zero_sum_conservation_simple(self):
        # Setup
        logger = MagicMock()
        settlement_system = SettlementSystem(logger=logger)
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.4
        config.INHERITANCE_DEDUCTION = 0.0
        inheritance_manager = InheritanceManager(config_module=config)

        state = MagicMock()
        state.time = 1
        state.settlement_system = settlement_system
        state.real_estate_units = []
        state.stock_market = MagicMock()
        state.stock_market.get_daily_avg_price.return_value = 100.0

        deceased = MockAgent(101, 1000.0)
        deceased._bio_state.is_active = False
        deceased.set_shares(1, 10) # 10 * 100 = 1000 Value
        # Total Wealth = 2000. Tax = 800. Cash 1000 > 800. No Liq.

        heir = MockAgent(102, 0.0)
        deceased._bio_state.children_ids = [102]

        gov = MockAgent(1, 100000.0, is_gov=True)
        gov.assets = 100000.0 # Explicitly set for property logic

        state.agents = {101: deceased, 102: heir, 1: gov}

        initial_money = deceased.assets + heir.assets + gov.assets

        saga = inheritance_manager.process_death(deceased, gov, state)
        settlement_system.submit_saga(saga)
        settlement_system.execute(state)

        final_money = deceased.assets + heir.assets + gov.assets

        # Deceased pays 800 tax -> Gov. Deceased has 200.
        # Deceased pays 200 dist -> Heir. Deceased has 0.

        assert abs(final_money - initial_money) < 0.01
        assert abs(deceased.assets) < 0.01
        assert abs(heir.assets - 200.0) < 0.01
        assert abs(gov.assets - 100800.0) < 0.01

    def test_zero_sum_with_liquidation(self):
        # Cash < Tax
        logger = MagicMock()
        settlement_system = SettlementSystem(logger=logger)
        config = MagicMock()
        config.INHERITANCE_TAX_RATE = 0.5
        config.INHERITANCE_DEDUCTION = 0.0
        inheritance_manager = InheritanceManager(config_module=config)

        state = MagicMock()
        state.time = 1
        state.settlement_system = settlement_system
        state.real_estate_units = []
        state.stock_market = MagicMock()
        state.stock_market.get_daily_avg_price.return_value = 100.0

        deceased = MockAgent(101, 100.0) # 100 Cash
        deceased._bio_state.is_active = False
        deceased.set_shares(1, 20) # 20 * 100 = 2000 Value
        # Total Wealth = 2100. Tax = 1050.
        # Cash 100 < 1050. Needs Liquidation.

        heir = MockAgent(102, 0.0)
        deceased._bio_state.children_ids = [102]

        gov = MockAgent(1, 100000.0, is_gov=True)
        gov.assets = 100000.0

        state.agents = {101: deceased, 102: heir, 1: gov}

        initial_money = deceased.assets + heir.assets + gov.assets

        saga = inheritance_manager.process_death(deceased, gov, state)
        settlement_system.submit_saga(saga)
        settlement_system.execute(state)

        final_money = deceased.assets + heir.assets + gov.assets

        # Liquidation: 2000 Stock -> Gov. Gov pays 2000 -> Deceased.
        # Deceased Cash: 100 + 2000 = 2100.
        # Tax: 1050 -> Gov.
        # Remaining: 1050 -> Heir.

        assert abs(final_money - initial_money) < 0.01
        assert abs(deceased.assets) < 0.01
        assert abs(heir.assets - 1050.0) < 0.01
        assert abs(gov.assets - (100000.0 - 2000.0 + 1050.0)) < 0.01 # Gov paid 2000, got 1050 tax.

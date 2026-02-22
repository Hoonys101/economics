import unittest
from unittest.mock import MagicMock
from typing import Dict, List

from simulation.systems.liquidation_manager import LiquidationManager
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, AssetBuyoutResultDTO
from modules.system.registry import AgentRegistry
from modules.hr.service import HRService
from modules.finance.service import TaxService
from modules.finance.api import EquityStake

class TestMultiCurrencyLiquidation(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock()
        self.mock_settlement.transfer.return_value = True

        self.agent_registry = AgentRegistry()
        self.hr_service = HRService()
        self.tax_service = TaxService(self.agent_registry)
        self.mock_shareholder_registry = MagicMock()

        # Mock public manager
        self.mock_public_manager = MagicMock()
        self.mock_public_manager.managed_inventory = {}
        self.mock_public_manager.execute_asset_buyout.return_value = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=0,
            transaction_id="default_tx",
            items_acquired={},
            buyer_id=999
        )

        self.manager = LiquidationManager(
            self.mock_settlement,
            self.hr_service,
            self.tax_service,
            self.agent_registry,
            self.mock_shareholder_registry,
            self.mock_public_manager
        )

        self.firm = MagicMock(spec=Firm)
        self.firm.id = 1
        self.firm.config = MagicMock()
        self.firm.config.goods_initial_price = {}
        self.firm.inventory = {}
        self.firm.last_prices = {}
        self.firm.capital_stock = 0.0
        self.firm.finance = MagicMock()
        self.firm.finance.current_profit = 0.0
        self.firm.finance.balance = {DEFAULT_CURRENCY: 1000.0, "KRW": 50000.0}
        self.firm.liquidate_assets.return_value = self.firm.finance.balance.copy()

        self.firm.hr = MagicMock()
        self.firm.hr.employees = []
        self.firm.total_shares = 100.0
        self.firm.treasury_shares = 0.0
        self.firm.total_debt = 0.0
        # Mock get_equity_stakes to simulate 100% ownership by shareholder 101
        self.firm.get_equity_stakes.return_value = [
            EquityStake(shareholder_id=101, ratio=1.0)
        ]

        self.state = MagicMock(spec=SimulationState)
        self.state.time = 100
        self.state.agents = {}
        self.state.households = []
        self.state.government = None # Simplify

        self.agent_registry.set_state(self.state)

    def test_foreign_currency_distribution_to_shareholders(self):
        """
        Verify that foreign currency assets are distributed to shareholders
        after debts are paid.
        """
        # Setup Shareholder
        shareholder = MagicMock(spec=Household)
        shareholder.id = 101
        shareholder.shares_owned = {1: 100.0} # 100% ownership

        self.state.households = [shareholder]
        self.state.agents[101] = shareholder

        # Execute
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify Transfers
        # Expect:
        # 1. 1000.0 USD to Shareholder
        # 2. 50000.0 KRW to Shareholder

        calls = self.mock_settlement.transfer.call_args_list

        usd_transfer = False
        krw_transfer = False

        for call in calls:
            args = call[0]
            kwargs = call[1]
            payee = args[1]
            amount = args[2]
            currency = kwargs.get('currency', DEFAULT_CURRENCY)

            if payee.id == 101:
                if currency == DEFAULT_CURRENCY and amount == 1000.0:
                    usd_transfer = True
                elif currency == "KRW" and amount == 50000.0:
                    krw_transfer = True

        self.assertTrue(usd_transfer, "Shareholder should receive 1000 USD")
        self.assertTrue(krw_transfer, "Shareholder should receive 50000 KRW")

if __name__ == '__main__':
    unittest.main()

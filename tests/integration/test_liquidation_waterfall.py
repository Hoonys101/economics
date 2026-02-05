import unittest
from unittest.mock import MagicMock, Mock
from typing import List

from simulation.systems.liquidation_manager import LiquidationManager
from modules.common.dtos import Claim
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState
from simulation.dtos.config_dtos import FirmConfigDTO
from modules.system.api import IAssetRecoverySystem, DEFAULT_CURRENCY
from modules.system.registry import AgentRegistry
from modules.hr.service import HRService
from modules.finance.service import TaxService

class TestLiquidationWaterfallIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock()
        self.mock_public_manager = MagicMock(spec=IAssetRecoverySystem)
        self.mock_public_manager.managed_inventory = {}
        self.mock_public_manager.id = 999
        self.mock_settlement.transfer.return_value = True # Default success

        # Use Real Services
        self.agent_registry = AgentRegistry()
        self.hr_service = HRService()
        self.tax_service = TaxService(self.agent_registry)

        self.manager = LiquidationManager(
            self.mock_settlement,
            self.hr_service,
            self.tax_service,
            self.agent_registry,
            self.mock_public_manager
        )

        # Setup Config
        self.config = MagicMock(spec=FirmConfigDTO)
        self.config.ticks_per_year = 365
        self.config.severance_pay_weeks = 2.0
        self.config.corporate_tax_rate = 0.2
        self.config.labor_market_min_wage = 10.0
        self.config.halo_effect = 0.0

        # Setup Firm
        self.firm = MagicMock(spec=Firm)
        self.firm.id = 1
        self.firm.config = self.config
        self.firm.finance = MagicMock()
        self.firm.finance.balance = {DEFAULT_CURRENCY: 0.0} # Start with 0 cash
        self.firm.finance.current_profit = 0.0 # Fix 1

        # Configure liquidate_assets to return current balance
        self.firm.liquidate_assets.side_effect = lambda tick: self.firm.finance.balance

        self.firm.inventory = {}
        self.firm.last_prices = {}
        self.firm.hr = MagicMock()
        self.firm.hr.employees = []
        self.firm.hr.employee_wages = {}
        self.firm.hr.unpaid_wages = {}
        self.firm.total_shares = 1000.0
        self.firm.treasury_shares = 0.0
        self.firm.total_debt = 0.0

        # Setup State
        self.state = MagicMock(spec=SimulationState)
        self.state.time = 2000 # Increased to accommodate 3y history
        self.state.agents = {}
        self.state.households = []
        self.state.government = MagicMock()
        self.state.government.id = "government"
        # Mock shares_owned.get for government to avoid TypeError
        self.state.government.shares_owned.get.return_value = 0.0

    def _setup_registry(self):
        self.agent_registry.set_state(self.state)

    def test_severance_priority_over_shareholders(self):
        """
        Verify that employees receive severance before shareholders receive any dividends.
        Scenario:
        - Cash: 5000
        - Employee A: 3 years tenure, wage 100. Claim: 3yr * 2wk * 7day * 100 = 4200.
        - Employee B: 1 year tenure, wage 100. Claim: 1yr * 2wk * 7day * 100 = 1400.
        - Total Tier 1: 5600.
        - Shortfall: 600.
        - Expected: Employees get pro-rata (5000/5600 ratio). Shareholders get 0.
        """
        self._setup_registry()
        self.firm.finance.balance = {DEFAULT_CURRENCY: 5000.0}

        # Employee A
        empA = MagicMock(spec=Household)
        empA.id = 101
        empA._econ_state = MagicMock()
        empA._econ_state.employment_start_tick = 2000 - (365 * 3) # 3 years

        # Employee B
        empB = MagicMock(spec=Household)
        empB.id = 102
        empB._econ_state = MagicMock()
        empB._econ_state.employment_start_tick = 2000 - 365 # 1 year

        self.firm.hr.employees = [empA, empB]
        self.firm.hr.employee_wages = {101: 100.0, 102: 100.0}

        # Register in state
        self.state.agents[101] = empA
        self.state.agents[102] = empB

        # Run Liquidation
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify Transfers
        # Total Claims = 4200 + 1400 = 5600.
        # Ratio = 5000 / 5615.38 (approx)
        # But A has 3 years, B has 1 year. 3:1 ratio of claims.
        # Total Cash 5000.
        # A gets 5000 * 0.75 = 3750.
        # B gets 5000 * 0.25 = 1250.

        expected_A = 3750.0
        expected_B = 1250.0

        # Check call args
        calls = self.mock_settlement.transfer.call_args_list
        self.assertEqual(len(calls), 2)

        # Extract amounts paid
        paid_amounts = {}
        for call in calls:
            args, _ = call
            # args: (from, to, amount, memo)
            payee = args[1]
            amount = args[2]
            paid_amounts[payee.id] = amount

        self.assertAlmostEqual(paid_amounts[101], expected_A)
        self.assertAlmostEqual(paid_amounts[102], expected_B)

        # Verify Shareholders got nothing (no calls to shareholder agents)
        # Note: In this test setup, households list is empty so no shareholders loop ran anyway,
        # but execute_waterfall logic puts Equity at Tier 5, and loop breaks if cash=0.

    def test_waterfall_tiers(self):
        """
        Verify Tier 1 > Tier 2 > Tier 5.
        Scenario:
        - Cash: 10000.
        - Tier 1 (Severance): 2000.
        - Tier 2 (Debt): 5000.
        - Remaining: 3000.
        - Tier 5 (Equity): Should receive 3000.
        """
        self._setup_registry()
        self.firm.finance.balance = {DEFAULT_CURRENCY: 10000.0}

        # Employee (Tier 1) - 2000 claim
        # 2000 = Tenure * 2 * 7 * 100 => Tenure * 1400 = 2000 => Tenure = 1.42 yrs
        ticks = 1.428 * 365
        emp = MagicMock(spec=Household)
        emp.id = 101
        emp._econ_state = MagicMock()
        emp._econ_state.employment_start_tick = 2000 - int(ticks)

        self.firm.hr.employees = [emp]
        self.firm.hr.employee_wages = {101: 100.0}

        # Debt (Tier 2) - 5000
        self.firm.total_debt = 5000.0
        bank = MagicMock()
        bank.id = "bank"
        self.firm.decision_engine = MagicMock() # Fix 2
        self.firm.decision_engine.loan_market.bank = bank

        # Shareholders (Tier 5)
        shareholder = MagicMock(spec=Household)
        shareholder.id = 201
        shareholder.shares_owned = {1: 500.0} # 50% ownership

        self.state.households = [shareholder]
        self.state.agents[101] = emp
        self.state.agents["bank"] = bank
        self.state.agents[201] = shareholder

        # Run
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify
        # 1. Employee Paid Full 2000 (Approx)
        # 2. Bank Paid Full 5000
        # 3. Shareholder Paid 1500 (50% of 3000 remaining)

        # Calculate exact severance claim
        tenure = (2000 - emp._econ_state.employment_start_tick) / 365.0
        severance = tenure * 2.0 * (365/52) * 100.0

        remaining = 10000.0 - severance - 5000.0
        equity_payout = remaining * (500.0 / 1000.0)

        transfers = self.mock_settlement.transfer.call_args_list

        paid_map = {}
        for call in transfers:
            payee = call[0][1]
            amt = call[0][2]
            paid_map[payee.id] = amt

        self.assertAlmostEqual(paid_map[101], severance)
        self.assertAlmostEqual(paid_map["bank"], 5000.0)
        self.assertAlmostEqual(paid_map[201], equity_payout)

    def test_asset_rich_cash_poor_liquidation(self):
        """
        TD-187-LEAK Fix Verification.
        Scenario:
        - Cash: 0.0
        - Inventory: 100 units of 'Apples' @ 10.0 market price.
        - Liquidation Value: 100 * 10 * 0.8 (haircut) = 800.0
        - Severance Claim: 500.0

        Expected:
        - PublicManager buys inventory for 800.0.
        - Firm Balance becomes 800.0.
        - Employee paid 500.0.
        - Equity (or Escheatment) gets 300.0.
        """
        self._setup_registry()
        self.firm.finance.balance = {DEFAULT_CURRENCY: 0.0}
        self.firm.inventory = {"apples": 100.0}
        self.firm.last_prices = {"apples": 10.0}

        # Mock public manager managed inventory update
        self.mock_public_manager.managed_inventory = {"apples": 0.0}
        self.mock_public_manager.receive_liquidated_assets = MagicMock()

        # Employee Claim 500.0
        # 500 = Tenure * 2 * 7 * 100 => Tenure = 0.35 yrs
        ticks = 0.357 * 365
        emp = MagicMock(spec=Household)
        emp.id = 101
        emp._econ_state = MagicMock()
        emp._econ_state.employment_start_tick = 2000 - int(ticks)

        self.firm.hr.employees = [emp]
        self.firm.hr.employee_wages = {101: 100.0}

        self.state.agents[101] = emp

        # To simulate cash update after transfer, we need side_effect on transfer
        def transfer_side_effect(sender, receiver, amount, memo, currency=None):
            if receiver == self.firm:
                cur = currency or DEFAULT_CURRENCY
                self.firm.finance.balance[cur] = self.firm.finance.balance.get(cur, 0.0) + amount
            return True

        self.mock_settlement.transfer.side_effect = transfer_side_effect

        # Run
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify
        # 1. PublicManager -> Firm Transfer (800.0)
        self.mock_settlement.transfer.assert_any_call(
            self.mock_public_manager,
            self.firm,
            800.0,
            "Asset Liquidation (Inventory) - Firm 1",
            currency=DEFAULT_CURRENCY
        )

        # 2. Firm -> Employee Transfer (500.0)
        # Note: Match float roughly
        # severance = 0.357 * 2.0 * 7.019 * 100 ~= 500

        # Find payout
        payout = 0.0
        for call in self.mock_settlement.transfer.call_args_list:
            if call[0][0] == self.firm and call[0][1] == emp:
                payout = call[0][2]
                break

        self.assertGreater(payout, 490.0)
        self.assertLess(payout, 510.0)

        # 3. Verify Inventory Cleared
        self.assertEqual(self.firm.inventory, {})
        # 4. Verify Public Manager received inventory via interface
        self.mock_public_manager.receive_liquidated_assets.assert_called_with({"apples": 100.0})

if __name__ == '__main__':
    unittest.main()

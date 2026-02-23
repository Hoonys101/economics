import unittest
from unittest.mock import MagicMock, call
from typing import List

from simulation.systems.liquidation_manager import LiquidationManager
from modules.common.financial.dtos import Claim
from simulation.firms import Firm
from simulation.dtos.api import SimulationState
from modules.system.api import IAssetRecoverySystem, IAgentRegistry, DEFAULT_CURRENCY, AssetBuyoutResultDTO
from modules.hr.api import IHRService
from modules.finance.api import ITaxService, ILiquidatable
from simulation.finance.api import ISettlementSystem
from modules.simulation.api import IConfigurable, LiquidationConfigDTO, IShareholderRegistry

class TestLiquidationManager(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock(spec=ISettlementSystem)
        self.mock_hr = MagicMock(spec=IHRService)
        self.mock_tax = MagicMock(spec=ITaxService)
        self.mock_registry = MagicMock(spec=IAgentRegistry)
        self.mock_shareholder = MagicMock(spec=IShareholderRegistry)
        self.mock_public = MagicMock(spec=IAssetRecoverySystem)
        self.mock_public.receive_liquidated_assets = MagicMock()
        self.mock_public.execute_asset_buyout.return_value = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=0,
            transaction_id="default_tx",
            items_acquired={},
            buyer_id=999
        )

        self.manager = LiquidationManager(
            self.mock_settlement,
            self.mock_hr,
            self.mock_tax,
            self.mock_registry,
            self.mock_shareholder,
            self.mock_public
        )

        self.firm = MagicMock(spec=Firm)
        self.firm.id = 1
        # Mock liquidate_assets to return cash balance dictionary (TD-033)
        self.firm.liquidate_assets.return_value = {DEFAULT_CURRENCY: 1000.0}
        
        # New ILiquidatable requirements
        self.firm.get_all_claims = MagicMock(return_value=[])
        self.firm.get_equity_stakes = MagicMock(return_value=[])
        
        self.firm.total_shares = 1000.0
        self.firm.treasury_shares = 0.0
        self.firm.total_debt = 0.0
        # Mock last_prices and inventory for asset liquidation check
        self.firm.last_prices = {}
        self.firm.inventory = {}
        
        # Add required protocol methods
        self.firm.get_liquidation_config = MagicMock()
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={},
            default_price=10.0,
            market_prices={}
        )

        self.state = MagicMock(spec=SimulationState)
        self.state.time = 100
        # For shareholder iteration in tier 5
        self.state.households = []
        self.state.government = None

    def test_initiate_liquidation_orchestration(self):
        # Setup Claims returned by services
        claim_hr = Claim(creditor_id=101, amount_pennies=100, tier=1, description="Wage")
        claim_tax = Claim(creditor_id="gov", amount_pennies=50, tier=3, description="Tax")

        # Mock Registry resolution
        agent_101 = MagicMock()
        agent_101.id = 101
        agent_gov = MagicMock()
        agent_gov.id = "gov"

        self.mock_registry.get_agent.side_effect = lambda x: {101: agent_101, "gov": agent_gov}.get(x)
        self.mock_settlement.transfer.return_value = True
        
        # Mock Claims via Protocol
        self.firm.get_all_claims.return_value = [claim_hr, claim_tax]

        # Run
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify Firm Write-off
        self.firm.liquidate_assets.assert_called_once_with(self.state.time)

        # Verify Transfers
        # Expect transfers for both claims (Values cast to int by manager)
        self.mock_settlement.transfer.assert_has_calls([
            call(self.firm, agent_101, 100, "Liquidation Payout: Wage", currency=DEFAULT_CURRENCY),
            call(self.firm, agent_gov, 50, "Liquidation Payout: Tax", currency=DEFAULT_CURRENCY)
        ], any_order=True)

    def test_bank_claim_handling(self):
        # Setup Bank Debt
        self.firm.total_debt = 500

        # Mock Decision Engine structure since Firm is a spec mock
        self.firm.decision_engine = MagicMock()
        bank = MagicMock()
        bank.id = "bank_1"
        self.firm.decision_engine.loan_market.bank = bank

        bank_agent = MagicMock()
        bank_agent.id = "bank_1"
        self.mock_registry.get_agent.return_value = bank_agent
        
        # Mock Bank Claim via Protocol
        bank_claim = Claim(creditor_id="bank_1", amount_pennies=500, tier=2, description="Secured Loan")
        self.firm.get_all_claims.return_value = [bank_claim]

        self.manager.initiate_liquidation(self.firm, self.state)

        # Check transfer to bank
        self.mock_settlement.transfer.assert_called_with(
            self.firm, bank_agent, 500, "Liquidation Payout: Secured Loan", currency=DEFAULT_CURRENCY
        )

    def test_asset_liquidation_integration(self):
        # Setup Inventory
        self.firm.inventory = {"apple": 10}
        self.firm.get_all_items = MagicMock(return_value={"apple": 10})
        self.firm.get_liquidation_config.return_value = LiquidationConfigDTO(
            haircut=0.2,
            initial_prices={"default": 1000},
            default_price=1000,
            market_prices={"apple": 500}
        )

        self.mock_public.execute_asset_buyout.return_value = AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=4000, # 40.0 * 100
            transaction_id="buyout_tx",
            items_acquired={"apple": 10},
            buyer_id=999
        )

        self.mock_settlement.transfer.return_value = True

        self.manager.initiate_liquidation(self.firm, self.state)

        # Check transfer for asset liquidation
        # 10 * 500 * 0.8 = 4000.0
        # Note: Code uses "Agent {id}" not "Firm {id}"
        self.mock_settlement.transfer.assert_any_call(
            self.mock_public,
            self.firm,
            4000, # 40.0 * 100 pennies
            "Asset Liquidation (Inventory) - Agent 1",
            currency=DEFAULT_CURRENCY
        )

        # Also check execute_asset_buyout
        self.mock_public.execute_asset_buyout.assert_called()
        args, _ = self.mock_public.execute_asset_buyout.call_args
        self.assertEqual(args[0].inventory, {"apple": 10})
        # Check inventory is cleared via clearing method
        self.firm.clear_inventory.assert_called_once()

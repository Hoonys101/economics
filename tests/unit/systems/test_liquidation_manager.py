import unittest
from unittest.mock import MagicMock, call
from typing import List

from simulation.systems.liquidation_manager import LiquidationManager
from modules.common.dtos import Claim
from simulation.firms import Firm
from simulation.dtos.api import SimulationState
from modules.system.api import IAssetRecoverySystem, IAgentRegistry
from modules.hr.api import IHRService
from modules.finance.api import ITaxService
from simulation.finance.api import ISettlementSystem

class TestLiquidationManager(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock(spec=ISettlementSystem)
        self.mock_hr = MagicMock(spec=IHRService)
        self.mock_tax = MagicMock(spec=ITaxService)
        self.mock_registry = MagicMock(spec=IAgentRegistry)
        self.mock_public = MagicMock(spec=IAssetRecoverySystem)

        self.manager = LiquidationManager(
            self.mock_settlement,
            self.mock_hr,
            self.mock_tax,
            self.mock_registry,
            self.mock_public
        )

        self.firm = MagicMock()
        self.firm.id = 1
        self.firm.finance.balance = 1000.0
        self.firm.total_shares = 1000.0
        self.firm.treasury_shares = 0.0
        self.firm.total_debt = 0.0
        # Mock last_prices and inventory for asset liquidation check
        self.firm.last_prices = {}
        self.firm.inventory = {}
        self.firm.config = MagicMock()

        self.state = MagicMock(spec=SimulationState)
        self.state.time = 100
        # For shareholder iteration in tier 5
        self.state.households = []
        self.state.government = None

    def test_initiate_liquidation_orchestration(self):
        # Setup Claims returned by services
        claim_hr = Claim(creditor_id=101, amount=100.0, tier=1, description="Wage")
        claim_tax = Claim(creditor_id="gov", amount=50.0, tier=3, description="Tax")

        self.mock_hr.calculate_liquidation_employee_claims.return_value = [claim_hr]
        self.mock_tax.calculate_liquidation_tax_claims.return_value = [claim_tax]

        # Mock Registry resolution
        agent_101 = MagicMock()
        agent_101.id = 101
        agent_gov = MagicMock()
        agent_gov.id = "gov"

        self.mock_registry.get_agent.side_effect = lambda x: {101: agent_101, "gov": agent_gov}.get(x)
        self.mock_settlement.transfer.return_value = True

        # Run
        self.manager.initiate_liquidation(self.firm, self.state)

        # Verify Services Called
        self.mock_hr.calculate_liquidation_employee_claims.assert_called_once_with(self.firm, 100)
        self.mock_tax.calculate_liquidation_tax_claims.assert_called_once_with(self.firm)

        # Verify Transfers
        # Expect transfers for both claims
        self.mock_settlement.transfer.assert_has_calls([
            call(self.firm, agent_101, 100.0, "Liquidation Payout: Wage"),
            call(self.firm, agent_gov, 50.0, "Liquidation Payout: Tax")
        ], any_order=True)

    def test_bank_claim_handling(self):
        self.mock_hr.calculate_liquidation_employee_claims.return_value = []
        self.mock_tax.calculate_liquidation_tax_claims.return_value = []

        # Setup Bank Debt
        self.firm.total_debt = 500.0
        bank = MagicMock()
        bank.id = "bank_1"
        self.firm.decision_engine.loan_market.bank = bank

        bank_agent = MagicMock()
        bank_agent.id = "bank_1"
        self.mock_registry.get_agent.return_value = bank_agent

        self.manager.initiate_liquidation(self.firm, self.state)

        # Check transfer to bank
        self.mock_settlement.transfer.assert_called_with(
            self.firm, bank_agent, 500.0, "Liquidation Payout: Secured Loan"
        )

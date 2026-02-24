import unittest
from unittest.mock import MagicMock, ANY
from modules.common.financial.dtos import Claim
from simulation.systems.liquidation_manager import LiquidationManager
from simulation.finance.api import ISettlementSystem
from modules.finance.api import ILiquidatable
from simulation.dtos.api import SimulationState

class TestLiquidationMath(unittest.TestCase):
    def setUp(self):
        self.mock_settlement_system = MagicMock(spec=ISettlementSystem)
        self.mock_hr_service = MagicMock()
        self.mock_tax_service = MagicMock()
        self.mock_agent_registry = MagicMock()
        self.mock_shareholder_registry = MagicMock()

        self.manager = LiquidationManager(
            settlement_system=self.mock_settlement_system,
            hr_service=self.mock_hr_service,
            tax_service=self.mock_tax_service,
            agent_registry=self.mock_agent_registry,
            shareholder_registry=self.mock_shareholder_registry
        )

    def test_liquidation_dust_distribution(self):
        """
        Verify that pro-rata distribution handles remainders correctly (zero-sum).
        Scenario: 100 pennies available, 3 claims of 50 pennies each (Total 150).
        Factor: 100/150 = 0.666...
        Expected payments: 33, 33, 34 (Total 100).
        """
        # Mock dependencies
        mock_agent = MagicMock(spec=ILiquidatable)
        mock_agent.id = 1

        mock_state = MagicMock(spec=SimulationState)
        mock_state.time = 100
        mock_state.transactions = [] # Mock list for appending transactions

        # Mock claims
        claims = [
            Claim(creditor_id=101, amount_pennies=50, tier=1, description="Claim 1"),
            Claim(creditor_id=102, amount_pennies=50, tier=1, description="Claim 2"),
            Claim(creditor_id=103, amount_pennies=50, tier=1, description="Claim 3"),
        ]

        # Mock get_agent for creditors
        def get_agent_side_effect(agent_id):
            mock_creditor = MagicMock()
            mock_creditor.id = agent_id
            return mock_creditor

        self.mock_agent_registry.get_agent.side_effect = get_agent_side_effect

        # Mock settlement transfer success
        self.mock_settlement_system.transfer.return_value = True

        # Execute waterfall directly
        available_cash = 100
        self.manager.execute_waterfall(mock_agent, claims, available_cash, mock_state)

        # Verify total payments
        # We need to capture the amount passed to settlement_system.transfer
        # call_args_list items are (args, kwargs)
        # transfer(agent, creditor, amount, memo, currency)

        total_paid = 0
        payments = []
        for call in self.mock_settlement_system.transfer.call_args_list:
            args, _ = call
            amount = args[2] # 3rd argument is amount
            total_paid += amount
            payments.append(amount)

        print(f"DEBUG: Payments made: {payments}")
        print(f"DEBUG: Total paid: {total_paid}")

        # Assert zero-sum
        self.assertEqual(total_paid, available_cash, f"Total paid {total_paid} does not match available cash {available_cash}. Leakage detected.")

        # Specific check for distribution logic (optional, but good to verify implementation detail)
        # With standard dust distribution, we expect [33, 33, 34] or similar depending on order
        self.assertIn(33, payments)
        self.assertIn(34, payments)

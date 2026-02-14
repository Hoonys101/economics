import pytest
from unittest.mock import MagicMock, create_autospec, patch
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.system import FinanceSystem
from simulation.finance.api import IFinancialAgent
from modules.system.api import DEFAULT_CURRENCY

class TestSettlementIntegrity:

    @pytest.fixture
    def settlement_system(self):
        return SettlementSystem()

    @pytest.fixture
    def finance_system(self, settlement_system):
        gov = MagicMock(spec=IFinancialAgent)
        gov.id = 1
        gov.total_debt = 5000 # Default debt
        gov.sensory_data = MagicMock()
        gov.sensory_data.current_gdp = 10000

        cb = MagicMock(spec=IFinancialAgent)
        cb.id = 2
        bank = MagicMock(spec=IFinancialAgent)
        bank.id = 3
        # Mocking bank methods needed for FinanceSystem
        bank.base_rate = 0.03

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: default

        return FinanceSystem(
            government=gov,
            central_bank=cb,
            bank=bank,
            config_module=config,
            settlement_system=settlement_system
        )

    def test_transfer_float_raises_error(self, settlement_system):
        """Test that passing a float to transfer raises TypeError."""
        sender = MagicMock(spec=IFinancialAgent)
        sender.id = 10
        receiver = MagicMock(spec=IFinancialAgent)
        receiver.id = 11

        with pytest.raises(TypeError, match="Settlement integrity violation"):
            settlement_system.transfer(
                debit_agent=sender,
                credit_agent=receiver,
                amount=100.0, # Float!
                memo="test_float_transfer"
            )

    def test_create_and_transfer_float_raises_error(self, settlement_system):
        """Test that passing a float to create_and_transfer raises TypeError."""
        source = MagicMock(spec=IFinancialAgent)
        source.id = 1
        dest = MagicMock(spec=IFinancialAgent)
        dest.id = 10

        with pytest.raises(TypeError, match="Settlement integrity violation"):
            settlement_system.create_and_transfer(
                source_authority=source,
                destination=dest,
                amount=50.5, # Float!
                reason="test_float_mint",
                tick=1
            )

    def test_issue_treasury_bonds_float_leak(self, finance_system, settlement_system):
        """
        Test that issue_treasury_bonds fails if amount is float.
        Currently (before fix) it casts to int, masking the error.
        After fix, it should pass float to settlement which raises TypeError.
        """
        # Mock bank reserves in ledger to allow purchase
        finance_system.ledger.banks[finance_system.bank.id].reserves[DEFAULT_CURRENCY] = 1000

        # Patch _sync_ledger_balances to prevent overwriting reserves with 0 (since settlement system has no registry)
        with patch.object(finance_system, '_sync_ledger_balances'):
            # We pass a float amount.
            # Before fix: int(100.5) -> 100, transfer succeeds.
            # After fix: 100.5 passed to transfer -> TypeError.

            with pytest.raises(TypeError, match="Settlement integrity violation"):
                finance_system.issue_treasury_bonds(
                    amount=100.5,
                    current_tick=1
                )

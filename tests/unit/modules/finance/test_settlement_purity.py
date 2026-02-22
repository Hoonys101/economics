import pytest
from unittest.mock import MagicMock, create_autospec
from typing import cast

from modules.finance.api import IMonetaryAuthority, ISettlementSystem, IConfig, IBank, IGovernmentFinance
from modules.finance.system import FinanceSystem
from simulation.systems.settlement_system import SettlementSystem
from modules.simulation.api import AgentID

class TestSettlementPurity:
    """
    Verifies that SettlementSystem adheres to Protocol Purity rules
    and FinanceSystem uses the correct interfaces.
    """

    def test_settlement_system_implements_monetary_authority(self):
        """
        Verify that SettlementSystem implements the IMonetaryAuthority protocol.
        This includes the newly added register_account/deregister_account methods.
        """
        # Create a real instance (dependencies mocked/stubbed as needed)
        # SettlementSystem only needs logger and bank (optional)
        settlement_sys = SettlementSystem()

        # Check protocol compliance
        assert isinstance(settlement_sys, IMonetaryAuthority), \
            "SettlementSystem must implement IMonetaryAuthority protocol"

    def test_finance_system_uses_monetary_authority(self):
        """
        Verify that FinanceSystem accepts an IMonetaryAuthority mock
        and calls strict methods on it.
        """
        # Mocks for FinanceSystem dependencies
        mock_gov = MagicMock(spec=IGovernmentFinance)
        mock_gov.id = 1
        mock_cb = MagicMock() # CentralBank is a class forward ref, tricky to mock spec strict without import
        mock_bank = MagicMock(spec=IBank)
        mock_bank.id = 2
        mock_bank.base_rate = 0.05
        mock_config = MagicMock(spec=IConfig)

        # Strict Mock for Settlement System
        # We use create_autospec to ensure it follows the Protocol
        mock_settlement = create_autospec(IMonetaryAuthority, instance=True)

        # Instantiate FinanceSystem
        fs = FinanceSystem(
            government=mock_gov,
            central_bank=mock_cb,
            bank=mock_bank,
            config_module=mock_config,
            settlement_system=mock_settlement
        )

        # Trigger a method that uses register_account
        # process_loan_application calls register_account

        borrower_id = 100
        amount = 5000
        profile = {"preferred_lender_id": mock_bank.id}

        # Mock internal engines to bypass logic if needed, or rely on defaults
        # To reach register_account, we need successful loan booking
        # Easier path: mock the engines directly on the instance

        fs.loan_risk_engine = MagicMock()
        decision = MagicMock()
        decision.is_approved = True
        fs.loan_risk_engine.assess.return_value = decision

        fs.loan_booking_engine = MagicMock()
        result = MagicMock()

        # Mock generated transactions to simulate loan creation
        tx = MagicMock()
        tx.item_id = "credit_creation_LOAN_1"
        result.generated_transactions = [tx]

        # Mock ledger update
        mock_loan_state = MagicMock()
        mock_loan_state.loan_id = "LOAN_1"
        mock_loan_state.borrower_id = borrower_id

        # We need to setup the ledger state so it finds the loan
        fs.ledger = MagicMock()
        fs.ledger.banks = {
            mock_bank.id: MagicMock()
        }
        fs.ledger.banks[mock_bank.id].loans = {"LOAN_1": mock_loan_state}

        # Mock bank_registry to return the loan (Since process_loan_application queries registry)
        fs.bank_registry = MagicMock()
        fs.bank_registry.get_loan.return_value = mock_loan_state
        # Also need get_all_banks for fallback logic if needed, but lender_id is in profile/app
        # But wait, app_dto.lender_id is set from profile.
        # process_loan_application uses app_dto.lender_id.

        fs.loan_booking_engine.grant_loan.return_value = result

        # Execute
        fs.process_loan_application(borrower_id, amount, profile, current_tick=10)

        # Verify register_account was called
        mock_settlement.register_account.assert_called_with(mock_bank.id, borrower_id)

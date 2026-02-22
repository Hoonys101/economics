import pytest
from modules.finance.registry.bank_registry import BankRegistry
from modules.finance.engine_api import BankStateDTO, DepositStateDTO, LoanStateDTO
from modules.system.api import DEFAULT_CURRENCY

class TestBankRegistry:
    def test_initialization_empty(self):
        registry = BankRegistry()
        assert registry.banks_dict == {}
        assert registry.get_all_banks() == []

    def test_initialization_with_data(self):
        bank_state = BankStateDTO(bank_id=1, base_rate=0.03)
        initial_banks = {
            1: bank_state
        }
        registry = BankRegistry(initial_banks=initial_banks)
        assert registry.banks_dict == initial_banks
        assert registry.get_bank(1) == initial_banks[1]

    def test_register_bank(self):
        registry = BankRegistry()
        bank_state = BankStateDTO(bank_id=1, base_rate=0.03)
        registry.register_bank(bank_state)

        assert registry.get_bank(1) == bank_state
        assert registry.banks_dict[1] == bank_state

    def test_get_deposit(self):
        registry = BankRegistry()
        deposit = DepositStateDTO(
            deposit_id="DEP_1_1",
            customer_id=2,
            balance_pennies=1000,
            interest_rate=0.0
        )
        bank_state = BankStateDTO(
            bank_id=1,
            base_rate=0.03,
            deposits={"DEP_1_1": deposit}
        )
        registry.register_bank(bank_state)

        fetched = registry.get_deposit(1, "DEP_1_1")
        assert fetched == deposit

        # Test missing bank or deposit
        assert registry.get_deposit(1, "DEP_MISSING") is None
        assert registry.get_deposit(999, "DEP_1_1") is None

    def test_get_loan(self):
        registry = BankRegistry()
        loan = LoanStateDTO(
            loan_id="LOAN_1",
            borrower_id=2,
            lender_id=1,
            principal_pennies=5000,
            remaining_principal_pennies=5000,
            interest_rate=0.05,
            origination_tick=0,
            due_tick=100
        )
        bank_state = BankStateDTO(
            bank_id=1,
            base_rate=0.03,
            loans={"LOAN_1": loan}
        )
        registry.register_bank(bank_state)

        fetched = registry.get_loan(1, "LOAN_1")
        assert fetched == loan

        assert registry.get_loan(1, "LOAN_MISSING") is None
        assert registry.get_loan(999, "LOAN_1") is None

    def test_shared_reference(self):
        """Verify that modifications to the shared dict are reflected."""
        registry = BankRegistry()
        shared_dict = registry.banks_dict

        bank_state = BankStateDTO(bank_id=1, base_rate=0.03)
        shared_dict[1] = bank_state

        assert registry.get_bank(1) == bank_state

import re

for test_file in ["tests/unit/markets/test_housing_transaction_handler.py", "tests/unit/systems/handlers/test_housing_handler.py"]:
    with open(test_file, "r") as f:
        content = f.read()

    # The reviewer mentioned:
    # "However, they failed to update the test mocks in test_housing_transaction_handler.py and test_housing_handler.py (where context.bank.grant_loan still returns a dictionary instead of a LoanDTO)."
    # Wait, the output I just showed has `loan_dto = MagicMock(); loan_dto.loan_id = "loan_123"`.
    # That IS an object, not a dictionary!
    # Ah, let me check `tests/unit/systems/handlers/test_housing_handler.py`

    print(f"File: {test_file}")

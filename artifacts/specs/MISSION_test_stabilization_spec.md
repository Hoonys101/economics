# Design Spec: Test Suite Stabilization (Protocol Alignment)

## 1. Introduction

- **Purpose**: To resolve critical regression failures in the integration test suite caused by the recent hardening of the `SettlementSystem` and `TaxService`. These systems now strictly enforce `runtime_checkable` Protocols (`ITaxableHousehold`, `ICentralBank`, `IFinancialEntity`) using `isinstance()` checks, causing legacy mocks to fail or be silently ignored.
- **Scope**:
  - `tests/integration/test_government_integration.py`
  - `tests/unit/test_tax_collection.py`
  - `tests/integration/test_omo_system.py`
  - `tests/unit/systems/test_settlement_security.py`
  - `tests/integration/test_government_refactor_behavior.py`
- **Goal**: Restore 100% pass rate for the identified tests by implementing Protocol-compliant Mock classes.

## 2. Problem Analysis

### 2.1. The "Silent Skip" Pattern (TaxService)
The `TaxService.collect_wealth_tax` method iterates through a list of agents:
```python
for agent in agents:
    if isinstance(agent, ITaxableHousehold):
        # ... calculate and collect tax
```
**Current State**: Tests use `MagicMock()`. `isinstance(MagicMock(), ITaxableHousehold)` returns `False`.
**Result**: The loop finishes without processing any agents. Assertions for tax collection fail (Actual: 0, Expected: >0).

### 2.2. The "Minting Denial" Pattern (SettlementSystem)
The `SettlementSystem.create_and_transfer` method (used for minting) enforces:
```python
if isinstance(source_authority, ICentralBank):
    # Allow minting (no balance check)
else:
    # Require funds (standard transfer)
```
**Current State**: Tests use `OMOTestAgent` or `StrictMockBank` which do not implement `ICentralBank`.
**Result**: The system treats the minting attempt as a standard transfer. Since the mock CB starts with 0 funds, it raises `InsufficientFundsError`.

## 3. Implementation Plan

### 3.1. Shared Mock Definitions (To be implemented locally in test files)

To avoid creating a shared test utility dependency hell, we will define lightweight, concrete mock classes within the test files (or a local helper if they share the exact directory).

#### **MockTaxableHousehold**
*Required for: `test_government_integration.py`, `test_government_refactor_behavior.py`*

```python
from modules.government.api import ITaxableHousehold
from modules.finance.api import IFinancialEntity
from modules.system.api import DEFAULT_CURRENCY

class MockTaxableHousehold(ITaxableHousehold): # Inherits Protocol for explicit typing
    def __init__(self, id, assets=0, is_employed=True):
        self.id = id
        self.is_active = True
        self.is_employed = is_employed
        self.needs = {}
        self._balance = int(assets) # Pennies

    @property
    def balance_pennies(self) -> int:
        return self._balance

    def deposit(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            self._balance += amount_pennies

    def withdraw(self, amount_pennies: int, currency = DEFAULT_CURRENCY) -> None:
        if currency == DEFAULT_CURRENCY:
            if self._balance >= amount_pennies:
                self._balance -= amount_pennies
            else:
                raise Exception("Insufficient funds")

    # Legacy Compatibility
    def get_balance(self, currency=DEFAULT_CURRENCY):
        return self._balance

    def get_assets_by_currency(self):
        return {DEFAULT_CURRENCY: self._balance}
```

#### **MockCentralBank**
*Required for: `test_omo_system.py`, `test_settlement_security.py`*

```python
from modules.finance.api import ICentralBank, IFinancialEntity

class MockCentralBank(ICentralBank):
    def __init__(self, id):
        self.id = id
        self._balance = 0

    @property
    def balance_pennies(self) -> int:
        return self._balance

    def deposit(self, amount: int, currency="USD"):
        self._balance += amount

    def withdraw(self, amount: int, currency="USD"):
        self._balance -= amount # Allow negative for tracking (or no-op for minting logic)

    def _deposit(self, amount, currency="USD"): self.deposit(amount, currency)
    def _withdraw(self, amount, currency="USD"): self.withdraw(amount, currency)

    def get_balance(self, currency="USD"): return self._balance
    def get_assets_by_currency(self): return {"USD": self._balance}
    def get_total_deposits(self): return 0

    # IMonetaryOperations
    def execute_open_market_operation(self, instruction): return []

    # ICentralBank specific
    def process_omo_settlement(self, transaction): pass
    
    # ISettlementSystem specific (if needed by inheritance)
    def transfer(self, *args, **kwargs): pass
    def register_account(self, *args, **kwargs): pass
    def deregister_account(self, *args, **kwargs): pass
    def remove_agent_from_all_accounts(self, *args, **kwargs): pass
    def get_account_holders(self, *args, **kwargs): return []
    def get_agent_banks(self, *args, **kwargs): return []
    
    # IBank specific
    base_rate = 0.05
    def get_customer_balance(self, agent_id): return 0
    def get_debt_status(self, borrower_id): return None
    def terminate_loan(self, loan_id): return None
    def withdraw_for_customer(self, agent_id, amount): return False
    def close_account(self, agent_id): return 0
    def repay_loan(self, loan_id, amount): return amount
    def receive_repayment(self, borrower_id, amount): return amount
    
    @property
    def total_wealth(self): return self._balance
    def get_liquid_assets(self, currency="USD"): return float(self._balance)
    def get_total_debt(self): return 0.0

```

### 3.2. File-Specific Refactoring Instructions

#### 1. `tests/integration/test_government_integration.py`
- **Action**: Remove `rich_agent = MagicMock()` and `poor_agent = MagicMock()`.
- **Implementation**: Instantiate `MockTaxableHousehold(id=101, assets=2000000)` and `MockTaxableHousehold(id=102, assets=100, is_employed=False)`.
- **Note**: Ensure `settlement_system.transfer` asserts check the *properties* of these objects, not `call_args` on the agent itself (since it's no longer a mock).

#### 2. `tests/unit/test_tax_collection.py`
- **Action**: Modify the existing `MockAgent` class.
- **Implementation**: Add `balance_pennies` property. Inherit from `ITaxableHousehold` (optional, but good for clarity). Ensure `is_active`, `is_employed`, `needs` are set in `__init__`.

#### 3. `tests/integration/test_omo_system.py`
- **Action**: Update `OMOTestAgent` class.
- **Implementation**:
  - Add `ICentralBank` to inheritance list (if importing possible).
  - Implement `process_omo_settlement(self, transaction) -> None`.
  - Ensure `id` matches `ID_CENTRAL_BANK` when used as CB.
  - **Constraint**: `SettlementSystem` checks `isinstance(agent, ICentralBank)`. We must ensure `OMOTestAgent` registers as such. If direct inheritance is tricky due to circular imports, use `abc.ABCMeta` register or just simple inheritance if `modules.finance.api` is available.

#### 4. `tests/unit/systems/test_settlement_security.py`
- **Action**: Create `StrictMockCentralBank` class.
- **Implementation**: Must implement `ICentralBank` protocol methods. Use this class for the `central_bank` mock in `test_mint_and_distribute_security`.

#### 5. `tests/integration/test_government_refactor_behavior.py`
- **Action**: In `test_social_policy_execution`, replace `rich_agent = MagicMock()` with `MockTaxableHousehold`.

## 4. Verification Plan

### 4.1. Pre-Implementation Audit
- Check `modules/finance/api.py` to confirm `ITaxableHousehold` and `ICentralBank` definitions are `@runtime_checkable`.

### 4.2. Test Execution Strategy
Run the affected tests specifically:
```bash
pytest tests/integration/test_government_integration.py tests/unit/test_tax_collection.py tests/integration/test_omo_system.py tests/unit/systems/test_settlement_security.py tests/integration/test_government_refactor_behavior.py
```

### 4.3. Success Criteria
- **Pass Rate**: 100% (Green).
- **Log Validation**:
  - For Tax tests: Verify logs show "Tax collected" (not 0).
  - For OMO tests: Verify logs show "MINT_AND_TRANSFER" success.

## 5. Risk Assessment

- **Circular Imports**: Importing `ITaxableHousehold` in integration tests might trigger a chain loading `Government` -> `PolicyEngine` -> ...
  - *Mitigation*: Import Protocols from `api.py` files only. Do not import implementation classes.
- **Over-Mocking**: If we mock too much, we mask the actual behavior.
  - *Mitigation*: The proposed Mock classes are "Fakes" (lightweight implementations) rather than Mocks, which is safer for Protocol testing.

## 6. Mandatory Reporting
- Create `communications/insights/test-stabilization-spec.md` immediately.
- Document the "Silent Skip" risk in the report to warn future developers about `isinstance` checks on `MagicMock`.

---
*End of Spec*
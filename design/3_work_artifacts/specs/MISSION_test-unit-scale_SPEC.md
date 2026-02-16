modules/finance/api.py
```python
from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union
from dataclasses import dataclass
import abc
from uuid import UUID

# Explicit definition for clarity in Spec, replacing imports
class MoneyDTO(TypedDict):
    """
    Standard Data Transfer Object for monetary values.
    MUST use integer pennies to prevent floating point drift.
    """
    amount_pennies: int
    currency: str

class MultiCurrencyWalletDTO(TypedDict):
    """
    DTO for transferring wallet state.
    """
    balances: Dict[str, int] # Currency Code -> Pennies

# Re-exporting basic types for context
AgentID = Union[str, int]
CurrencyCode = str
DEFAULT_CURRENCY = "USD"

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.models import Transaction, Order
    from modules.common.dtos import Claim

# --- Core Financial Protocols (Strict Integer Enforcement) ---

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Enforces the 'Penny Standard' (Integer arithmetic).
    """
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        ...

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the entity's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws funds from the entity's wallet.
        Raises InsufficientFundsError if balance is too low.
        """
        ...

@runtime_checkable
class IFinancialFirm(IFinancialEntity, Protocol):
    """
    Interface for a Firm entity used in financial analysis.
    Ensures strict typing for solvency checks and financial reporting.
    """
    id: AgentID

    @property
    def capital_stock_pennies(self) -> int:
        """The capital stock value in pennies."""
        ...

    @property
    def inventory_value_pennies(self) -> int:
        """The total value of inventory in pennies."""
        ...

    @property
    def total_debt_pennies(self) -> int:
        """The total outstanding debt in pennies."""
        ...

@runtime_checkable
class ISettlementSystem(Protocol):
    """
    Interface for the centralized settlement system.
    This is the Single Source of Truth for financial transactions.
    """

    def transfer(
        self,
        debit_agent: IFinancialEntity, # Must adhere to Entity protocol
        credit_agent: IFinancialEntity,
        amount: int, # STRICTLY INT
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[Any]: # Returns Transaction
        """Executes an immediate, single transfer. Returns transaction or None."""
        ...

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        Returns Integer Pennies.
        """
        ...

@runtime_checkable
class IBank(IFinancialEntity, Protocol):
    """
    Interface for commercial and central banks.
    """
    
    @abc.abstractmethod
    def get_customer_balance(self, agent_id: AgentID) -> int:
        """
        Retrieves the current balance for a given CUSTOMER account (deposit).
        Returns Integer Pennies.
        """
        ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: int) -> bool:
        """
        Repays a portion or the full amount of a specific loan.
        Amount is Integer Pennies.
        """
        ...

# --- Exceptions ---

class InsufficientFundsError(Exception):
    """
    Raised when an operation cannot be completed due to lack of funds.
    Attributes should now reflect penny amounts.
    """
    def __init__(self, message: str, required: Optional[MoneyDTO] = None, available: Optional[MoneyDTO] = None):
        self.required = required
        self.available = available
        super().__init__(message)
```

design/3_work_artifacts/specs/test_unit_standardization_spec.md
```markdown
# Spec: Test Unit Scale Standardization (Dollar -> Penny)

## 1. Context & Objective
The current codebase exhibits a "Unit Scale Mismatch" (TD-TEST-UNIT-SCALE). Integration tests (`test_fiscal_integrity.py`) and Unit tests (`test_firms.py`) operate on Floating Point Dollars, while the Core Architecture (`api.py`, `SettlementSystem`) enforces Integer Pennies. This creates "Mock Drift," where tests pass against invalid mocks but the system would fail in production.

**Goal**: Refactor the test suite to strictly adhere to the `int` (Penny) standard using the conversion factor `1.00 USD = 100 Pennies`.

## 2. Technical Strategy

### 2.1. The "Penny Standard" Scale
- **Conversion Factor**: `100`
- **Input (Test)**: `$10.50` -> `1050` pennies.
- **Assertion**: `assert balance == 1050` (NOT `10.5`).

### 2.2. New Test Utility: `tests/utils/currency.py`
To maintain readability without magic numbers, we will introduce helper functions.

```python
# tests/utils/currency.py
from typing import Union

SCALE = 100

def P(amount_dollars: Union[int, float]) -> int:
    """
    Converts a Dollar amount (float/int) to Pennies (int).
    Usage: P(10.50) -> 1050
    """
    return int(round(amount_dollars * SCALE))

def to_dollars(amount_pennies: int) -> float:
    """
    Converts Pennies (int) to Dollars (float) for display/logging only.
    Usage: to_dollars(1050) -> 10.5
    """
    return float(amount_pennies) / SCALE
```

### 2.3. Mock Hygiene Enforcements
All Mocks representing Financial Systems MUST use `spec=Protocol` to enforce type signatures.

```python
# BAD
settlement_system = MagicMock()
settlement_system.get_balance.return_value = 5000.0  # PASSES silently, fails runtime

# GOOD
settlement_system = MagicMock(spec=ISettlementSystem)
settlement_system.get_balance.return_value = 5000.0  # FAIL: Mock will strictly adhere to signature if autospec used
# Better: explicitly set return value to int
settlement_system.get_balance.return_value = 500000
```

## 3. Detailed Migration Steps

### Phase 1: Utility & Infrastructure
1. Create `tests/utils/currency.py`.
2. Update `tests/conftest.py` to import `P` helper if needed globally, or just import in test files.

### Phase 2: `tests/integration/test_fiscal_integrity.py` Refactor
This file is the primary offender.

- **Config Mocking**: 
  - `INFRASTRUCTURE_INVESTMENT_COST = 5000.0` -> `P(5000)` (500,000)
  - `EDUCATION_COST_PER_LEVEL = {1: 500}` -> `{1: P(500)}`
  - `GOODS_INITIAL_PRICE = {"basic_food": 5.0}` -> `{"basic_food": P(5.0)}`
- **Government Initialization**:
  - `initial_assets=1000.0` -> `initial_assets=P(1000)`
- **Assertions**:
  - `assert ... == 5000.0` -> `assert ... == P(5000)`
- **Bank Mocks**:
  - Ensure `bank.total_wealth` returns `int`.

### Phase 3: `tests/unit/test_firms.py` Refactor
Fix the Hybrid/Partial state.

- **Fix `test_book_value_no_liabilities`**:
  - Existing: `firm.wallet.add(1000)` (1000 pennies = $10.00).
  - Existing Assert: `assert result == 10.0` (Book Value is logical Dollars).
  - **Decision**: Keep Book Value logic as *Float (Dollars)* if strictly display-oriented, OR convert to *Pennies (Int)*. 
  - **Standard**: `IFinancialFirm` properties are `_pennies`. `get_book_value_per_share()` is a calculated metric. Ideally, it should return a float (Currency Unit), but the inputs MUST be pennies.
  - **Fix**: Ensure `assets=0` in `create_firm` factory implies 0 pennies.
  - **Fix**: `firm.production_state.capital_stock = 100.0` -> `10000` (if $100).

## 4. Risk Analysis: Agent Decomposition Conflict
- **Risk**: `TD-STR-GOD-DECOMP` involves refactoring `Firm` attributes.
- **Conflict**: If we rename `firm.capital_stock` to `firm.capital_stock_pennies` in tests, we might break pending changes.
- **Mitigation**: 
  - Use `IFinancialFirm` protocol methods where possible. 
  - If direct attribute access is needed, prefer `firm.production_state.capital_stock_pennies` if it exists. 
  - If not, document the `float -> int` logic change clearly in `TECH_DEBT_LEDGER.md` under the decomposition task.

## 5. Verification Plan
1. **Run Tests**: `pytest tests/integration/test_fiscal_integrity.py tests/unit/test_firms.py`
2. **Type Check**: `mypy tests/integration/test_fiscal_integrity.py` (optional but recommended).

## 6. Mandatory Reporting
**[CRITICAL INSTRUCTION]**
Upon completion of the refactor, you must create a new file:
`communications/insights/test-unit-standardization-spec.md`

Content:
1. **Migration Statistics**: Number of files changed, number of lines affected.
2. **Mock Drift Findings**: List any mocks that were found violating strict `int` returns.
3. **Decomposition Notes**: Any friction encountered with `Firm` or `Household` structure.
4. **Test Output**: Copy-paste the passing `pytest` summary.

```

design/2_operations/ledgers/TECH_DEBT_LEDGER.md
```markdown
<!-- ADDITION TO THE EXISTING LEDGER - DO NOT REMOVE EXISTING CONTENT -->

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-TEST-UNIT-SCALE** | Testing | **Unit Scale Ambiguity**: Mismatch between "Dollars" (Float) in tests and "Pennies" (Int) in Engines. | **High**: Financial Logic. | **In Progress** |
```
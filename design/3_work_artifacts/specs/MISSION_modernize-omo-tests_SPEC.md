from modules.common.dtos import BaseDTO
from typing import Literal, TypedDict, Optional

class OMOInstructionDTO(BaseDTO):
    """
    Data Transfer Object for Open Market Operation instructions.
    Used by CentralBankSystem to execute monetary policy.
    """
    operation_type: Literal["purchase", "sale"]
    target_amount: int
    security_id: Optional[str]  # Defaults to government_bond if None

class OMOResultDTO(BaseDTO):
    """
    Result of an OMO execution.
    """
    orders_created: int
    total_quantity: int
    market_id: str

# Interface definition for the Settlement System (for reference/mocking)
class SettlementSystemProtocol(TypedDict):
    """
    Protocol defining the expected interface for Settlement System.
    """
    def get_balance(self, agent_id: int, currency: str = "USD") -> int: ...
    def get_all_balances(self) -> dict[str, int]: ...
    def settle_atomic(self, debit_agent: object, credits: list[tuple], tick: int) -> bool: ...

# design/3_work_artifacts/specs/modernize_omo_tests_spec.md
# Spec: Modernize OMO & Settlement Tests (SSoT Alignment)

## 1. Introduction

- **Purpose**: Refactor `test_omo_system.py` and `test_atomic_settlement.py` to align with the SSoT (Single Source of Truth) architecture. State verification must move from `Agent.assets` to `SettlementSystem.get_balance()`.
- **Scope**:
    - `tests/integration/test_omo_system.py`
    - `tests/integration/test_atomic_settlement.py`
- **Goal**: Eliminate "Legacy Agent State Assertions" and enforce "Zero-Sum Integrity" in test verifications.

## 2. Technical Debt & Risk Analysis (Pre-Implementation)

### 2.1. Debt Ledger Analysis
- **Target Debt**: `TEST-001` (Legacy Agent State Access).
- **Resolution**: This spec explicitly resolves the violation where tests access private `agent.assets` instead of querying the authoritative ledger.
- **New Insight**: The current `MockAgent` duplicates state logic (local `assets` vs. System state). This duality is a source of drift.

### 2.2. Risks
- **Dependency Risk**: If `SettlementSystem` internally delegates to `Agent.get_balance()` without a central ledger, this refactor is purely cosmetic (API alignment) but doesn't fix the underlying architectural split.
- **Test Fragility**: Strict strict zero-sum checks might fail if there are hidden "sinks" or "sources" in the mock setup (e.g., float precision errors or implicit fees).

## 3. Detailed Design

### 3.1. Refactoring `test_omo_system.py`

#### A. `MockAgent` Update
- **Requirement**: `MockAgent` must adhere to `AgentProtocol` but should rely on `SettlementSystem` for truth where possible, or at least the *test* should ignore its internal state.
- **Change**: Rename to `OMOTestAgent`. Remove `total_wealth` property usage in assertions.

#### B. Setup Fixture (`omo_setup`)
- Ensure `SettlementSystem` is initialized with a reference to a `Ledger` (if applicable) or correctly wired to the agents.
- **Zero-Sum Baseline**: Calculate `initial_system_money` at the start of the test.

#### C. Test Logic Updates (Pseudo-code)

```python
def test_process_omo_purchase_transaction(omo_setup):
    cb_system, tx_manager, state, cb_agent, gov_agent, household = omo_setup
    
    # 1. Capture Pre-State via SSoT
    initial_hh_balance = settlement.get_balance(household.id)
    initial_gov_issued = gov_agent.total_money_issued # Ledger-specific metric, keep agent access if purely internal logic, OR move to CentralBank ledger check.
    initial_system_sum = sum_all_balances(settlement)

    # 2. Execute
    tx_manager.execute(state)

    # 3. Verify via SSoT
    expected_hh_balance = initial_hh_balance + 100
    assert settlement.get_balance(household.id) == expected_hh_balance
    
    # 4. Zero-Sum / Integrity Check
    # OMO purchase creates money (Minting), so total system money INCREASES.
    # We must verify the delta matches exactly.
    final_system_sum = sum_all_balances(settlement)
    assert final_system_sum == initial_system_sum + 100
```

### 3.2. Refactoring `test_atomic_settlement.py`

#### A. Assertions
- Replace `debit_agent.get_balance()` with `settlement.get_balance(debit_agent.id)`.

#### B. Rollback Verification
- Ensure that when `settle_atomic` returns `False`, the `SettlementSystem` reports the original balances.

## 4. Verification Plan

### 4.1. New Test Cases
- **`test_omo_integrity_zero_sum`**: A specific test ensuring that OMO operations strictly mint/burn the exact amount intended, with no leakage to other agents.

### 4.2. Impact on Existing Tests
- Existing tests will break immediately upon removing `assets` from `MockAgent` if the `SettlementSystem` mocks aren't updated.
- **Mitigation**: Update `MockAgent` to be a compliant `Protocol` implementation that `SettlementSystem` can interact with, even if the test assertions change.

### 4.3. Mandatory Reporting
- Execution of this spec **MUST** result in a report generated at `communications/insights/modernize-omo-tests.md`.
- The report must contain:
    - Diff of `pytest` output (Before vs. After).
    - Confirmation that `settlement.get_balance` is returning correct values.

## 5. Mocking Guide (Golden Data)

- **Do NOT** use `MagicMock` for `SettlementSystem` return values in `test_atomic_settlement.py` if testing the system itself. Use the real class with mocked agents.
- **Agents**: Continue using `MockAgent` but strip it down to minimal `Protocol` requirements.

## 6. Implementation Steps

1.  **Create Insight File**: `communications/insights/modernize-omo-tests.md`.
2.  **Refactor `MockAgent`**: Add `get_balance` that queries internal state (temporary) or delegates.
3.  **Update `test_atomic_settlement.py`**: Switch assertions to `settlement.get_balance`.
4.  **Update `test_omo_system.py`**: Switch assertions and add `sum_all_balances` check.
5.  **Run Tests**: `pytest tests/integration/test_omo_system.py tests/integration/test_atomic_settlement.py`.
6.  **Log Results**: Paste output to insight file.
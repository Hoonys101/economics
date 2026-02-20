# modules/finance/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional, List, Any, Dict

from modules.simulation.api import AgentID

# ==============================================================================
# DTOs (Data Transfer Objects)
# ==============================================================================

@dataclass(frozen=True)
class FinanceConfigDTO:
    """
    Configuration DTO for FinanceEngine.
    Resolves TD-CONF-MAGIC-NUMBERS by encapsulating hardcoded constants.
    """
    days_per_year: int = 365
    tax_payment_period: int = 7
    bankruptcy_threshold: float = 0.0
    
    # Debt & Loan Constraints
    max_leverage_ratio: float = 1.8  # Legacy magic number for debt ceiling
    default_loan_interest_rate: float = 0.05
    min_loan_amount: float = 1000.0
    
    # AI/Behavioral weights
    z_score_bankruptcy_threshold: float = 1.81
    insolvency_buffer: float = 0.10  # 10% buffer before panic

@dataclass
class LoanInfoDTO:
    """
    Standardized Data Transfer Object for Loan Information.
    """
    loan_id: str
    borrower_id: int
    original_amount: float
    outstanding_balance: float
    interest_rate: float
    origination_tick: int
    due_tick: int
    lender_id: Optional[int] = None
    term_ticks: int = 30

@dataclass
class MortgageApplicationDTO:
    """
    DTO for mortgage applications passing through the Loan Market.
    """
    applicant_id: AgentID
    property_id: str
    property_value: float
    requested_principal: float
    down_payment: float
    applicant_monthly_income: float
    existing_monthly_debt_payments: float
    loan_term: int = 360  # ticks

# ==============================================================================
# Protocols (Interfaces)
# ==============================================================================

@runtime_checkable
class ILoanMarket(Protocol):
    """
    Protocol describing the Loan Market capabilities required by Firms/Households.
    Resolves TD-ARCH-LOAN-CIRCULAR by decoupling concrete implementation.
    """
    
    id: str

    def get_interest_rate(self) -> float:
        """Returns the current market base interest rate."""
        ...

    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """Checks if an application meets market criteria (LTV, DTI)."""
        ...

    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> Optional[str]:
        """Stages an application and returns a temporary ID if successful."""
        ...

    def place_order(self, order: Any, current_tick: int) -> List[Any]:
        """
        Legacy support for order-based interactions (Transactions).
        'order' should be compatible with simulation.models.Order
        """
        ...

@runtime_checkable
class IFinancialAgent(Protocol):
    """
    Protocol for agents that participate in financial transactions.
    """
    id: AgentID
    
    def get_balance(self) -> float:
        ...
    
    def deposit(self, amount: float) -> None:
        ...
        
    def withdraw(self, amount: float) -> bool:
        ...

```

# design/3_work_artifacts/specs/MISSION_firm_decoupling_spec.md
```markdown
# Spec: Firm Architecture Decoupling & Config Hardening

## 1. Introduction

- **Purpose**: To decouple `Firm` from the concrete `LoanMarket` implementation and remove hardcoded constants from `FinanceEngine`. This refactoring targets **TD-CONF-MAGIC-NUMBERS** and **TD-ARCH-LOAN-CIRCULAR**.
- **Scope**:
  - `modules/finance/api.py`: Definition of `FinanceConfigDTO` and `ILoanMarket`.
  - `simulation/firms/firm.py`: Injection of dependencies.
  - `modules/finance/finance_engine.py`: Adoption of Config DTO.
  - `simulation/loan_market.py`: Protocol adherence verification.
- **Goals**:
  - Eliminate circular dependencies between Agents and Markets.
  - Centralize financial configuration for easier tuning and experiments.
  - Maintain 100% test pass rate.

## 2. Architecture & Design

### 2.1. Dependency Injection Strategy

Currently, `Firm` instantiates or accesses `LoanMarket` directly, often leading to import cycles. The new design uses constructor injection.

**Before:**
```python
class Firm(Agent):
    def __init__(self, ...):
        self.loan_market = LoanMarket(...) # Hard coupling
```

**After (Plan):**
```python
class Firm(Agent):
    def __init__(self, ..., loan_market: ILoanMarket, finance_config: FinanceConfigDTO):
        self.loan_market = loan_market
        self.finance_engine = FinanceEngine(..., config=finance_config)
```

### 2.2. Configuration Hardening (FinanceConfigDTO)

`FinanceEngine` currently contains magic numbers like `1.8` (Z-Score threshold) or `365` (Days/Year). These will be moved to `FinanceConfigDTO`.

- **Location**: `modules/finance/api.py`
- **Fields**: See API definition.

### 2.3. Protocol Definition (ILoanMarket)

To break the cycle, `Firm` will depend on `ILoanMarket` (Protocol) defined in `modules/finance/api.py`, not the concrete `LoanMarket` class in `simulation/loan_market.py`.

## 3. Implementation Steps (Pseudo-code)

### Step 1: Define API Artifacts
- Create `modules/finance/api.py` (as defined in output).

### Step 2: Refactor `FinanceEngine`
- Modify `__init__` to accept `config: FinanceConfigDTO`.
- Replace all magic numbers with `self.config.<field>`.

```python
# modules/finance/finance_engine.py

class FinanceEngine:
    def __init__(self, agent_id, ..., config: FinanceConfigDTO):
        self.config = config

    def check_health(self):
        # OLD: if z_score < 1.81:
        if z_score < self.config.z_score_bankruptcy_threshold:
            ...
```

### Step 3: Refactor `Firm`
- Update `Firm.__init__` signature to accept `loan_market: ILoanMarket` and `finance_config: FinanceConfigDTO`.
- Pass `finance_config` to `FinanceEngine`.

### Step 4: Update Factory/Simulation
- In `simulation/simulation.py` or `agent_factory.py`, when creating Firms:
  1. Instantiate `FinanceConfigDTO` (loading values from `economy_params.yaml` or using defaults).
  2. Pass the `LoanMarket` instance (which implements `ILoanMarket`) to the Firm.

## 4. Verification & Testing

### 4.1. Protocol Compliance Test
Create `tests/finance/test_protocol_compliance.py`:
```python
def test_loan_market_implements_protocol():
    from simulation.loan_market import LoanMarket
    from modules.finance.api import ILoanMarket
    
    # Mock dependencies for instantiation
    market = LoanMarket(..., bank=MockBank(), ...) 
    assert isinstance(market, ILoanMarket)
```

### 4.2. Impact on Existing Tests
- **`tests/test_firm.py`**: Will fail due to `__init__` signature change. Must update fixtures to inject `Mock(spec=ILoanMarket)` and `FinanceConfigDTO()`.
- **`tests/test_finance_engine.py`**: Will fail. Update instantiation to provide config.

### 4.3. Golden Data
- Ensure `tests/conftest.py` fixtures for `firm` are updated to provide valid defaults for the new parameters, ensuring the "Golden Path" remains valid.

## 5. Risk Assessment

- **Circular Import**: `modules/finance/api.py` MUST NOT import `simulation.firms` or `simulation.loan_market`.
- **Legacy Order Support**: `ILoanMarket` includes `place_order` to support legacy logic in `Firm.update()`. This is a transitional bridge.
- **Config Drift**: If `economy_params.yaml` structure doesn't match `FinanceConfigDTO` structure exactly, the mapping logic in the Factory must be robust.

## 6. Mandatory Reporting

Insights and technical debt resolutions must be logged to `communications/insights/firm-decoupling-spec.md`.
```

# design/2_operations/ledgers/TECH_DEBT_LEDGER.md
```markdown
### ID: TD-CONF-MAGIC-NUMBERS
- **Title**: Magic Numbers in FinanceEngine
- **Status**: **IN PROGRESS** (Targeted by firm-decoupling-spec)
- **Description**: Hardcoded constants (365, 1.8) being moved to `FinanceConfigDTO`.

### ID: TD-ARCH-LOAN-CIRCULAR
- **Title**: Circular Dependency Firm <-> LoanMarket
- **Status**: **IN PROGRESS** (Targeted by firm-decoupling-spec)
- **Description**: Breaking cycle via `ILoanMarket` Protocol injection.
```

# CHANGELOG.md
```markdown
### Added
- `modules/finance/api.py`: Added `FinanceConfigDTO` and `ILoanMarket` protocol.

### Changed
- `Firm` architecture decoupled from concrete `LoanMarket`.
- `FinanceEngine` now uses injected configuration instead of hardcoded constants.
```

# task.md
```markdown
- [ ] Create `modules/finance/api.py` with `FinanceConfigDTO` and `ILoanMarket` <!-- id: 0 -->
- [ ] Refactor `FinanceEngine` to use `FinanceConfigDTO` <!-- id: 1 -->
- [ ] Refactor `Firm` to accept `ILoanMarket` via DI <!-- id: 2 -->
- [ ] Update `Simulation` initialization to pass `FinanceConfigDTO` <!-- id: 3 -->
- [ ] Verify `LoanMarket` implements `ILoanMarket` <!-- id: 4 -->
- [ ] Fix unit tests for `Firm` and `FinanceEngine` <!-- id: 5 -->
- [ ] Create insight report `communications/insights/firm-decoupling-spec.md` <!-- id: 6 -->
```

# PROJECT_STATUS.md
```markdown
### Phase 2: Refactoring & Architecture Hardening
- **Current Focus**: Decoupling Firm dependencies and hardening Financial configuration.
- **Active Mission**: `firm-decoupling-spec` (TD-CONF-MAGIC-NUMBERS, TD-ARCH-LOAN-CIRCULAR).
```
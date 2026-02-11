# Refactoring Plan: Stateless Finance Engines

## 1. Executive Summary
The current `Bank` and `FinanceSystem` classes have become "God Classes," violating the Single Responsibility Principle and creating a web of tight coupling and potential circular dependencies. This refactoring plan addresses this technical debt by introducing a stateless architecture.

The core of this redesign is to externalize all financial state into a central `FinancialLedgerDTO`. Business logic will be extracted from the monolithic classes and placed into small, pure, stateless **Finance Engines**. These engines will operate on the `FinancialLedgerDTO`, receiving it as input and returning a new, updated state along with a list of resultant `Transaction` objects. This approach enforces architectural purity, enhances testability, and breaks dangerous dependencies.

## 2. API Definitions (`modules/finance/engine_api.py`)

This file will contain the data contracts (DTOs) and the public interfaces for the new stateless engines.

```python
# modules/finance/engine_api.py

from typing import TypedDict, List, Dict, Optional, Protocol
from dataclasses import dataclass, field

from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.models import Transaction

# =================================================================
# 1. CORE STATE DTOs (The Financial Ledger)
# =================================================================

# Represents a single loan on the books
@dataclass
class LoanStateDTO:
    loan_id: str
    borrower_id: AgentID
    lender_id: AgentID # e.g., Bank ID
    principal: float
    remaining_principal: float
    interest_rate: float
    origination_tick: int
    due_tick: int
    is_defaulted: bool = False

# Represents a single deposit account
@dataclass
class DepositStateDTO:
    deposit_id: str
    customer_id: AgentID
    balance: float
    interest_rate: float
    currency: CurrencyCode = DEFAULT_CURRENCY

# Represents a government bond
@dataclass
class BondStateDTO:
    bond_id: str
    owner_id: AgentID # Who holds the bond (e.g., Bank, CentralBank)
    face_value: float
    yield_rate: float
    issue_tick: int
    maturity_tick: int

# State specific to the banking system
@dataclass
class BankStateDTO:
    bank_id: AgentID
    reserves: Dict[CurrencyCode, float] = field(default_factory=dict)
    base_rate: float = 0.03
    loans: Dict[str, LoanStateDTO] = field(default_factory=dict) # Key: loan_id
    deposits: Dict[str, DepositStateDTO] = field(default_factory=dict) # Key: deposit_id

# State specific to government treasury and debt
@dataclass
class TreasuryStateDTO:
    government_id: AgentID
    balance: Dict[CurrencyCode, float] = field(default_factory=dict)
    bonds: Dict[str, BondStateDTO] = field(default_factory=dict) # Key: bond_id

# The central, unified ledger for all financial state
@dataclass
class FinancialLedgerDTO:
    """The single source of truth for financial state in the simulation."""
    current_tick: int
    banks: Dict[AgentID, BankStateDTO] = field(default_factory=dict)
    treasury: TreasuryStateDTO = field(default_factory=dict)
    # Add other major financial entities here if needed (e.g., CentralBankState)

# =================================================================
# 2. INPUT/OUTPUT DTOs for Engines
# =================================================================

# Result from any engine operation
@dataclass
class EngineOutputDTO:
    updated_ledger: FinancialLedgerDTO
    generated_transactions: List[Transaction] = field(default_factory=list)

# Input for assessing a new loan application
@dataclass
class LoanApplicationDTO:
    borrower_id: AgentID
    amount: float
    # Borrower financial profile, credit score, etc.
    # To be defined, but let's assume it's a dict for now
    borrower_profile: Dict 

# Decision from the risk assessment engine
@dataclass
class LoanDecisionDTO:
    is_approved: bool
    interest_rate: float
    rejection_reason: Optional[str] = None

# Input for firm liquidation
@dataclass
class LiquidationRequestDTO:
    firm_id: AgentID
    inventory_value: float
    capital_value: float
    outstanding_debt: float # Total debt to be settled

# =================================================================
# 3. STATELESS ENGINE INTERFACES (Protocols)
# =================================================================

class ILoanRiskEngine(Protocol):
    """(Stateless) Assesses the risk of a loan application."""
    def assess(
        self,
        application: LoanApplicationDTO,
        ledger: FinancialLedgerDTO # For context (e.g., current base rates)
    ) -> LoanDecisionDTO:
        ...

class ILoanBookingEngine(Protocol):
    """(Stateless) Books a new loan onto the ledger if approved."""
    def grant_loan(
        self,
        application: LoanApplicationDTO,
        decision: LoanDecisionDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:
        ...

class ILiquidationEngine(Protocol):
    """(Stateless) Handles the bankruptcy and liquidation of a firm."""
    def liquidate(
        self,
        request: LiquidationRequestDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:
        """
        Settles debts, destroys value, and generates final transactions.
        """
        ...

class IInterestRateEngine(Protocol):
    """(Stateless) Adjusts interest rates based on economic indicators."""
    def update_rates(
        self,
        # Economic indicators (GDP, CPI, etc.) would be passed here
        economic_indicators: Dict,
        ledger: FinancialLedgerDTO
    ) -> FinancialLedgerDTO: # Returns only the updated ledger
        ...

class IDebtServicingEngine(Protocol):
    """(Stateless) Services all active loans and bonds for a single tick."""
    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO:
        ...

```

## 3. Specification: `design/3_work_artifacts/specs/finance_engine_refactor_spec.md`

# Spec: Stateless Finance Engine Refactoring

## 1. Logic Steps (Pseudo-code)

The new workflow follows a functional, stateless pattern orchestrated by a controller (e.g., the main `Simulation` class).

**Example: Granting a Loan**
```python
# 1. An agent (e.g., a Firm) requests a loan from the system.

# 2. The simulation controller gathers the required data.
ledger: FinancialLedgerDTO = get_current_financial_state()
application = LoanApplicationDTO(borrower_id=firm.id, amount=10000, profile=firm.get_profile())

# 3. The controller invokes the stateless LoanRiskEngine.
risk_engine = LoanRiskEngine() # Instantiated, has no state
decision = risk_engine.assess(application, ledger)

# 4. The controller checks the decision and invokes the LoanBookingEngine.
if decision.is_approved:
    booking_engine = LoanBookingEngine()
    engine_output = booking_engine.grant_loan(application, decision, ledger)
    
    # 5. The controller commits the results.
    commit_new_financial_state(engine_output.updated_ledger)
    commit_transactions(engine_output.generated_transactions)
else:
    # Handle rejection (e.g., notify agent).
    pass
```

## 2. Exception Handling
- Since engines are pure functions, traditional exception handling within them is minimized.
- Validation logic inside an engine will result in a clear "rejection" DTO (e.g., `LoanDecisionDTO(is_approved=False, rejection_reason="Insufficient collateral")`).
- The outer controller is responsible for handling I/O errors or fatal state inconsistencies before calling an engine.

## 3. Interface 명세
The core of the new design is the `FinancialLedgerDTO`, which acts as the single source of truth, and the `EngineOutputDTO`, which encapsulates the result of any state-mutating operation.

- **`FinancialLedgerDTO`**: Contains all state previously held by `Bank` and `FinanceSystem`, including lists of `LoanStateDTO`, `DepositStateDTO`, and `BondStateDTO`.
- **`EngineOutputDTO`**: Bundles the `updated_ledger` and `generated_transactions`, ensuring that state changes and their corresponding economic events are atomically returned.

## 4. 검증 계획 (Testing & Verification Strategy)

This refactoring invalidates nearly all existing tests for `Bank` and `FinanceSystem`. The new testing strategy will be significantly more robust and maintainable.

- **New Test Cases (Unit Tests)**:
    - Each `FinanceEngine` will be tested in complete isolation.
    - Tests will manually construct a `FinancialLedgerDTO` representing a specific scenario (e.g., a borrower with high debt).
    - The test will call the engine's method with the test ledger and assert that the returned `EngineOutputDTO` contains the expected new state and transactions.
    - **Example**: `test_liquidation_engine_distributes_assets_correctly()`

- **Existing Test Impact**:
    - **High Impact**: All tests that instantiate `Bank` or `FinanceSystem` will fail.
    - **Mitigation**: These tests must be rewritten from scratch to follow the new Controller -> Engine pattern. Mocks will no longer be needed for internal components like `LoanManager` but will be replaced by constructing specific `FinancialLedgerDTO` states.

- **Integration Check**:
    - A full simulation run with a simple scenario (e.g., one firm, one bank) must complete without money leaks.
    - The system's total net worth (Assets - Liabilities) must remain constant across all engine operations, except where explicitly intended (e.g., liquidation value destruction). A "Zero-Sum Verifier" utility should be written to check this after each tick.

## 5. Mocking 가이드
- **금지 (Prohibited)**: Direct mocking of engine methods (`@patch('...LoanRiskEngine.assess')`).
- **필수 (Required)**: Tests should control engine behavior by providing tailored `FinancialLedgerDTO` inputs. To test how the system reacts to a loan rejection, you don't mock the `assess` method; you provide a ledger state that *causes* the engine to logically reject the loan.
- **Fixture Usage**: `conftest.py` fixtures should be updated to return `FinancialLedgerDTO` instances representing "golden" scenarios, not instantiated God Classes.

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 위험**: **Mitigated**. Engines only depend on the `engine_api.py` file, which contains only DTOs and Protocols. There are no dependencies between concrete engine implementations. The controller orchestrates the data flow, breaking the import cycle.

- **테스트 영향도**: **High / Acknowledged**. The existing test suite is rendered obsolete. The benefit is a new suite of highly modular, maintainable, and predictable unit tests for each business logic component. The cost is the high, one-time effort of rewriting them.

- **설정 의존성**: **Mitigated**. Configuration values (e.g., reserve ratios, interest rate premiums) should be passed explicitly to the engines as arguments or be part of the `FinancialLedgerDTO` itself, removing the dependency on a global `ConfigManager`.

- **선행 작업 권고**: A dedicated "state migration" script will be required to transform the saved state of old simulation runs (if any) into the new `FinancialLedgerDTO` format.

## 7. 🚨 Mandatory Reporting Verification

- **Insight**: This refactoring moves the system from an Object-Oriented paradigm (where objects manage their own state) to a more Functional paradigm (where stateless functions operate on external state). This dramatically improves predictability and testability.
- **Technical Debt Recorded**: The entire stateful architecture of `Bank` and `FinanceSystem` is identified as technical debt. This refactoring pays down that debt.
- **Report Location**: The insights gained from this architectural shift have been recorded in `communications/insights/RPT-20260211-StatelessFinance.md`.

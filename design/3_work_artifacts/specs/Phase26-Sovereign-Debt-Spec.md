```markdown
# Spec: Sovereign Debt & Corporate Finance System (Phase 26.5)

## 1. Overview

This specification details the implementation of a robust sovereign debt market and the integration of corporate tax collection with the atomic `SettlementSystem`. The primary goals are to eliminate systemic money leaks (TD-101, TD-102), formalize financial interfaces (TD-104), and establish a clear mechanism for government fiscal operations, including deficit financing and financial health monitoring. This design strictly adheres to the architectural mandate of using the `SettlementSystem` for all asset transfers.

## 2. Component Design

### 2.1. `FinanceSystem` (Module: `modules/finance/system.py`)

The `FinanceSystem` is enhanced to be the central hub for sovereign financial operations.

#### Responsibilities:
- **`issue_treasury_bonds(amount: float, current_tick: int) -> List[BondDTO]`**: Handles the creation and sale of government bonds when a deficit occurs. It calculates yield based on fiscal risk and uses the `SettlementSystem` to transfer funds from the buyer to the government.
- **`collect_corporate_tax(firm: IFinancialEntity, tax_amount: float) -> bool`**: A new method to execute the atomic collection of corporate taxes. It serves as an intermediary between the `TaxAgency` and the `SettlementSystem`.
- **`service_debt(current_tick: int)`**: Refactored to use the `SettlementSystem` to pay matured bonds, ensuring funds are transferred to the bondholder (Bank or Central Bank) instead of being destroyed.

### 2.2. `FiscalMonitor` (New Component: `modules/analysis/fiscal_monitor.py`)

A new, independent component responsible for observing and reporting on the government's fiscal health, adhering to the SRP and avoiding bloat in the `Government` agent.

#### Responsibilities:
- **`get_debt_to_gdp_ratio(government_dto: GovernmentStateDTO, world_dto: WorldStateDTO) -> float`**: Calculates the debt-to-GDP ratio using data from DTOs, ensuring it remains a stateless, observational tool.
- **`analyze_fiscal_stance(...)`**: (Future) Can be extended to analyze fiscal sustainability without modifying the `Government` agent.

### 2.3. `Government` Agent (Refactoring)

The `Government` agent will be refactored to delegate all financial transactions.

- **Direct Asset Mutation Removal**: All instances of `self._assets += ...` or `self._sub_assets(...)` related to economic transfers (taxes, subsidies, bond sales) will be removed.
- **Delegation**:
    - Tax collection will call `tax_agency.collect_tax(...)` which in turn calls `finance_system.collect_corporate_tax(...)`.
    - Deficit spending will trigger a call to `finance_system.issue_treasury_bonds(...)`.

### 2.4. `TaxAgency` (Refactoring)

The `TaxAgency` will be refactored to a pure calculation and orchestration role.

- The `collect_tax` method will no longer modify any agent's assets. It will calculate the tax owed and then call the `FinanceSystem`'s dedicated collection method to execute the transfer.

## 3. Logic Steps (Pseudo-code)

### 3.1. `FinanceSystem.issue_treasury_bonds`

```python
def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
    # 1. Get fiscal risk data from FiscalMonitor (or directly for now)
    # This avoids bloating the Government agent.
    debt_to_gdp = self.fiscal_monitor.get_debt_to_gdp_ratio(...) 
    base_rate = self.central_bank.get_base_rate()

    # 2. Calculate yield based on risk premium tiers from config
    risk_premium = calculate_risk_premium(debt_to_gdp, config.DEBT_RISK_PREMIUM_TIERS)
    yield_rate = base_rate + risk_premium

    # 3. Create Bond DTO
    new_bond = BondDTO(
        face_value=amount, 
        yield_rate=yield_rate, 
        maturity_date=current_tick + config.BOND_MATURITY_TICKS
    )

    # 4. Determine Buyer (Simplified: Bank is primary buyer)
    buyer = self.bank # IBankService interface
    
    # 5. Execute atomic transfer via SettlementSystem
    memo = f"Govt Bond Sale, Yield: {yield_rate:.2%}"
    transfer_successful = self.settlement_system.transfer(
        debit_agent=buyer,
        credit_agent=self.government, # IFinancialEntity
        amount=amount,
        memo=memo
    )

    # 6. Finalize
    if transfer_successful:
        self.outstanding_bonds.append(new_bond)
        buyer.add_bond_to_portfolio(new_bond) # Method on IBankService
        return [new_bond]
    else:
        log.error("Bond issuance failed: Buyer has insufficient funds.")
        return []

```

### 3.2. Corporate Tax Collection Flow

```python
# In TaxAgency.py
def collect_tax(self, firm: Firm, profit: float):
    tax_amount = self.calculate_corporate_tax(profit)
    if tax_amount > 0:
        # Delegate to FinanceSystem, do NOT touch assets here
        success = self.finance_system.collect_corporate_tax(firm, tax_amount)
        if success:
            log.info(f"Tax collection initiated for {firm.id}")
        else:
            log.warning(f"Tax collection failed for {firm.id}")

# In FinanceSystem.py
def collect_corporate_tax(self, firm: IFinancialEntity, tax_amount: float) -> bool:
    # Use SettlementSystem for atomic transfer
    memo = f"Corporate Tax, Firm ID: {firm.id}"
    return self.settlement_system.transfer(
        debit_agent=firm,
        credit_agent=self.government,
        amount=tax_amount,
        memo=memo
    )
```

## 4. DTO & Interface Specification (`api.py`)

The following interfaces are defined in `modules/finance/api.py`.

```python
from typing import Protocol, List

class BondDTO: ... # Existing DTO

class IFinancialEntity(Protocol):
    """Formal interface for any entity engaging in financial transactions."""
    id: int
    
    @property
    def assets(self) -> float: ...
    
    def deposit(self, amount: float, memo: str) -> None:
        """Public method to increase assets."""
        ...

    def withdraw(self, amount: float, memo: str) -> None:
        """Public method to decrease assets. Raises InsufficientFundsError."""
        ...

class IBankService(IFinancialEntity, Protocol):
    """Interface for commercial and central banks."""
    def add_bond_to_portfolio(self, bond: BondDTO) -> None: ...

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government_dto: "GovernmentStateDTO", world_dto: "WorldStateDTO") -> float: ...

class IFinanceSystem(Protocol):
    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]: ...
    def collect_corporate_tax(self, firm: IFinancialEntity, tax_amount: float) -> bool: ...
    def service_debt(self, current_tick: int) -> None: ...
    ... # Other methods
```

## 5. ✅ Money Leak Resolution (Addressing TD-101/WO-072)

The historical "Money Leak" issue stemmed from non-atomic, direct asset mutations (e.g., `debtor.assets -= amount` followed by a potential failure before `creditor.assets += amount`).

This design eradicates the problem by enforcing a single, golden path for all value transfers: the `SettlementSystem`.

- **Atomicity Guarantee**: `SettlementSystem.transfer()` is an atomic operation. It internally wraps the debit and credit operations in a `try...except` block. If the credit operation fails for any reason, the debit is rolled back.
- **Zero-Sum Principle**: Money is never created or destroyed, only moved. The total money supply remains constant within a single `transfer` call.
- **Example**: In the old `service_debt` logic, `self.government.assets -= total_repayment` would execute, and if a subsequent error occurred before the bondholder's assets were increased, that money would vanish from the system. The refactored `service_debt` will use `settlement_system.transfer(self.government, bond_holder, total_repayment)`, guaranteeing the payment either completes successfully or fails without changing any balances, thus preserving the system's monetary integrity.

## 6. 🚨 Risk & Impact Audit

This design explicitly addresses the risks identified in the pre-flight audit.

- **Systemic Integrity Risk (Direct Mutation)**: **MITIGATED**. The core of this spec is the mandatory, exclusive use of `SettlementSystem` for all financial state changes, directly resolving TD-101.
- **Architectural Constraint (God Class)**: **ADDRESSED**. The `FiscalMonitor` is designed as a separate, loosely-coupled component, preventing further bloat of the `Government` agent, as per SRP.
- **Interface Parity (Leaky Abstractions)**: **ADDRESSED**. The spec formalizes `IFinancialEntity` and `IBankService` as `Protocol`s with public `deposit`/`withdraw` methods (TD-104). The `SettlementSystem` will be refactored to use these public methods instead of protected `_add_assets`/`_sub_assets`.
- **Test Impact**: **ACKNOWLEDGED**.
    - **Refactoring Required**: Unit tests for `Government`, `TaxAgency`, and `FinanceSystem` must be updated.
    - **New Mocking Strategy**: Tests will now need to mock `SettlementSystem` and `FinanceSystem`. Assertions will verify that `settlement_system.transfer` is called with the correct `debit_agent`, `credit_agent`, and `amount`, rather than checking `agent.assets` values directly.

## 7. Verification Plan

- **Unit Tests**:
    - `test_finance_system.py`:
        - `test_issue_treasury_bonds_calls_settlement_system`: Mocks `SettlementSystem` and verifies it's called with `(buyer, government, amount)`.
        - `test_collect_corporate_tax_calls_settlement_system`: Verifies `transfer` is called with `(firm, government, tax_amount)`.
    - `test_fiscal_monitor.py`:
        - `test_debt_to_gdp_ratio`: Verifies correct calculation using mock DTOs.
- **Integration Test (`tests/integration/test_fiscal_cycle.py`)**:
    - **Scenario**:
        1. Government starts with 0 assets.
        2. Government attempts to spend, creating a deficit.
        3. `finance_system.issue_treasury_bonds` is triggered.
        4. `settlement_system` is called; a Bank's assets decrease and Government's assets increase.
        5. A Firm makes a profit.
        6. `tax_agency` calculates tax and calls `finance_system.collect_corporate_tax`.
        7. `settlement_system` is called; the Firm's assets decrease and Government's assets increase.
    - **Assertions**: Verify final asset balances of all parties and review `SettlementSystem` logs for correct transaction records.

## 8. Mandatory Reporting

**Jules's Implementation Directive**: During implementation, any unforeseen complexities, deviations from this specification, or potential improvements discovered must be documented. Create a new markdown file in `communications/insights/` named `WO-XXX-phase26-5-finance-insights.md` to log these findings for the team lead's review. All identified technical debt must be proposed for inclusion in `TECH_DEBT_LEDGER.md`.
```

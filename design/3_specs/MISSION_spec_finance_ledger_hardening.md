# 📄 Specification Draft: Finance & Ledger Architecture Hardening

**Mission Key**: `FINANCE-LEDGER-HARDENING-SPEC`
**Target Phase**: Finance & Ledger Stability (Addressing Phase 33/4.1 Tech Debt)
**Target Files**: 
- `modules/finance/api.py`
- `modules/government/components/monetary_ledger.py`
- `modules/system/api.py`
- `modules/finance/system.py`

---

## 1. 🔍 [Debt Review] Mandatory Ledger Audit

**Analysis of `TECH_DEBT_LEDGER.md` context:**
The current task aims to **Resolve** five critical technical debts related to the financial ledger and macroeconomic integrity:
1. **TD-FIN-NEGATIVE-M2**: Resolves "M2 Black Hole" by strictly separating positive balances from overdrafts.
2. **TD-BANK-RESERVE-CRUNCH**: Resolves liquidity lock-ups during bond issuance by enforcing reserve checks.
3. **TD-FIN-LIQUIDATION-DUST**: Resolves "Wealth Orphanage" by explicitly routing truncated pennies.
4. **TD-SYS-IMPLICIT-REGISTRY-LOOKUP**: Resolves duck-typing resolution via strict `ICurrencyHolder` registry indexing.
5. **TD-FIN-MAGIC-BASE-RATE**: Resolves hardcoded magic numbers by pulling from `IGlobalRegistry`.

**Potential Accumulation/Risks**:
- Implementing strict M2 constraints and zero-sum dust routing will likely **exacerbate Test Debt**. Legacy macro-economic scenario judges expecting M2 = base_M2 + negative_balances will hard-fail. 
- Refactoring the `MonetaryLedger` to use an isolated `ICurrencyHolder` registry index mitigates God Class dependency on `IWorldState` but requires careful synchronization during agent birth/death lifecycles.

---

## 2. 🏛️ Detailed Design & Logic Steps (Pseudo-code)

### 2.1. TD-FIN-NEGATIVE-M2 & SRP (M2 vs SystemDebt)
**Concept**: Separate M2 calculation into asset and liability tracking.
```python
# In modules/government/components/monetary_ledger.py
def calculate_total_money(self) -> MoneySupplyDTO:
    total_m2 = 0
    total_debt = 0
    
    # Utilizing strict registry (TD-SYS-IMPLICIT-REGISTRY-LOOKUP)
    for agent in self._currency_holder_registry.get_all():
        balance = agent.get_balance(DEFAULT_CURRENCY)
        if balance > 0:
            total_m2 += balance
        else:
            total_debt += abs(balance)
            
    return MoneySupplyDTO(
        m2_supply=total_m2, 
        system_debt=total_debt, 
        currency=DEFAULT_CURRENCY
    )
```

### 2.2. TD-FIN-LIQUIDATION-DUST (Dust Settlement Service)
**Concept**: Truncated fractional pennies must not vanish. They are collected and swept to the Central Bank's "Dust Reserve".
```python
# Pseudo-code for AssetBuyout / Liquidation 
def allocate_liquidation_funds(self, total_pennies: int, creditors: List[AgentID]) -> Dict[AgentID, int]:
    allocations = {}
    pennies_remaining = total_pennies
    
    for creditor in creditors:
        share = calculate_pro_rata_share() # returns float
        amount = math.floor(share)
        allocations[creditor] = amount
        pennies_remaining -= amount
        
    if pennies_remaining > 0:
        # Sweep dust to Central Bank or SystemTreasury to maintain zero-sum integrity
        self.central_bank.inject_dust(pennies_remaining)
        
    return allocations
```

### 2.3. TD-BANK-RESERVE-CRUNCH
**Concept**: Bond issuance cannot exceed available liquidity.
```python
def issue_treasury_bonds(self, amount: int) -> BondIssuanceResultDTO:
    bank_reserves = self.bank.get_reserves()
    issue_amount = min(amount, bank_reserves)
    
    if issue_amount <= 0:
        return BondIssuanceResultDTO(success=False, amount_issued=0, reason="RESERVE_CRUNCH")
        
    # Proceed with issuance of issue_amount
    ...
```

### 2.4. TD-SYS-IMPLICIT-REGISTRY-LOOKUP
**Concept**: `MonetaryLedger` maintains an internal index of `ICurrencyHolder` rather than asking the God Class `IWorldState` for all firms/households.
```python
# Upon agent creation in Factory or Orchestrator:
if isinstance(agent, ICurrencyHolder):
    monetary_ledger.register_holder(agent)
```

### 2.5. TD-FIN-MAGIC-BASE-RATE
**Concept**: Rely on `IGlobalRegistry`.
```python
def get_base_rate(self) -> float:
    # Requires injection of IGlobalRegistry
    return self.registry.get("FINANCE.BASE_INTEREST_RATE", 0.03)
```

---

## 3. 📦 Interface Specifications (API Outline)

### `modules/finance/dtos/api.py` (Draft Addition)
```python
from dataclasses import dataclass
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

@dataclass(frozen=True)
class MoneySupplyDTO:
    """DTO for strictly segregated M2 and Debt aggregations."""
    m2_supply: int
    system_debt: int
    currency: CurrencyCode = DEFAULT_CURRENCY

@dataclass(frozen=True)
class BondIssuanceResultDTO:
    """Result of attempting to issue treasury bonds."""
    success: bool
    amount_issued: int
    reason: str = "SUCCESS"
```

### `modules/finance/api.py` (Draft Addition)
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IDustReceiver(Protocol):
    """Protocol for an entity capable of receiving zero-sum fractional dust."""
    def inject_dust(self, amount_pennies: int) -> None:
        ...

@runtime_checkable
class ICurrencyHolderRegistry(Protocol):
    """Protocol for strictly tracking valid currency holders."""
    def register_holder(self, agent: 'ICurrencyHolder') -> None:
        ...
    def get_all(self) -> list['ICurrencyHolder']:
        ...
```

---

## 4. 🚨 Risk & Impact Audit (Pre-flight Mitigations)

1. **Hidden Dependencies & God Classes**: 
   - **Mitigation**: The `MonetaryLedger` will *no longer* accept `SimulationState` or `IWorldState` as an argument. It will expose a `register_holder(ICurrencyHolder)` method. The lifecycle orchestrator is responsible for registration, cutting the God Class dependency.
2. **Potential Circular Imports**:
   - **Mitigation**: `MoneySupplyDTO` and `BondIssuanceResultDTO` are completely devoid of domain logic and rely only on primitive types and `CurrencyCode`. They are placed in standard DTO boundary files, utilizing `TYPE_CHECKING` for type annotations.
3. **Violations of Single Responsibility Principle (SRP)**:
   - **Mitigation**: `IAssetRecoverySystem` will delegate the actual dust resolution to `IDustReceiver`. The M2 calculation explicitly separates `m2_supply` and `system_debt` into distinct fields within `MoneySupplyDTO`.
4. **Risks to Existing Tests**:
   - **Macro-Economic Verification Breaks**: Tests asserting `total_money == 1000000` will fail if there are bankruptcies. Test verification functions must be rewritten to assert: `(M2 - SystemDebt) + CentralBankReserves == InitialMoney`.
   - **Strict Protocol Mocking Failures**: Legacy tests using `MagicMock` for agents will fail the `isinstance(agent, ICurrencyHolder)` check. **Action**: Ensure test agents implement `ICurrencyHolder` or use `MagicMock(spec=ICurrencyHolder)`.

---

## 5. 🧪 Testing & Verification Strategy

- **New Test Cases**:
  - `test_monetary_ledger_m2_segregation`: Validate that a mock agent with `-500` balance increases `SystemDebt` by 500 and leaves `M2` unchanged.
  - `test_dust_sweeping_zero_sum_integrity`: Simulate a 100 penny liquidation split among 3 creditors (33 pennies each). Ensure the 1 remaining penny correctly hits the `IDustReceiver`.
  - `test_bond_issuance_reserve_limit`: Request 50,000 bond issuance when bank reserves are 10,000. Verify only 10,000 is issued.
- **Mocking Guide**:
  - **MANDATORY**: Do not instantiate raw `MagicMock()` in finance tests.
  - Use `conftest.py`'s `golden_households` and `golden_firms`. If custom agents are required, use `spec=ICurrencyHolder`.
  - **Schema Change Notice**: Since `MoneySupplyDTO` structure is replacing raw `int` return types, any `get_total_money()` snapshot comparisons in `design/_archive/snapshots/` will require re-harvesting via `fixture_harvester.py`.
- **Integration Check**: 
  - `pytest tests/systems/test_finance_system.py` must pass.
  - The zero-sum macro verifier (`audit_economic_integrity.py` / `check_tx.py`) must be updated to balance `M2 - Debt + Dust == Base`.

---

## 6. ⚠️ [Conceptual Debt]

- **Context Triage: Ignore legacy M2 bounds checks**. Any test that strictly validates `total_money` as a single scalar integer without accommodating `SystemDebt` is functionally deprecated by this Spec. The conceptual integrity of double-entry accounting overrides the physical consistency of those outdated tests.
- **Lifecycle Registration Sync**: By moving to an explicit `ICurrencyHolderRegistry`, if an agent is destroyed/inactivated but not deregistered, it may inflate M2 with ghost balances. A future debt ticket (`TD-SYS-AGENT-DEREGISTRATION`) should be tracked for safe memory management.

---

## 7. 📝 Mandatory Reporting Instruction

**TO IMPLEMENTER (JULES)**:
Upon completion of this specification's implementation, you **MUST** record your insights, any unexpected architectural landmines, and the exact regression fixes applied to the tests.

Create a new file independently at:
`communications/insights/FINANCE-LEDGER-HARDENING-SPEC.md`

Your file **MUST** contain:
1. `[Architectural Insights]`: Note the changes made to the M2 aggregate and the Dust sweeping logic.
2. `[Regression Analysis]`: Explain which legacy macro tests failed due to the new `MoneySupplyDTO` and `max(0, balance)` logic, and how you fixed them.
3. `[Test Evidence]`: The FULL literal output of `pytest` demonstrating 100% test pass.

**DO NOT** append this to `manual.md` or any other shared registry. Failure to produce this insight file will result in a Hard-Fail of the mission.
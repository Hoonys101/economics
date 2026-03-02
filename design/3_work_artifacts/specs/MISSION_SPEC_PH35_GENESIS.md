# MISSION_SPEC: Genesis Protocol & M2 Integrity (MISSION-PH35-SPEC-GENESIS)

## 1. Executive Summary
This specification addresses critical financial integrity issues, specifically **TD-FIN-NEGATIVE-M2** (M2 Black Hole) and **TD-115/117** (Tick 1 Asset Leak & DTO Purity Regression). The solution enforces a "Sacred Sequence" for system bootstrapping to prevent "Helicopter Money," routes all macro-financial calculations through the Single Source of Truth (`MonetaryLedger`), and completely eradicates raw dictionary metadata in transactions by introducing strict DTO typing.

---

## 2. API & DTO Definitions (`api.py` Draft)

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from modules.system.api import AgentID, CurrencyCode

@dataclass(frozen=True)
class TransactionMetadataDTO:
    """
    Replaces raw dict `metadata` in Transactions to enforce DTO Purity.
    Ensures genesis transfers are strictly trackable.
    """
    is_genesis: bool = False
    memo: Optional[str] = None
    original_metadata: Optional[Dict[str, Any]] = None  # Fallback for unmigrated fields

@dataclass(frozen=True)
class MoneySupplyDTO:
    """
    Physics-tier monetary aggregate SSoT. 
    Formula: m2_pennies - system_debt_pennies == m0_baseline_pennies (in a closed system)
    """
    m2_pennies: int             # Sum(max(0, balance))
    system_debt_pennies: int    # Sum(abs(min(0, balance)))
    m0_baseline_pennies: int    # Initial money injected at Genesis

class IMonetaryLedger(Protocol):
    def calculate_total_money(self) -> MoneySupplyDTO:
        """Single Source of Truth for M2 and System Debt calculation."""
        ...

class IBootstrapper(Protocol):
    def execute_sacred_sequence(self, central_bank: Any, agents: List[Any]) -> None:
        """Executes strict 4-phase initialization."""
        ...
```

---

## 3. Logic & Implementation Steps (Pseudo-code)

### 3.1. Bootstrapper: The Sacred Sequence
To resolve initialization race conditions (God Context), the `Bootstrapper` or `SimulationInitializer` MUST execute in this exact order:

```python
def execute_sacred_sequence(central_bank, all_agents, registry, settlement_system):
    # Phase 1: Fiat Lux (M0 Minting)
    # Central Bank creates initial money from the void.
    central_bank.mint(CONFIG.INITIAL_MONEY_SUPPLY)
    m0_baseline = central_bank.get_balance()

    # Phase 2: Agent Registration
    # All agents registered with 0.0 assets
    for agent in all_agents:
        registry.register(agent)

    # Phase 3: Account Linking
    # Accounts strictly linked BEFORE any capital injection
    for agent in all_agents:
        settlement_system.register_account(bank_id=ID_CENTRAL_BANK, agent_id=agent.id)

    # Phase 4: Genesis Distribution (Atomic Transfers)
    genesis_metadata = TransactionMetadataDTO(is_genesis=True, memo="GENESIS_GRANT")
    for agent, amount in initial_distribution_plan:
        settlement_system.transfer(
            debit_agent=central_bank,
            credit_agent=agent,
            amount=amount,
            metadata=genesis_metadata
        )
```

### 3.2. M2 Calculation Redesign (SSoT via `MonetaryLedger`)
Modify `calculate_total_money` logic to accurately reflect liquidity vs. debt.

```python
class MonetaryLedger:
    def calculate_total_money(self) -> MoneySupplyDTO:
        m2 = 0
        system_debt = 0
        
        for agent in self.registry.get_all_financial_agents():
            balance = self.settlement_system.get_balance(agent.id)
            if balance > 0:
                m2 += balance
            elif balance < 0:
                system_debt += abs(balance)
                
        return MoneySupplyDTO(
            m2_pennies=m2,
            system_debt_pennies=system_debt,
            m0_baseline_pennies=self.m0_baseline
        )

# WorldState simply delegates:
class WorldState:
    def calculate_total_money(self) -> MoneySupplyDTO:
        return self.get_monetary_ledger().calculate_total_money()
```

---

## 4. 🚨 [Audit] Pre-Implementation Risk Analysis

1. **SSoT Calculation Conflict**: 
   - *Risk*: `WorldState`, `SimulationState`, and `MonetaryLedger` all having independent M2 calculation logic.
   - *Mitigation*: Hard-deprecate logic in `WorldState` and `SimulationState`, replacing them with pure pass-through delegation to `MonetaryLedger.calculate_total_money()`.
2. **DTO Purity Violation via Metadata**:
   - *Risk*: Replacing `metadata={}` with `metadata=TransactionMetadataDTO()` alters the constructor of the core `Transaction` object. Code relying on `tx.metadata.get("key")` will crash.
   - *Mitigation*: Implementation MUST execute a codebase-wide search for `Transaction(` and `tx.metadata` to refactor all call sites.
3. **Accounting Imbalance (Zero-Sum Gap)**:
   - *Risk*: If a transfer fails silently or an agent is excluded from `get_all_financial_agents()`, `M2 - SystemDebt != M0` will cause systemic assertions to panic.
   - *Mitigation*: The `SettlementSystem.audit_total_m2()` must explicitly account for `MoneySupplyDTO.system_debt_pennies`.

---

## 5. 🚨 [Debt Review] Mandatory Ledger Audit

- **[RESOLVE] TD-FIN-NEGATIVE-M2 (M2 Black Hole)**: This spec definitively resolves the issue by separating overdrafts into `SystemDebt`, restoring M2 as a true measure of positive liquidity.
- **[RESOLVE] TD-LIFECYCLE-GHOST-FIRM**: The 4-Phase "Sacred Sequence" structurally prevents capital injection before firm registration and bank account linkage.
- **[RESOLVE] TD-ARCH-SSOT-BYPASS**: Enforces strict reliance on `MonetaryLedger` for macro-metrics.
- **[IMPACT] TD-ARCH-GOD-DTO**: Positively impacts this debt by removing direct dependency on `SimulationState` for M2 calculations, delegating down to domain modules.

---

## 6. 🚨 [Conceptual Debt] (정합성 부채)

1. **Legacy Test Fixture Invalidation**: Hundreds of existing tests use `agent.assets = 1000` or `agent._add_assets(1000)` to bypass the Settlement System. This introduces massive technical debt for the test suite. *Action Required*: All such tests must be migrated to use `golden_households` or `SettlementSystem.transfer()` with `TransactionMetadataDTO(is_genesis=True)`.
2. **System Agent Exclusions**: `get_all_financial_agents()` must explicitly exclude `ID_SYSTEM`, `ID_ESCROW`, and `ID_PUBLIC_MANAGER` to prevent double-counting M2. This relies on strict ID conventions which remains a conceptual vulnerability.

---

## 7. Testing & Verification Strategy

- **New Test Cases**:
  - `test_genesis_sequence_strict_order`: Use `unittest.mock.call` tracking to verify that `registry.register` occurs *strictly before* `settlement_system.transfer`.
  - `test_m2_calculation_overdraft_segregation`: Setup an agent with `-500` pennies. Verify `M2` remains unchanged while `SystemDebt` increases by `500`. Verify `M2 - SystemDebt == M0_Baseline`.
- **Existing Test Impact**:
  - **Zero-Sum Tests**: Any test evaluating `assert m2 == total` MUST be updated to `assert (m2_pennies - system_debt_pennies) == m0_baseline_pennies`.
  - **Mock Updates**: All `MagicMock` setups for `SettlementSystem` must be updated to expect `metadata: TransactionMetadataDTO`.
- **Integration Verification**: 
  - Run `scripts/audit/trace_leak.py` at Tick 0 and Tick 1 to ensure `Delta: 0.000000` and no M2 jump occurs.

---

## 8. 🚨 [Routine] Mandatory Reporting Instruction

**[TO THE IMPLEMENTATION AGENT]**
Upon completion of this implementation, you **MUST** create a new file at `communications/insights/MISSION-PH35-SPEC-GENESIS.md`. 
Do NOT append to `manual.md`.
Your report MUST include:
1. **[Architectural Insights]**: Any new technical debt discovered during the `TransactionMetadataDTO` migration or Sacred Sequence refactor.
2. **[Regression Analysis]**: Documentation of which legacy tests were broken by the M2/Zero-Sum formula changes, and how you updated their fixtures.
3. **[Test Evidence]**: The FULL literal output of `pytest` demonstrating 100% test pass rate across the suite. Submissions without this evidence will be hard-failed.
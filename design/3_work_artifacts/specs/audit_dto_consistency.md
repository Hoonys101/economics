# DTO Consistency Audit Report (TD-DTO-STAB)

## 1. Executive Summary
This audit reviewed the codebase for Data Transfer Object (DTO) consistency, specifically targeting `simulation/dtos`, `simulation/models`, and `modules/**/api.py`. The primary goal was to identify conflicting DTOs, fragile access patterns, and propose a consolidation plan adhering to the "DTO Purity" and "Protocol Purity" architectural guardrails.

**Key Findings:**
- **Fragmentation:** Multiple definitions for core concepts like Orders (`StockOrder` vs `CanonicalOrderDTO`) and Transactions (`Transaction` vs `TransactionDTO`).
- **Fragility:** `FirmStateDTO` relies on extensive `hasattr` checks, violating protocol purity.
- **Legacy Debt:** Deprecated interfaces (`IFinancialEntity`) and aliases (`OrderDTO`) persist.

## 2. Inventory of DTOs

### 2.1 Simulation Core (`simulation/models.py`)
- `Transaction`: Standard dataclass for executed trades.
- `StockOrder`: **DEPRECATED**. Legacy DTO for stock market.
- `Share`: Standard dataclass.
- `RealEstateUnit`: Standard dataclass (with lien support).
- `Order`: Alias for `CanonicalOrderDTO`.

### 2.2 Simulation DTOs (`simulation/dtos/`)
- `FirmStateDTO`: Aggregates firm state (Finance, Production, Sales, HR). **High Fragility**.
- `ScenarioStrategy`: Configuration DTO.
- `LegacySettlementAccount`: Transient escrow DTO.
- `TransactionDTO`: **Type Alias for `Any`**. Weak typing.
- `WatchtowerSnapshotDTO`: Analytics aggregate.

### 2.3 Module APIs (`modules/**/api.py`)
- **Market:** `CanonicalOrderDTO` (The Standard), `OrderBookStateDTO`, `MatchingResultDTO`.
- **Finance:** `MoneyDTO`, `TransactionResult`, `LiquidationContext`.
- **Simulation:** `AgentStateDTO`, `AgentSensorySnapshotDTO`, `LiquidationConfigDTO`.
- **Household:** `BudgetPlan`, `HousingActionDTO`.
- **Government:** `BondRepaymentDetailsDTO`, `FiscalPolicyDTO`.

## 3. Consistency Analysis

### 3.1 Conflicting DTOs
| Concept | Primary DTO | Conflicting/Legacy DTO | Impact |
| :--- | :--- | :--- | :--- |
| **Order** | `CanonicalOrderDTO` | `StockOrder` | Duplicate logic, maintenance burden. |
| **Transaction** | `simulation.models.Transaction` | `simulation.dtos.transactions.TransactionDTO` (Any) | Loss of type safety in function signatures. |
| **Financial Agent** | `IFinancialAgent` | `IFinancialEntity` | `IFinancialEntity` lacks multi-currency support. |
| **Agent State** | `AgentSensorySnapshotDTO` | `AgentStateDTO` | Conceptual overlap; Sensory is for observation, State for persistence. |

### 3.2 Fragile Access Patterns
- **`FirmStateDTO.from_firm`:** This method constructs a DTO by inspecting the `firm` object using over 15 `hasattr` checks. This implies `Firm` does not adhere to a strict protocol for state export, making the DTO generator brittle to internal refactors.
- **`convert_legacy_order_to_canonical`:** Uses duck typing to inspect `order` objects. While necessary for migration, it masks type errors.
- **`TransactionDTO = Any`:** Completely bypasses type checking for transaction objects in `simulation/dtos/transactions.py`.

## 4. Consolidation Plan

### Phase 1: Standardization (Immediate)
1.  **Deprecate `StockOrder`:** Add `@deprecated` warning and ensure no new code uses it.
2.  **Enforce `CanonicalOrderDTO`:** Update `simulation/models.py` to alias `Order` solely to `CanonicalOrderDTO`.
3.  **Remove `TransactionDTO = Any`:** Replace with `simulation.models.Transaction` or a Union if needed.

### Phase 2: Protocol Adoption (Short Term)
1.  **Define `IFirmStateProvider` Protocol:** Create a protocol that `Firm` must implement, enforcing a `get_state_dto()` method.
2.  **Refactor `FirmStateDTO`:** Remove `from_firm` scraping logic. Rely on the provider protocol.
3.  **Deprecate `IFinancialEntity`:** Replace all usages with `IFinancialAgent`.

### Phase 3: Cleanup (Medium Term)
1.  **Remove `StockOrder`:** Delete the class entirely once all references are gone.
2.  **Remove `convert_legacy_order_to_canonical`:** Once `StockOrder` is gone, this adapter is obsolete.
3.  **Unify Agent State:** Clearly document and separate `AgentSensorySnapshotDTO` (Public/Observed) vs `AgentStateDTO` (Internal/SaveLoad).

## 5. Verification Methodology
This audit was conducted by scanning the file structure and reading key files (`simulation/models.py`, `simulation/dtos/*.py`, `modules/**/api.py`). The analysis focused on:
1.  Identifying multiple classes representing the same domain concept.
2.  Checking for loose typing (`Any`, `dict`) where DTOs should be used.
3.  Examining "conversion" or "factory" methods for `hasattr` usage.

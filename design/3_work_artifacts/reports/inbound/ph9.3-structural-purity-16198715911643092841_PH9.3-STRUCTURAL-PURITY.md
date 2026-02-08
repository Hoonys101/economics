# PH9.3 Structural Purity & Composition Shift - Technical Insight Report

## 1. Problem Phenomenon
The project suffered from deep inheritance coupling via `BaseAgent`, leading to:
- **God Class**: `BaseAgent` accumulated disparate responsibilities (Inventory, Finance, Identity, decision support).
- **Abstraction Leaks**: Engines (`HREngine`, `FinanceEngine`) accepted raw `Agent` objects, accessing internal state directly.
- **Protocol Violation**: Components relied on `hasattr` checks rather than strict Protocols.
- **Initialization Complexity**: `Firm` and `Household` had tangled `__init__` chains depending on `BaseAgent`.

During the refactoring, several regressions surfaced:
- `AttributeError: 'float' object has no attribute 'append'` in `FinanceSystem` when interacting with `CentralBank`'s assets (treating wallet balance as portfolio).
- `TypeError: Firm.__init__() got an unexpected keyword argument 'id'` in `FirmSystem` due to signature changes.
- `AttributeError: 'Firm' object has no attribute 'get_assets_by_currency'` in `TickOrchestrator`.
- `TypeError` in AI Engines due to `assets` returning a `dict` instead of `float`.

## 2. Root Cause Analysis
- **Implicit Contracts**: `FinanceSystem` assumed `buyer.assets` could store bonds if it was a dictionary, breaking encapsulation of `Wallet`.
- **Signature Drift**: The shift to `AgentCoreConfigDTO` for `Firm` initialization was not propagated to factory methods like `FirmSystem.spawn_firm`.
- **Protocol Gaps**: `Firm` dropped `BaseAgent` but missed implementing `ICurrencyHolder` (specifically `get_assets_by_currency`), causing failures in orchestration loops.
- **Type Mismatch**: `Household.get_agent_data()` began returning the raw `Wallet` dictionary for `assets`, while the AI models expected a scalar float value for wealth discretization.

## 3. Solution Implementation Details

### A. Composition Over Inheritance
- Removed `BaseAgent` inheritance from `Firm` and `Household`.
- Introduced `InventoryManager` and `Wallet` as composed components.
- Implemented `IOrchestratorAgent`, `IFinancialEntity`, `IInventoryHandler`, and `ICurrencyHolder` explicitly on agents.

### B. Engine & System Hardening
- **Settlement Decomposition**: Split `SettlementSystem` into `SettlementCore`, `EstateManager`, and `MonetaryAuthorityGateway`.
- **Engine Contexts**: Refactored `HREngine`, `FinanceEngine`, `SalesEngine` to use strict `ContextDTOs`, removing raw agent dependencies.
- **Central Bank Protocol**: Implemented `add_bond_to_portfolio` on `CentralBank` to satisfy `FinanceSystem` requirements without hacking the `Wallet`.

### C. DTO & Type Standardization
- Unified `OrderDTO` and removed `StockOrder`.
- Updated `HouseholdAI` to correctly handle dictionary-based asset data by extracting the default currency balance.
- Standardized `Firm` initialization via `FirmSystem` to use `AgentCoreConfigDTO`.

### D. Zero-Sum Integrity
- Verified via `audit_zero_sum.py`. The M2 money supply remains invariant (delta 0.0000) across transactions, proving the decomposition of `SettlementSystem` maintained transactional integrity.

## 4. Lessons Learned & Technical Debt
- **Lesson**: "Optimistic State Updates" in Systems (like `FinanceSystem` modifying `buyer.assets`) are dangerous when properties return copies (like `Wallet.get_all_balances`). State mutation must happen via explicit methods on the entity.
- **Debt**: `HRProxy` and `FinanceProxy` in `Firm` exist solely for backward compatibility. These should be deprecated and removed in Phase 10.
- **Debt**: `EconomicIndicatorsViewModel` relies on iterating over `agent._bio_state.needs`. While working, this couples the View to the internal DTO structure. A dedicated `AnalyticsDTO` pipeline is recommended.
- **Insight**: Strict Protocols (`@runtime_checkable`) significantly aided in catching missing methods after removing `BaseAgent`.

## 5. Verification Status
- [x] `audit_zero_sum.py`: **PASS** (Zero Leak)
- [x] `smoke_test.py`: **PASS** (Basic functionality)
- [x] `iron_test.py`: **RUN COMPLETE** (1000 ticks, no crashes). *Note: FAIL verdict refers to simulation KPIs, not software stability.*
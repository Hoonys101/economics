# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

## 📑 Table of Contents
1. [Core Summary Table](#-core-summary-table)
2. [Architecture & Infrastructure](#architecture--infrastructure)
3. [Financial Systems (Finance & Transactions)](#financial-systems-finance--transactions)
4. [AI & Economic Simulation](#ai--economic-simulation)
5. [Market & Systems](#market--systems)
6. [Lifecycle & Configuration](#lifecycle--configuration)
7. [Testing & Quality Assurance](#testing--quality-assurance)
8. [DX & Cockpit Operations](#dx--cockpit-operations)

---

## 📊 Core Summary Table

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-FIRM-COUP** | Architecture | **Parent Pointer Pollution**: `Firm` departments use `self.parent`, bypassing Orchestrator. | **High**: Structural Integrity. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-init. | **Low**: Fragility. | Open |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singleton `government`. | **Medium**: Logic Drift. | Audit Done |
| **TD-CRIT-FLOAT-CORE** | Finance | **Float Core**: `SettlementSystem` and `MatchingEngine` use `float` instead of `int`. | **Critical**: Determinism. | Audit Done |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation. | **Low**: Leak. | Open |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Handler**: `bailout`, `bond_issuance` tx types not registered. | **High**: Failure. | Audit Done |
| **TD-PROTO-MONETARY** | Transaction | **Monetary Protocol Violation**: `MonetaryHandler` uses `hasattr` instead of Protocols. | **Low**: Fragility. | Open |
| **TD-AI-DEBT-AWARE** | AI | **Constraint Blindness**: AI spams spend intents at debt ceiling. | **Medium**: AI Performance. | **RESOLVED** |
| **TD-CONF-MAGIC-NUMBERS** | Config | **Magic Numbers**: Hardcoded constants in `FinanceEngine` (Z-Score, Divisors). | **Low**: Configurability. | Open |
| **TD-ARCH-LOAN-CIRCULAR** | Architecture | **Circular Dependency**: Firm depends on concrete `LoanMarket` for debt status. | **Medium**: Coupling. | Open |
| **TD-ECON-WAR-STIMULUS** | Economic | **Fiscal Masking**: Stimulus prevents GDP 0 but masks wage-affordability imbalances. | **Medium**: Policy. | Open |
| **TD-MARKET-FLOAT-CAST** | Market | **Unsafe Quantization**: Direct `int()` cast in `matching_engine.py` instead of rounding. | **Medium**: Precision. | Open |
| **TD-MARKET-STRING-PARSE** | Market | **Brittle Key Parsing**: `StockMarket` splits strings to find `firm_id`. | **Low**: Fragility. | Open |
| **TD-DEPR-STOCK-DTO** | Market | **Legacy DTO**: `StockOrder` is deprecated. Use `CanonicalOrderDTO`. | **Low**: Tech Debt. | Open |
| **TD-LIFECYCLE-STALE** | Lifecycle | **Queue Pollution**: Missing scrubbing of `inter_tick_queue` after liquidation. | **Medium**: Determinism. | Audit Done |
| **TD-CONF-GHOST-BIND** | Config | **Ghost Constants**: Modules bind config values at import time. | **Medium**: Dynamic. | Identified |
| **TD-SYS-ACCOUNTING-GAP** | Systems | **Accounting Accuracy**: `accounting.py` misses tracking buyer expenses. | **Medium**: Accuracy. | Open |
| **TD-ARCH-FIRM-MUTATION** | Agents | **In-place State Mutation**: `Firm` engines mutate state objects directly. | **Medium**: Structural. | Open |
| **TD-ANALYTICS-DTO-BYPASS** | Systems | **Encapsulation Bypass**: `analytics_system.py` calls `agent.get_quantity` directly. | **Low**: Purity. | Open |
| **TD-SYS-PERF-DEATH** | Systems | **O(N) Rebuild**: `death_system.py` uses O(N) rebuild for `state.agents`. | **Low**: Perf. | Open |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync. | **Low**: Flakiness. | Identified |
| **TD-TEST-COCKPIT-MOCK** | Testing | **Cockpit 2.0 Mock Regressions**: Tests use deprecated `system_command_queue`. | **High**: Silent Failure. | Identified |
| **TD-TEST-LIFE-STALE** | Testing | **Stale Lifecycle Logic**: `test_engine.py` calls refactored liquidation methods. | **High**: Breakdown. | Identified |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | Identified |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. | **Medium**: Quality. | Open |
| **TD-DX-AUTO-CRYSTAL** | DX / Ops | **Crystallization Overhead**: Manual Gemini Manifest registration required. | **Medium**: Friction. | Open |

---

## Architecture & Infrastructure
---
### ID: TD-ARCH-FIRM-COUP
- **Title**: Parent Pointer Pollution
- **Symptom**: `Department` classes in `Firm` initialized with `self.parent = firm`.
- **Risk**: Circular dependencies and "God-class" sprawl. Departments modify state in other departments directly.
- **Solution**: Refactor to stateless engines. Pass explicit DTOs.
- **Related**: [MISSION_firm_ai_hardening_spec.md](../../../artifacts/specs/MISSION_firm_ai_hardening_spec.md)

### ID: TD-ARCH-FIRM-MUTATION
- **Title**: Firm In-place State Mutation
- **Symptom**: `firm.py` passes `self.sales_state` to engines without capturing a return DTO.
- **Risk**: Violates the "Stateless Engine & Orchestrator" pattern.
- **Solution**: Refactor `BrandEngine` and `SalesEngine` to return `ResultDTOs`.

### ID: TD-ARCH-DI-SETTLE
- **Title**: Dependency Injection Timing
- **Symptom**: Circular dependency risks due to post-init service injection.
- **Risk**: Initialization fragility.
- **Solution**: Move to Factory-based initialization or early registry lookup.

### ID: TD-ARCH-GOV-MISMATCH
- **Title**: Singleton vs List Mismatch
- **Symptom**: `WorldState` has `governments` (List) vs Singleton `government`.
- **Risk**: Logic Fragility.
- **Solution**: Standardize on a single representation for government access.

---

## Financial Systems (Finance & Transactions)
---
### ID: TD-CRIT-FLOAT-CORE (M&A Expansion)
- **Title**: M&A and Stock Market Float Violation
- **Symptom**: `MAManager` passes `float` offer prices to settlement, causing errors.
- **Risk**: Runtime crash during hostile takeovers or mergers.
- **Solution**: Quantize all valuations using `round_to_pennies()`.

### ID: TD-INT-BANK-ROLLBACK
- **Title**: Rollback Coupling
- **Symptom**: Bank rollback logic dependent on `hasattr` implementation details.
- **Risk**: Abstraction Leak.
- **Solution**: Move rollback logic to `TransactionProcessor` and use strict protocols.

### ID: TD-RUNTIME-TX-HANDLER
- **Title**: Missing Transaction Handlers
- **Symptom**: `bailout`, `bond_issuance` tx types not registered.
- **Risk**: Runtime Failure.
- **Solution**: Register all transaction types with the `TransactionEngine`.

### ID: TD-PROTO-MONETARY
- **Title**: Monetary Protocol Violation
- **Symptom**: `MonetaryTransactionHandler` uses `isinstance` checks on concrete classes.
- **Risk**: Logic Fragility.
- **Solution**: Refactor to use `IInvestor` and `IPropertyOwner` protocols throughout.

---

## AI & Economic Simulation
---
### ID: TD-AI-DEBT-AWARE
- **Title**: AI Constraint Blindness (Log Spam)
- **Symptom**: AI proposes aggressive investments while in a debt spiral.
- **Risk**: Inefficient decision-making. AI fails to "learn" the barrier.
- **Solution**: Add `current_debt_ratio` to AI input DTO and penalize rejected intents in reward function.

### ID: TD-ECON-WAR-STIMULUS
- **Title**: Fiscal Imbalance & Stimulus Dependency
- **Symptom**: GDP/Welfare metrics are propped up by high frequency stimulus triggers.
- **Risk**: Artificially propped economy. Masking logic errors in Firm pricing/wage models.
- **Solution**: Implement progressive taxation and productivity-indexed wage scaling.

---

## Market & Systems
---
### ID: TD-MARKET-FLOAT-CAST
- **Title**: Unsafe Quantization in Market Matching
- **Symptom**: `matching_engine.py` uses direct `int()` casting for `trade_total_pennies`.
- **Risk**: Potential calculation loss if quantities involve extremely small precision floats.
- **Solution**: Replace with explicit `round_to_pennies` logic.

### ID: TD-MARKET-STRING-PARSE
- **Title**: Brittle ID Parsing in StockMarket
- **Symptom**: `StockMarket.get_price` splits `item_id` using strings to extract `firm_id`.
- **Risk**: Highly coupled to naming conventions, preventing scalable keys.
- **Solution**: Create dedicated DTO keys or pass semantic ID tuples.

### ID: TD-DEPR-STOCK-DTO
- **Title**: Legacy DTO Usage
- **Symptom**: `StockOrder` is deprecated.
- **Risk**: Technical Debt.
- **Solution**: Use `CanonicalOrderDTO` instead of `StockOrder`.

### ID: TD-SYS-ACCOUNTING-GAP
- **Title**: Missing Buyer Expense Tracking
- **Symptom**: `accounting.py` fails to track expenses for raw materials on the buyer's side.
- **Risk**: Asymmetric financial logging that complicates GDP and profit analyses.
- **Solution**: Update Handler and `accounting.py` to ensure reciprocal debit/credit logging.

### ID: TD-ANALYTICS-DTO-BYPASS
- **Title**: Encapsulation Bypass in Analytics
- **Symptom**: `analytics_system.py` calls `agent.get_quantity` instead of reading snapshot.
- **Risk**: Purity Violation.
- **Solution**: Analytics should operate on immutable snapshots or DTOs.

### ID: TD-SYS-PERF-DEATH
- **Title**: O(N) Rebuild in Death System
- **Symptom**: `death_system.py` uses O(N) rebuild for `state.agents` dict.
- **Risk**: Performance degradation with many agents.
- **Solution**: Optimize agent removal to avoid full dictionary rebuilds.

---

## Lifecycle & Configuration
---
### ID: TD-LIFECYCLE-STALE
- **Title**: Persistent Queue Pollution (Stale IDs)
- **Symptom**: Transactions for dead agents linger in `inter_tick_queue`.
- **Risk**: Ghost transactions attempts bloat logs.
- **Solution**: Implement a `ScrubbingPhase` in `AgentLifecycleManager`.

### ID: TD-CONF-GHOST-BIND
- **Title**: Ghost Constant Binding (Import Time)
- **Symptom**: Constants locked at import time prevent effective runtime hot-swaps.
- **Risk**: Prevents dynamic tuning.
- **Solution**: Use a `ConfigProxy` that resolves values at access time.

---

## Testing & Quality Assurance
---
### ID: TD-TEST-TX-MOCK-LAG
- **Title**: Transaction Test Lag
- **Symptom**: `test_transaction_engine.py` mocks are out of sync with `ITransactionParticipant`.
- **Risk**: Test Flakiness.
- **Solution**: Update mocks to reflect current `ITransactionParticipant` interface.

### ID: TD-TEST-COCKPIT-MOCK
- **Title**: Cockpit 2.0 Mock Regressions
- **Symptom**: Old tests still reference `system_command_queue`.
- **Risk**: Silent Test Failure.
- **Solution**: Migrate tests to use the new `CommandService` interface.

### ID: TD-TEST-LIFE-STALE
- **Title**: Stale Lifecycle Logic in Tests
- **Symptom**: `test_engine.py` calls refactored `_handle_agent_liquidation` with old signatures.
- **Risk**: Test Breakdown.
- **Solution**: Update test assertions to match refactored Lifecycle DTOs.

### ID: TD-TEST-TAX-DEPR
- **Title**: Deprecated Tax API in Tests
- **Symptom**: `test_transaction_handlers.py` still uses `collect_tax`.
- **Risk**: Technical Debt.
- **Solution**: Update tests to use the new tax collection API.

---

## DX & Cockpit Operations
---
### ID: TD-UI-DTO-PURITY
- **Title**: UI Manual Deserialization
- **Symptom**: Cockpit UI uses dict indexing instead of Pydantic models for telemetry.
- **Risk**: Code Quality.
- **Solution**: Enforce DTO Purity in the frontend-backend interface.

### ID: TD-DX-AUTO-CRYSTAL
- **Title**: Crystallization Overhead
- **Symptom**: Manual steps required to register Gemini missions for distillation.
- **Risk**: DX Friction.
- **Solution**: Automate mission registration via a decorator/registry auto-discovery.

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

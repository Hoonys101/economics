# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singleton `government`. | **Medium**: Logic Fragility. | **Audit Confirmed** |
| **TD-ARCH-FIRM-COUP** | Architecture | **Parent Pointer Pollution**: `Firm` departments use `self.parent`, bypassing Orchestrator and risking circularity. | **High**: Structural Integrity. | Open |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Open |
| **TD-CRIT-FLOAT-CORE** | Finance | **Float Core**: `SettlementSystem` and `MatchingEngine` use `float` instead of `int` pennies. | **Critical**: Determinism. | **Audit Done** |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Handler**: `bailout`, `bond_issuance` tx types not registered. | **High**: Runtime Failure. | **Audit Done** |
| **TD-PROTO-MONETARY** | Transaction | **Monetary Protocol Violation**: `MonetaryTransactionHandler` uses `hasattr` instead of Protocols. | **Low**: Logic Fragility. | Open |
| **TD-AI-DEBT-AWARE** | AI | **Constraint Blindness**: AI spams spend intents at debt ceiling. Leads to log pollution and logic overhead. | **Medium**: AI Performance. | Open |
| **TD-ECON-WAR-STIMULUS** | Economic | **Fiscal Masking**: Stimulus prevents GDP 0 but masks fundamental wage-affordability imbalances. | **Medium**: Policy Fidelity. | Open |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync with `ITransactionParticipant`. | **Low**: Test Flakiness. | **Identified** |
| **TD-TEST-COCKPIT-MOCK** | Testing | **Cockpit 2.0 Mock Regressions**: Tests use deprecated `system_command_queue`. | **High**: Silent Test Failure. | **Identified** |
| **TD-TEST-LIFE-STALE** | Testing | **Stale Lifecycle Logic**: `test_engine.py` calls refactored `_handle_agent_liquidation`. | **High**: Test Breakdown. | **Identified** |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | **Identified** |
| **TD-LIFECYCLE-STALE** | Lifecycle | **Queue Pollution**: Missing scrubbing of `inter_tick_queue` after agent liquidation. | **Medium**: Determinism. | **Audit Done** |
| **TD-CONF-GHOST-BIND** | Config | **Ghost Constants**: Modules bind config values at import time, preventing runtime hot-swap. | **Medium**: Dynamic Tuning. | **Identified** |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-DEPR-STOCK-DTO** | Market | **Legacy DTO**: `StockOrder` is deprecated. Use `CanonicalOrderDTO`. | **Low**: Technical Debt. | Open |
| **TD-DX-AUTO-CRYSTAL** | DX / Ops | **Crystallization Overhead**: Manual Gemini Manifest registration required for session distillation. | **Medium**: DX Friction. | Open |
| **TD-ARCH-FIRM-MUTATION** | Agents | **In-place State Mutation**: `Firm` engines (`SalesEngine`, `BrandEngine`) mutate state objects, violating stateless mandate. | **Medium**: Structural Drift. | Open |
| **TD-MARKET-FLOAT-CAST** | Market | **Unsafe Quantization**: Direct `int()` cast in `matching_engine.py` instead of explicit rounding. | **Medium**: Precision Loss. | Open |
| **TD-MARKET-STRING-PARSE** | Market | **Brittle Key Parsing**: `StockMarket.get_price` splits strings to find `firm_id`. | **Low**: Logic Fragility. | Open |
| **TD-ANALYTICS-DTO-BYPASS** | Systems | **Encapsulation Bypass**: `analytics_system.py` calls `agent.get_quantity` instead of reading snapshot. | **Low**: Purity Violation. | Open |
| **TD-SYS-ACCOUNTING-GAP** | Systems | **Accounting Accuracy**: `accounting.py` misses tracking buyer expenses for raw materials. | **Medium**: Data Accuracy. | Open |
| **TD-SYS-PERF-DEATH** | Systems | **O(N) Rebuild**: `death_system.py` uses O(N) rebuild for `state.agents` dict. | **Low**: Performance. | Open |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)

### Architecture
---
#### ID: TD-ARCH-FIRM-COUP
- **Title**: Parent Pointer Pollution (Stateful Components)
- **Symptom**: `Department` classes in `Firm` initialized with `self.parent = firm`.
- **Risk**: Circular dependencies and "God-class" sprawl. Departments modify state in other departments directly.
- **Solution**: Refactor to stateless engines. Pass explicit DTOs to components.

### Finance & Transactions
---
#### ID: TD-CRIT-FLOAT-CORE (M&A Expansion)
- **Title**: M&A and Stock Market Float Violation
- **Symptom**: `MAManager` passes `float` offer prices to `SettlementSystem.transfer`, causing `TypeError`.
- **Risk**: Runtime crash during hostile takeovers or mergers.
- **Solution**: Quantize all M&A valuations using `round_to_pennies()` before settlement boundary.

---
#### ID: TD-INT-BANK-ROLLBACK
- **Title**: Rollback Coupling
- **Symptom**: Bank rollback logic dependent on `hasattr` implementation details.
- **Solution**: Move rollback logic to `TransactionProcessor` and use strict protocols.

### AI & Economic
---
#### ID: TD-AI-DEBT-AWARE
- **Title**: AI Constraint Blindness (Log Spam)
- **Symptom**: `DEBT_CEILING_HIT` spam in logs.
- **Risk**: Inefficient decision-making. AI fails to "learn" the barrier.
- **Solution**: Reward penalty for rejected spending intents. Add `current_debt_ratio` to AI input DTO.

---
#### ID: TD-ECON-WAR-STIMULUS
- **Title**: Fiscal Imbalance & Stimulus Dependency
- **Symptom**: `STIMULUS_TRIGGERED` occurs multiple times. Welfare > Tax.
- **Risk**: Artificially propped economy. Masking logic errors in Firm pricing/wage models.
- **Solution**: Implement progressive taxation and adjust Firm productivity-wage linkage.

### Lifecycle & Config
---
#### ID: TD-LIFECYCLE-STALE
- **Title**: Persistent Queue Pollution (Stale IDs)
- **Symptom**: Transactions for dead agents linger in `inter_tick_queue`.
- **Risk**: Ghost transactions attempts bloat logs.
- **Solution**: Implement a `ScrubbingPhase` in `AgentLifecycleManager` to purge invalid IDs from all queues.

---
#### ID: TD-CONF-GHOST-BIND
- **Title**: Ghost Constant Binding (Import Time)
- **Symptom**: `from config import MIN_WAGE` locks the value at import time.
- **Solution**: Use a `ConfigProxy` or `DynamicConfig` object that resolves values at access time.

### Recent Audit Findings (Watchtower)
---
#### ID: TD-ARCH-FIRM-MUTATION
- **Title**: Firm In-place State Mutation
- **Symptom**: `firm.py` passes `self.sales_state` to `BrandEngine` and `SalesEngine`, without capturing a return DTO.
- **Risk**: Violates the "Stateless Engine & Orchestrator" pattern.
- **Solution**: Refactor `BrandEngine` and `SalesEngine` to return `ResultDTOs`.

---
#### ID: TD-MARKET-FLOAT-CAST
- **Title**: Unsafe Quantization in Market Matching
- **Symptom**: `matching_engine.py` uses direct `int()` casting for `trade_total_pennies`.
- **Risk**: Potential calculation loss if quantities involve extremely small precision floats.
- **Solution**: Replace with explicit `round_to_pennies` logic.

---
#### ID: TD-MARKET-STRING-PARSE
- **Title**: Brittle ID Parsing in StockMarket
- **Symptom**: `StockMarket.get_price` splits `item_id` using strings to extract `firm_id`.
- **Risk**: Highly coupled to naming conventions, preventing scalable keys.
- **Solution**: Create dedicated DTO keys or pass tuples instead of raw strings.

---
#### ID: TD-SYS-ACCOUNTING-GAP
- **Title**: Missing Buyer Expense Tracking
- **Symptom**: `accounting.py` fails to track expenses for raw materials from the buyer's side.
- **Risk**: Asymmetric financial logging that complicates GDP and profit analyses.
- **Solution**: Update Handler and `accounting.py` to ensure reciprocal logging.

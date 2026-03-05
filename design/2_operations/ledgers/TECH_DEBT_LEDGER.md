# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

## 📑 Table of Contents
1. [Core Summary Table](#-core-summary-table)
2. [Architecture & Infrastructure](#architecture--infrastructure)
3. [Financial Systems (Finance & Transactions)](#financial-systems-finance--transactions)
4. [AI & Economic Simulation](#ai--economic-simulation)
5. [Market & Systems](#market--systems)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [DX & Cockpit Operations](#dx--cockpit-operations)

---

## 📊 Core Summary Table

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-PERF-GETATTR-LOOP** | Performance | **getattr Bottleneck**: Tight loops (100k+) using `getattr` for config lookups. | **High**: Runtime. | **RESOLVED** |
| **TD-FIN-MAGIC-BASE-RATE** | Finance | `FinanceSystem.issue_treasury_bonds` uses hardcoded `0.03`. | **Low**: Config. | Identified |
| **TD-ARCH-SSOT-BYPASS** | Architecture | **Protocol Evasion**: Direct mutation bypassing `SettlementSystem`. Linked to `AUDIT-S3-2A-SSOT-BYPASS`. | **CRITICAL**: SSoT. | **ACTIVE (SPEC)** |
| **TD-SYS-TRANSFER-HANDLER-GAP**| Finance | **Invisible P2P**: Generic `transfer` lacks handler. Linked to `AUDIT-S3-2B-TRANSFER-GAP`. | **CRITICAL**: Integrity. | **ACTIVE (SPEC)** |
| **TD-FIN-TX-HANDLER-HARDENING**| Finance | **Typed TX Errors**: Convert `Destination account does not exist` to typed `TransactionError` for clean rollbacks. | **High**: Stability. | **ACTIVE (PH22)** |
| **TD-WAVE3-DTO-SWAP** | DTO | **IndustryDomain Shift**: Replace `major` with `IndustryDomain` enum. | **Medium**: Structure. | **SPECCED** |
| **TD-WAVE3-TALENT-VEIL** | Agent | **Hidden Talent**: `EconStateDTO` missing `hidden_talent`. | **High**: Intent. | **RESOLVED** |
| **TD-WAVE3-MATCH-REWRITE** | Market | **Bargaining vs OrderBook**: Existing LaborMarket assumes sorting. | **High**: Economy. | **RESOLVED** |
| **TD-FIN-LIQUIDATION-DUST** | Finance | **Wealth Orphanage**: Pro-rata liquidation truncates dust pennies. | **Low**: Accuracy. | **RESOLVED** |
| **TD-REBIRTH-BUFFER-LOSS** | Architecture | **Buffer Flush Risk**: Crash during simulation results in loss of up to N ticks of data. | **Medium**: Data Loss. | **NEW (PH34)** |
| **TD-REBIRTH-TIMELINE-OPS** | Configuration | **Dynamic Shift Handling**: Config DTOs are immutable; re-generation needed during events. | **High**: Logic Complexity. | **RESOLVED** |
| **TD-BANK-RESERVE-CRUNCH** | Finance | **Bank Reserve Structural Constraint**: Bank 2 lacks reserves for bond issuance. | **High**: Macro. | Identified |
| **TD-ECON-ZOMBIE-FIRM** | Agent | **Zombie Firms**: Rapid extinction of basic_food firms. | **High**: Economy. | **RESOLVED** |
| **TD-FIN-NEGATIVE-M2** | Finance | **M2 Black Hole**: Aggregate M2 sums raw balances including overdrafts (Negative M2). | **CRITICAL**: Accounting. | **RESOLVED** |
| **TD-LIFECYCLE-GHOST-FIRM** | Lifecycle | **Ghost Firms**: Race condition; capital injection attempted before registration. | **CRITICAL**: Reliability. | **RESOLVED** |
| **TD-ARCH-ORPHAN-SAGA** | Architecture | **Orphaned Sagas**: Sagas holding stale references to dead/failed agents. | **High**: Integrity. | **RESOLVED** |
| **TD-TEST-MOCK-REGRESSION** | Testing | **Cockpit Stale Attr**: `system_command_queue` used in mocks. | **High**: Gap. | **RESOLVED** |
| **TD-ARCH-TX-INJECTION** | Architecture | **Transaction Injection Bypass**: `CentralBankSystem` directly mutating `WorldState.transactions`. | **High**: Purity. | **DEFERRED (TECH DEBT)** |
| **TD-FIN-FLOAT-INCURSION-RE**| Finance | **Recurring Float Incursion**: `monetary_ledger.py` using `float()` for debt principal. | **Critical**: Integrity. | **DEFERRED (TECH DEBT)** |
| **TD-ARCH-GOD-DTO** | Architecture | **SimulationState God DTO**: Monolithic dependency violating Interface Segregation. | **High**: Rigidity. | **ACTIVE (V2 AUDIT)** |
| **TD-TEST-MOCK-LEAK** | Testing | **[S3-1] MagicMock Leaks**: Reference cycles in God DTO causing OOM and GC hangs. | **High**: Reliability. | **RESOLVED** |
| **TD-ARCH-PROTOCOL-EVASION** | Architecture | **[S3-1] Protocol Evasion**: `hasattr()` usage in lifecycle logic (Ref: [AUDIT_PLATFORM_DEEP.md](file:///c:/coding/economics/reports/audits/AUDIT_PLATFORM_DEEP.md)). | **Medium**: Safety. | **ACTIVE** |
| **TD-ARCH-GOD-WORLDSTATE** | Architecture | **God Class Incursion**: `WorldState` holding service instances instead of pure data (Ref: [AUDIT_PLATFORM_DEEP.md](file:///c:/coding/economics/reports/audits/AUDIT_PLATFORM_DEEP.md)). | **High**: Purity. | **NEW** |
| **TD-ARCH-DTO-FRAGMENTATION** | Architecture | **Loose Typing**: Event queues using `Dict/Any` instead of DTOs (Ref: [AUDIT_PLATFORM_DEEP.md](file:///c:/coding/economics/reports/audits/AUDIT_PLATFORM_DEEP.md)). | **Medium**: Type Safety. | **NEW** |
| **TD-MEM-ENGINE-CYCLIC** | Memory | **Engine Lifecycle Memory Leak**: Cyclic references between `Simulation`, `TickOrchestrator`, and `ActionProcessor` prevented GC. | **High**: Reliability. | **RESOLVED (2026-03-04)** |
| **TD-MEM-TEARDOWN-HARDCODE** | Memory | **Hardcoded Teardown List**: `WorldState.teardown()` uses a 40-item string list; new systems risk silent leaks if not added. Consider `__dict__`-based dynamic teardown. | **Medium**: Maintenance. | **NEW (2026-03-04)** |
| **TD-MEM-TEARDOWN-HARDCODE** | Memory | **Hardcoded Teardown List**: `WorldState.teardown()` uses a 40-item string list; new systems risk silent leaks if not added. Consider `__dict__`-based dynamic teardown. | **Medium**: Maintenance. | **NEW (2026-03-04)** |
| **TD-MEM-TEARDOWN-INCOMPLETE** | Memory | **Incomplete Teardown**: `bank`, `central_bank`, `stock_market` missing from `WorldState.teardown()` subsystems list. | **High**: Memory Leak. | **NEW (2026-03-04)** |
| **TD-MEM-REGISTRY-INPLACE** | Memory | **List Reference Leak**: `AgentRegistry.purge_inactive()` overwrites `households`/`firms` lists instead of in-place `[:]` modification; cached references become stale. | **Medium**: Data Integrity. | **NEW (2026-03-04)** |
| **TD-MEM-INACTIVE-TTL** | Memory | **Unbounded Inactive Agents**: `AgentRegistry.inactive_agents` grows without eviction; needs TTL or max-size policy for long runs. | **Medium**: Memory. | **NEW (2026-03-04)** |
| **TD-LIFECYCLE-AGENT-DISPOSE** | Lifecycle | **Agent Dispose Pattern**: `DemographicManager` directly clears agent fields (`_econ_state`, `portfolio`); should delegate to `Agent.dispose()` method for encapsulation. | **High**: Encapsulation. | **NEW (2026-03-04)** |
| **TD-ARCH-LATE-RESET-DELEGATE** | Architecture | **Late-Reset Delegation**: `TickOrchestrator._finalize_tick` manually clears `world_state` queues; consider delegating to a `WorldState.flush_transient_queues()` method. | **Low**: Encapsulation. | **NEW (2026-03-04)** |
| **TD-TEST-MOCK-SPEC-ENFORCE** | Testing | **Global Mock Spec Enforcement**: Bare `MagicMock()` in `tests/utils/mocks.py` caused Mock Drift. Need to enforce `spec=<Interface>` on all global test mocks via linting or refactor. | **Medium**: Test Integrity. | **NEW (2026-03-04)** |
| **TD-ECON-MASLOW-STATIC** | AI/Economy | **Maslow Static Weights**: `NeedsEngine` uses static `desire_weights` instead of dynamic suppression formula $W_{L+1}$. Blocks emergent Veblen/network effects. | **Medium**: Economy. | **NEW (ROADMAP)** |
| **TD-ECON-SIGNALING-DRIFT** | AI/Economy | **Signaling→HumanCapital Drift**: Education modeled as direct productivity enhancement instead of labor market signal. `HRDepartment` missing Halo Effect logic. | **Medium**: Economy. | **NEW (ROADMAP)** |
| **TD-TEST-GC-MOCK-EXPLOSION** | Testing | **GC Hang due to Mocks**: Massive `MagicMock` graphs during initialization cause memory spikes and tens of seconds of GC pause in tests. | **CRITICAL**: Developer Velocity. | **RESOLVED (2026-03-05)** |
| **TD-TEST-MOCK-BYPASS** | Testing | **Transaction Metadata Duct-tape**: Government tests bypass `TransactionMetadataDTO` using `getattr(metadata, "original_metadata")`. | **Low**: Stability. | **NEW** |
| **TD-ARCH-HEAVY-FINANCE-API** | Architecture | **Heavy Finance API**: `modules.finance.api` (1200+ lines) causes Gemini OOM by pulling Gov/HR. | **High**: Rigidity. | **NEW (2026-03-05)** |

---

## Architecture & Infrastructure
---
### ID: TD-BANK-RESERVE-CRUNCH
- **Title**: Bank Reserve Structural Constraint
- **Symptom**: `BOND_ISSUANCE_FAILED` because Bank 2 only has 1,000,000 pennies in reserves but tries to issue bonds for 8M - 40M.
- **Risk**: Macroeconomic scale of the government is completely stunted because central/commercial banks lack fractional elasticity.
- **Solution**: Implement proper fractional reserve system or inject more liquidity early on.
- **Status**: NEW

### ID: TD-ARCH-SHARED-WALLET-RISK
- **Title**: Shared Wallet Object Identity Risk
- **Symptom**: Spouses in a Household share the same `Wallet` memory instance. Previously caused M2 double counting.
- **Risk**: Latent reference risk for universal effects (UBI, index adjustments).
- **Solution**: Mid-term migration to `AccountID` pointer mapping or `JointAccount` entity.
- **Status**: **MITIGATED** (Wallet Identity Deduplication implemented in PH34)

### ID: TD-REBIRTH-BUFFER-LOSS
- **Title**: Buffer Flush Risk
- **Symptom**: Crash during simulation results in loss of up to N ticks of data.
- **Risk**: Data Loss.
- **Solution**: Periodic checkpointing of simulation state.
- **Status**: NEW (PH34)

### ID: TD-ARCH-ORPHAN-SAGA
- **Title**: Orphaned Saga References
- **Symptom**: `SAGA_SKIP | Saga ... missing participant IDs`.
- **Risk**: Sagas consume compute cycles for dead agents; memory leaks; state corruption in subsequent ticks.
- **Audit Update (PH21)**: Confirmed `SAGA_SKIP | Saga ... missing participant IDs`. Sagas become "Orphaned Processes" consuming cycles without effect.
- **Solution**: Implement `SagaCaretaker` to purge dead references or use weak references for participants.
- **Status**: **RESOLVED** (Phase 35 Stabilization - Ref: `design/3_work_artifacts/reports/inbound/feat-audit-structural-2883268932289924915__forensic_audit_ph21_report.md`)

### ID: TD-ARCH-GOD-DTO
- **Title**: SimulationState God DTO
- **Symptom**: `SimulationState` aggregates 40+ unrelated fields, forcing systems to depend on the entire simulation engine.
- **Risk**: High architectural rigidity; any change in the engine triggers side-effects in unrelated systems like `DeathSystem`.
- **Solution**: Segregate into scoped `DomainContext` protocols (e.g., `IDeathContext`).
- **Status**: ACTIVE

### ID: TD-ARCH-PROTOCOL-EVASION
- **Title**: Protocol Evasion via `hasattr()`
- **Symptom**: `DeathSystem.py` frequently uses `hasattr()` to check for `hr_state` or `get_agent_banks`.
- **Risk**: Type safety violations; "Duck Typing" makes the system fragile during refactors.
- **Solution**: Harden protocols (`ISettlementSystem`, `IFirm`) to include these missing methods.
- **Status**: ACTIVE

### ID: TD-ARCH-GOD-CLASS
- **Title**: God Classes in Core Agents
- **Symptom**: `simulation/firms.py` (1800+ lines) and `core_agents.py` (1200+ lines) violate Single Responsibility Principle.
- **Risk**: Maintenance nightmare; high cognitive load for new developers; fragile state management.
- **Solution**: Decompose into trait-based Engines (e.g., `BirthComponent`, `EconComponent`).
- **Status**: NEW (AUDIT)

### ID: TD-SYS-ABS-LEAK
- **Title**: Abstraction Leaks in System Services
- **Symptom**: `WelfareService` and `GovernmentSystem` pass raw `Household` objects between modules.
- **Risk**: Circular dependencies; tight coupling to simulation internals.
- **Solution**: Ensure all inter-module communication uses strictly typed DTOs (e.g., `WelfareCandidateDTO`).
- **Status**: NEW (AUDIT)

### ID: TD-ARCH-HEAVY-FINANCE-API
- **Title**: Heavy Dependency Bloat in `modules.finance.api`
- **Symptom**: Gemini-CLI OOM failures when analyzing small modules like `AccountRegistry`; 1200+ line API file pulling in unrelated domain modules (Government, HR, Saga).
- **Risk**: High architectural rigidity; unmanageable context size for AI agents; violating Interface Segregation Principle.
- **Solution**: Segregate finance API into granular functional protocols; move concrete DTOs to sub-modules; ensure core finance interfaces do not depend on high-level domain services.
- **Status**: NEW (2026-03-05)

---

## Financial Systems (Finance & Transactions)
---
### ID: TD-FIN-MAGIC-BASE-RATE
- **Title**: Magic Number for Base Interest Rate
- **Symptom**: `FinanceSystem.issue_treasury_bonds` uses a hardcoded `0.03` fallback when no banks are available.
- **Risk**: Lack of configurability and transparency.
- **Solution**: Define a named constant in `modules.finance.constants`.
- **Status**: Identified

### ID: TD-FIN-LIQUIDATION-DUST
- **Title**: Wealth Orphanage (Dust Pennies)
- **Symptom**: Pro-rata liquidation truncates dust pennies.
- **Risk**: Precision accuracy.
- **Solution**: Allocate remainder to the government or estate registry.
- **Status**: SPECCED (PH33)

### ID: TD-FIN-NEGATIVE-M2
- **Title**: M2 Money Supply "Black Hole"
- **Symptom**: `MONEY_SUPPLY_CHECK` reaches large negative values (e.g. -99,096,426 by Tick 55).
- **Risk**: Economic calculations (GDP, inflation) become meaningless; accounting violation of Zero-Sum Integrity.
- **Audit Update (PH21)**: Debt (overdrafts) masks liquidity. M2 should equal `Sum(max(0, balance_i))`.
- **Solution**: Modify `calculate_total_money` to sum `max(0, balance)` and track negative balances as `SystemDebt`.
- **Status**: **RESOLVED** (Phase 35 Stabilization - Ref: `design/3_work_artifacts/reports/inbound/feat-audit-structural-2883268932289924915__forensic_audit_ph21_report.md`)

### ID: TD-FIN-FLOAT-RESIDUE
- **Title**: Float Price Residue in Transaction model
- **Symptom**: `Transaction` dataclass still defines `price: float` despite integer penny migration.
- **Risk**: Confusion between `price: float` (dollars) and `total_pennies: int` (pennies), leading to conversion errors.
- **Solution**: Completely remove `price: float` or rename it to `price_display: float` and mark as secondary.
- **Status**: NEW (AUDIT)

### ID: TD-FIN-TX-HANDLER-HARDENING
- **Title**: Transaction Handler Hardening (Typed Errors)
- **Symptom**: Settlement failures (e.g. invalid destinations) are treated as generic runtime engine errors.
- **Risk**: Prevents graceful catching and rolling back of specific failed transactions without aborting the broader engine sequence.
- **Audit Update (PH21)**: `TransactionEngine` must validate `recipient_id` existence before processing. Convert "Destination account does not exist" to typed `TransactionError`.
- **Solution**: Introduce `TransactionError` hierarchy. Implement fail-fast destination checks in `Bank` registry.
- **Status**: **ACTIVE** (Phase 22 Spec)

### ID: TD-FIN-FLOAT-INCURSION
- **Title**: Float Incursion during Ledger Metadata Parsing
- **Symptom**: Ledger components using `float()` to parse monetary values from metadata dictionaries.
- **Risk**: Float precision errors accumulating to violate Zero-Sum integrity (e.g. creating or destroying dust pennies).
- **Solution**: Enforce strict `int()` casting for all monetary values in parsing logic and DTOs.
- **Status**: **RESOLVED** (Enforced via `CommandBatchDTO` and strict `int` checks)

### ID: TD-ARCH-TX-INJECTION
- **Title**: Transaction Injection State Mutation Bypass
- **Symptom**: `CentralBankSystem` accepts a direct reference to `WorldState.transactions` and appends to it.
- **Risk**: Violates "Stateless Engine" principle; breaks side-effect tracking; hard to audit.
- **Resolution**: Refactor to return `Transaction` objects for orchestrator collection.
- **Status**: **DEFERRED** (Planned for SSoT Wave 2)

### ID: TD-FIN-FLOAT-INCURSION-RECUR
- **Title**: Recurring Float Incursion in Ledger
- **Symptom**: `monetary_ledger.py` uses `float(repayment_details["principal"])`.
- **Risk**: Precision loss in debt repayment calculations.
- **Resolution**: Use `int()` or dedicated penny-safe parser.
- **Status**: **DEFERRED** (Planned for SSoT Wave 1.1)

### ID: TD-ECON-GHOST-MONEY
- **Title**: Ghost Money from Implicit System Operations
- **Symptom**: M2 (Total Money Supply) calculations showed leakage during LLR injections.
- **Risk**: Treasury/Central Bank operations were un-auditable.
- **Solution**: Implemented **Transaction Injection Pattern** where `CentralBankSystem` directly appends to global ledger.
- **Status**: **RESOLVED** (Merged in Settlement Sync)

---

## AI & Economic Simulation
---
### ID: TD-ECON-ZOMBIE-FIRM
- **Title**: Rapid Extinction of basic_food Firms
- **Symptom**: Firms (e.g., Firm 121, 122) trigger `FIRE_SALE` continually, go `ZOMBIE` (cannot afford wage), and then `FIRM_INACTIVE` within the first 30 ticks.
- **Risk**: Destruction of the simulation economy early in the run.
- **Solution**: Re-tune pricing constraints, initial reserves, or labor cost expectations specifically for essential goods.
- **Status**: NEW

### ID: TD-LIFECYCLE-GHOST-FIRM
- **Title**: Ghost Firm Atomic Startup Failure
- **Symptom**: `SETTLEMENT_FAIL | Engine Error: Destination account does not exist: [120, 123, 124]`.
- **Risk**: Investor funds debited without firm capitalization; "Zombie" firms with 0 capital.
- **Audit Update (PH21)**: Race condition where Capital Injection is attempted *before* Firm Agent registration in Bank/WorldState.
- **Solution**: Implement atomic `FirmFactory` ensuring registration and bank account opening before injection.
- **Status**: **RESOLVED** (Phase 35 Stabilization - Ref: `design/3_work_artifacts/reports/inbound/feat-audit-structural-2883268932289924915__forensic_audit_ph21_report.md`)

---

## Testing & Quality Assurance
---
### ID: TD-TEST-MOCK-REGRESSION
- **Title**: Cockpit Mock Attribute Regressions
- **Symptom**: Tests (e.g. `test_state_synchronization.py`) use deprecated `system_command_queue` on `WorldState` mocks.
- **Risk**: Silent coverage loss; Cockpit commands are ignored in tests but tests pass.
- **Solution**: Update mocks to use `system_commands` (list).

### ID: TD-TEST-LIFECYCLE-STALE-MOCK
- **Title**: Stale Lifecycle Method Access
- **Symptom**: `tests/system/test_engine.py` attempts to call `_handle_agent_liquidation` which was refactored into `DeathSystem`.
- **Risk**: Test failures in the system engine suite.
- **Solution**: Realign test logic to use `DeathSystem` or mock the new lifecycle components accurately.

### ID: TD-TEST-DTO-MOCKING
- **Title**: DTO Mocking Anti-Pattern
- **Symptom**: Tests return `MagicMock` instead of real DTOs (e.g. `Transaction`), bypassing type checks and schema validation.
- **Risk**: Hidden regressions where code assumes specific DTO attributes or behavior that `MagicMock` silently absorbs.
- **Solution**: Use real DTOs or `dataclass` instances in test fixtures.
- **Status**: NEW (AUDIT)

---

### ID: TD-PERF-GETATTR-LOOP
- **Title**: getattr Bottleneck in Tight Loops
- **Symptom**: Significant performance degradation in `TaxService.collect_wealth_tax` when processing 100k+ agents.
- **Risk**: Simulation runtime becomes unsustainable as population scales.
- **Solution**: Cache config values as local instance variables during `__init__` to avoid `getattr` overhead in loops.
- **Status**: **RESOLVED** (Merged in `fix/tax-service-config-caching`)

---

> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

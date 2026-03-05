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
| **TD-PERF-GETATTR-LOOP** | Performance | **getattr Bottleneck**: Proxy lookup overhead in tight loops (100k+) for `sim.bank`, `sim.agents`. | **High**: Runtime. | **RESOLVED (2026-03-05)** |
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
| **TD-TEST-MOCK-REGRESSION** | Testing | **Cockpit Stale Attr**: `system_command_queue` used in mocks. | **High**: Gap. | **RESOLVED** |
| **TD-ARCH-TX-INJECTION** | Architecture | **Transaction Injection Bypass**: `CentralBankSystem` directly mutating `WorldState.transactions`. | **High**: Purity. | **DEFERRED (TECH DEBT)** |
| **TD-FIN-FLOAT-INCURSION-RE**| Finance | **Recurring Float Incursion**: `monetary_ledger.py` using `float()` for debt principal. | **Critical**: Integrity. | **RESOLVED (2026-03-05)** |
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
| **TD-MEM-GLOBAL-WALLET-LEAK** | Memory | **Global Wallet Leak**: `GLOBAL_WALLET_LOG` unbounded growth over simulation ticks. | **CRITICAL**: Reliability. | **RESOLVED (2026-03-05)** |
| **TD-MEM-AGENT-ENGINE-BLOAT** | Memory | **O(N) Engine Allocation**: Stateless engines created per household agent. | **High**: Scaling. | **RESOLVED (Household)** |
| **TD-MEM-FIRM-SINGLETON-DEBT** | Memory | **Firm Engine Singletoning**: Firm `CorporateManager` still uses per-instance config, blocking singleton pattern. | **Medium**: Scaling. | **NEW (TD-20260305)** |
| **TD-ARCH-HEAVY-FINANCE-API** | Architecture | **Heavy Finance API**: `modules.finance.api` (1200+ lines) causes Gemini OOM by pulling Gov/HR. | **High**: Rigidity. | **NEW (2026-03-05)** |
| **TD-MEM-GLOBAL-AUDIT-LEAK** | Memory | **Global Audit Leaks**: `GLOBAL_WALLET_LOG` never clears, appending thousands of DTOs and causing `MemoryError` even at 20 agents. | **CRITICAL**: Memory. | **NEW (AUDIT)** |
| **TD-ARCH-TEST-HANG-PROXY** | Architecture/Testing | **Init Hang via Proxy Overhead**: `Simulation.__getattr__` delegation combined with `isinstance` checks on protocols causes O(N) slowing "hang" during agent registration. | **High**: Runtime/Tests. | **NEW (AUDIT)** |
| **TD-TEST-HEAVY-INFO-LOGS** | Testing | **Massive Test I/O Overhead**: `INFO` level logging captures every micro-transaction across 1000+ tests, causing 35% of tests to exceed 10mins. | **Medium**: Test Speed. | **NEW (AUDIT)** |

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

---

### ID: TD-PERF-GETATTR-LOOP
- **Title**: God Class Proxy Lookup Overhead in Deep Loops
- **Symptom**: Significant performance degradation in `TaxService` and `SimulationInitializer` during 10k+ agent registration.
- **Risk**: Simulation runtime becomes unsustainable; initialization hang.
- **Resolution**: Implemented **Local Reference Caching** pattern. Dependencies like `sim.agents`, `sim.bank`, and `sim.settlement_system` are cached as local variables before entering loops.
- **Lesson**: Interface proxies (God Class `__getattr__`) have high overhead in Python; always cache references for deep loops.
- **Status**: **RESOLVED** (Phase A - 2026-03-05)

### ID: TD-FIN-REGISTRY-CONCURRENCY
- **Title**: AccountRegistry Thread-Safety Risks
- **Symptom**: Potential silent state corruption or dictionary iteration errors in `AccountRegistry` during multi-threaded initialization.
- **Cause**: Non-atomic mutations of `defaultdict(set)` across threads.
- **Resolution**: Introduced `threading.RLock()` to protect all state mutations and retrievals. Used `RLock` to safely handle re-entrant calls between methods.
- **Lesson**: Shared registries must be thread-safe from inception.
- **Status**: **RESOLVED** (Phase B - 2026-03-05)

---

> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

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
| **TD-FIN-MAGIC-BASE-RATE** | Finance | `FinanceSystem.issue_treasury_bonds` uses hardcoded `0.03`. | **Low**: Config. | Identified |
| **TD-WAVE3-DTO-SWAP** | DTO | **IndustryDomain Shift**: Replace `major` with `IndustryDomain` enum. | **Medium**: Structure. | **SPECCED** |
| **TD-WAVE3-TALENT-VEIL** | Agent | **Hidden Talent**: `EconStateDTO` missing `hidden_talent`. | **High**: Intent. | **SPECCED** |
| **TD-WAVE3-MATCH-REWRITE** | Market | **Bargaining vs OrderBook**: Existing LaborMarket assumes sorting. | **High**: Economy. | **SPECCED** |
| **TD-FIN-LIQUIDATION-DUST** | Finance | **Wealth Orphanage**: Pro-rata liquidation truncates dust pennies. | **Low**: Accuracy. | **SPECCED (PH33)** |
| **TD-REBIRTH-BUFFER-LOSS** | Architecture | **Buffer Flush Risk**: Crash during simulation results in loss of up to N ticks of data. | **Medium**: Data Loss. | **NEW (PH34)** |
| **TD-REBIRTH-TIMELINE-OPS** | Configuration | **Dynamic Shift Handling**: Config DTOs are immutable; re-generation needed during events. | **High**: Logic Complexity. | **NEW (PH34)** |
| **TD-BANK-RESERVE-CRUNCH** | Finance | **Bank Reserve Structural Constraint**: Bank 2 lacks reserves for bond issuance. | **High**: Macro. | NEW |
| **TD-ECON-ZOMBIE-FIRM** | Agent | **Zombie Firms**: Rapid extinction of basic_food firms. | **High**: Economy. | NEW |
| **TD-FIN-NEGATIVE-M2** | Finance | **M2 Black Hole**: Aggregate M2 sums raw balances including overdrafts (Negative M2). | **Critical**: Accounting. | **NEW (AUDIT)** |
| **TD-LIFECYCLE-GHOST-FIRM** | Lifecycle | **Ghost Firms**: Race condition; capital injection attempted before registration. | **High**: Reliability. | **NEW (AUDIT)** |
| **TD-ARCH-ORPHAN-SAGA** | Architecture | **Orphaned Sagas**: Sagas holding stale references to dead/failed agents. | **Medium**: Memory. | **NEW (AUDIT)** |
| **TD-TEST-MOCK-REGRESSION** | Testing | **Cockpit Stale Attr**: `system_command_queue` used in mocks. | **High**: Gap. | **NEW (AUDIT)** |
| **TD-FIN-FLOAT-INCURSION** | Finance | **Float Incursion in Ledger**: Parsing metadata using `float()` risks integer math integrity. | **Critical**: Integrity. | **RESOLVED** |
32: | **TD-SYS-IMPLICIT-REGISTRY-LOOKUP** | Architecture | **Duck-Typed Agent Resolution**: `MonetaryLedger` uses `hasattr` to find registries. | **Medium**: Rigidity. | **NEW** |
| **TD-TEST-DTO-MOCKING** | Testing | **DTO Mocking Anti-Pattern**: Replacing DTOs with MagicMocks breaks type safety and stability. | **Medium**: Quality. | **NEW (AUDIT)** |
| **TD-ARCH-GOD-DTO** | Architecture | **SimulationState God DTO**: Monolithic dependency violating Interface Segregation. | **High**: Rigidity. | **NEW (AUDIT)** |
| **TD-ARCH-PROTOCOL-EVASION** | Architecture | **Protocol Evasion**: `hasattr()` usage in lifecycle logic bypasses Protocol Purity. | **Medium**: Safety. | **NEW (AUDIT)** |

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
- **Solution**: Implement `SagaCaretaker` to purge dead references or use weak references for participants.
- **Status**: NEW (AUDIT)

### ID: TD-ARCH-GOD-DTO
- **Title**: SimulationState God DTO
- **Symptom**: `SimulationState` aggregates 40+ unrelated fields, forcing systems to depend on the entire simulation engine.
- **Risk**: High architectural rigidity; any change in the engine triggers side-effects in unrelated systems like `DeathSystem`.
- **Solution**: Segregate into scoped `DomainContext` protocols (e.g., `IDeathContext`).
- **Status**: NEW (AUDIT)

### ID: TD-ARCH-PROTOCOL-EVASION
- **Title**: Protocol Evasion via `hasattr()`
- **Symptom**: `DeathSystem.py` frequently uses `hasattr()` to check for `hr_state` or `get_agent_banks`.
- **Risk**: Type safety violations; "Duck Typing" makes the system fragile during refactors.
- **Solution**: Harden protocols (`ISettlementSystem`, `IFirm`) to include these missing methods.
- **Status**: NEW (AUDIT)

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
- **Symptom**: `MONEY_SUPPLY_CHECK` reaches large negative values (e.g. -99M).
- **Risk**: Economic calculations (GDP, inflation) become meaningless; accounting violation.
- **Solution**: Modify `calculate_total_money` to sum `max(0, balance)` and track negative balances as `SystemDebt`.
- **Status**: NEW (AUDIT)

### ID: TD-FIN-FLOAT-RESIDUE
- **Title**: Float Price Residue in Transaction model
- **Symptom**: `Transaction` dataclass still defines `price: float` despite integer penny migration.
- **Risk**: Confusion between `price: float` (dollars) and `total_pennies: int` (pennies), leading to conversion errors.
- **Solution**: Completely remove `price: float` or rename it to `price_display: float` and mark as secondary.
- **Status**: NEW (AUDIT)

### ID: TD-FIN-FLOAT-INCURSION
- **Title**: Float Incursion during Ledger Metadata Parsing
- **Symptom**: Ledger components using `float()` to parse monetary values from metadata dictionaries.
- **Risk**: Float precision errors accumulating to violate Zero-Sum integrity (e.g. creating or destroying dust pennies).
- **Solution**: Enforce strict `int()` casting for all monetary values in parsing logic and DTOs.
- **Status**: **RESOLVED** (Enforced via `CommandBatchDTO` and strict `int` checks)

### ID: TD-SYS-IMPLICIT-REGISTRY-LOOKUP
- **Title**: Duck-Typed Agent Resolution in Ledger
- **Symptom**: `MonetaryLedger._resolve_agent` utilizes `hasattr` chains to find `agent_registry` from `settlement_system` or `time_provider`.
- **Risk**: Weak dependency coupling; overloads `time_provider` with unintended domain responsibilities.
- **Solution**: Explicitly inject `IAgentRegistry` into `MonetaryLedger` and remove the fallback chain logic.
- **Status**: NEW

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
- **Symptom**: `SETTLEMENT_FAIL | Engine Error: Destination account does not exist`.
- **Risk**: Investor funds debited without firm capitalization; "Zombie" firms with 0 capital.
- **Solution**: Implement atomic `FirmFactory` ensuring registration and bank account opening before injection.
- **Status**: NEW (AUDIT)

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

> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

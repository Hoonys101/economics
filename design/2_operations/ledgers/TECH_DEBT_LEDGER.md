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
| **TD-TEST-MOCK-REGRESSION** | Testing | **Cockpit Stale Attr**: `system_command_queue` used in mocks. | **High**: Gap. | **NEW (AUDIT)** |
| **TD-TEST-LIFECYCLE-STALE-MOCK** | Testing | **Stale Method Access**: `test_engine.py` calls deprecated methods. | **Medium**: Failure. | **NEW (AUDIT)** |

---

## Architecture & Infrastructure
---
### ID: TD-BANK-RESERVE-CRUNCH
- **Title**: Bank Reserve Structural Constraint
- **Symptom**: `BOND_ISSUANCE_FAILED` because Bank 2 only has 1,000,000 pennies in reserves but tries to issue bonds for 8M - 40M.
- **Risk**: Macroeconomic scale of the government is completely stunted because central/commercial banks lack fractional elasticity.
- **Solution**: Implement proper fractional reserve system or inject more liquidity early on.
- **Status**: NEW

### ID: TD-REBIRTH-BUFFER-LOSS
- **Title**: Buffer Flush Risk
- **Symptom**: Crash during simulation results in loss of up to N ticks of data.
- **Risk**: Data Loss.
- **Solution**: Periodic checkpointing of simulation state.
- **Status**: NEW (PH34)

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

---

> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

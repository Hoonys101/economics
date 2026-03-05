# WO-IMPL-FIN-M2-CALC-FIX: Refined M2 Calculation Definition

## 1. [Architectural Insights]

### Consolidated M2 Logic
The M2 calculation logic has been consolidated into `SettlementSystem.get_total_m2_pennies`. This method now serves as the Single Source of Truth (SSoT) for the money supply held by the public. The logic explicitly iterates over active and estate agents, summing their `balance_pennies` (or `get_balance(DEFAULT_CURRENCY)`), while strictly excluding:
- **System Agents**: `ID_SYSTEM`, `ID_CENTRAL_BANK`, `ID_ESCROW`, `ID_PUBLIC_MANAGER`.
- **Commercial Banks**: Agents implementing the `IBank` protocol.

This definition ensures that M2 represents **Money held by the Non-Bank Public**. Bank Reserves (assets) and System funds are correctly treated as M0 or outside the money supply, eliminating the previous double-counting where both "Circulating Cash" (which included deposits in wallet form) and "Total Deposits" (reported by banks) were summed.

### Deduplication Strategy
To prevent M2 inflation due to race conditions or lifecycle transitions (e.g., death), the new implementation uses a `processed_ids` set to ensure each agent is counted exactly once, even if they appear in both `AgentRegistry` and `EstateRegistry` during a tick transition.

### Verification Alignment
The `audit_total_m2` method has been updated to verify the system's actual M2 (calculated via the new logic) against the `MonetaryLedger`'s expected M2. This aligns the forensic tools with the architectural definition.

## 2. [Regression Analysis]

### Broken Tests & Fixes
Two unit tests failed initially because they relied on the old, double-counting definition of M2 (M2 = Cash + Deposits + Reserves).
1.  `tests/unit/simulation/systems/test_audit_total_m2.py`: `test_audit_total_m2_logic` expected M2 to be 300 (Sum of all assets). It failed because the new logic correctly excludes the Bank (50) and does not double-count deposits (200), resulting in 100 (Household Balance).
    *   **Fix**: Updated the expectation to 100 and the log message assertion to match the new format.
2.  `tests/unit/systems/test_settlement_security.py`: `test_audit_total_m2_strict_protocol` expected 5200. It failed because the new logic returns 200 (Public Agent Balance).
    *   **Fix**: Updated the expectation to 200.

### Forensics Findings
`operation_forensics.py` reported a high M2 Delta (~1.1B) even after the fix. Analysis revealed:
- **Current M2 (~1.9B)**: Matches the sum of Household balances (verified via logs). This confirms the calculation logic is correct (Single Count).
- **Expected M2 (~0.98B)**: Matches the Baseline set at Tick 0.
- **Delta (+1B)**: Represents unrecorded monetary expansion during the simulation (likely Bank -> Public flows such as loans or interest payments that are not capturing `record_monetary_expansion`). While the calculation definition is now correct, the *tracking* of money creation in the wider simulation needs future attention (out of scope for this calculation fix).

## 3. [Test Evidence]

### Unit & Integration Tests
All 1064 tests passed successfully.

```bash
$ python -m pytest tests/
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.3, cov-6.0.0, anyio-4.8.0, mock-3.14.0, hypothesis-6.125.2
collected 1071 items

tests/unit/simulation/systems/test_audit_total_m2.py .                     [  0%]
tests/unit/systems/test_settlement_security.py .                             [  0%]
...
tests/unit/utils/test_config_factory.py ..                                   [100%]

================ 1064 passed, 7 skipped, 1 warning in 14.17s =================
```

### Operation Forensics Verification
Manually verified `SettlementSystem` exclusion logic using `operation_forensics.py` logs:
```
2026-02-25 01:50:00 [WARNING] modules.system.builders.simulation_builder: M2_CALC | High Balance Agent Included: 100 (Type: Household) = 108928810
...
2026-02-25 01:50:00 [WARNING] modules.system.builders.simulation_builder: MONEY_SUPPLY_CHECK | Current: 1956939635, Expected: 987302155, Delta: 969637480
```
The "Current" value matches the sum of the logged Household balances, confirming that Bank/System agents are correctly excluded and double-counting is eliminated.

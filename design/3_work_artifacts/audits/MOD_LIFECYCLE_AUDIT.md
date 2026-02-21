I will now generate the Technical Audit Report for Module C: Lifecycle & Saga Reliability, tracing the root causes of the Ghost Firm race condition and Saga Participant Drift.

# Module C Audit: Lifecycle & Saga Reliability

## Executive Summary
The audit of the lifecycle and Saga orchestration logic reveals critical timing and normalization failures. `TD-ARCH-STARTUP-RACE` is confirmed as a registration-order conflict in `firm_management.py`, while `TD-FIN-SAGA-ORPHAN` results from fragile DTO/dict branching in the `SagaOrchestrator`.

## Detailed Analysis

### 1. Root Cause Analysis: Ghost Firm Race Condition (TD-ARCH-STARTUP-RACE)
- **Status**: ⚠️ Partial Implementation (Legacy ordering)
- **Evidence**: `simulation\systems\firm_management.py:L138-144` executes `settlement_system.transfer` for capital injection **before** the firm is registered in the simulation's agent map at `L152`.
- **Diagnosis**: The `SettlementSystem` performs a lookup on the `credit_agent` ID. Because the firm is not yet in the `simulation.agents` registry or the Bank's account index, the transfer fails. The firm object exists in memory but is a "Ghost" to the financial system.

### 2. Root Cause Analysis: Saga Participant Drift (TD-FIN-SAGA-ORPHAN)
- **Status**: ❌ Missing Strict DTO Normalization
- **Evidence**: `modules\finance\sagas\orchestrator.py:L70-93` attempts to handle both `dict` and `HousingTransactionSagaStateDTO`. 
- **Diagnosis**: 
    - The ID extraction logic at `L85-93` is prone to failure if the `buyer_context` is a `SimpleNamespace` (injected at `L79`) rather than a full `HouseholdSnapshotDTO`.
    - If `buyer_id` or `seller_id` extraction fails, the loop triggers `SAGA_SKIP` at `L94`.
    - `TD-FIN-SAGA-ORPHAN` occurs because participant IDs are stored inconsistently between dictionary keys (`buyer_id`) and DTO attributes (`buyer_context.household_id`).

### 3. Root Cause Analysis: Rollback Coupling (TD-INT-BANK-ROLLBACK)
- **Status**: ⚠️ Partial (Technical Debt identified in `TECH_DEBT_LEDGER.md`)
- **Diagnosis**: Bank rollback logic currently relies on `hasattr` implementation details instead of the `IFinancialEntity` protocol (defined in `modules\finance\api.py:L33`). This causes an abstraction leak where the bank must "know" the internal structure of the agents it interacts with.

---

## Solution: Atomic Onboarding Protocol
To resolve these issues, the system must transition to an atomic lifecycle sequence that ensures "Registration before Transaction."

### 1. DTO Normalization
All Sagas must be converted to `HousingTransactionSagaStateDTO` at the `submit_saga` entry point. The `dict` fallback in `process_sagas` must be deprecated to ensure ID retrieval is deterministic (`saga.buyer_id` vs `saga.seller_id`).

### 2. Lifecycle Reordering (Pseudo Code)
```python
# Reordered spawn_firm in simulation\systems\firm_management.py
def spawn_firm(self, simulation, founder):
    # 1. Initialization
    new_firm = self._create_instance(...)
    
    # 2. ATOMIC REGISTRATION (Fix for TD-ARCH-STARTUP-RACE)
    simulation.agents[new_firm.id] = new_firm  # Immediate registry entry
    simulation.settlement_system.register_account(bank_id, new_firm.id)
    
    # 3. ENDOWMENT (Safe to execute now)
    success = settlement_system.transfer(founder, new_firm, startup_capital, ...)
    
    # 4. FINALIZATION
    if success:
        simulation.firms.append(new_firm)
        return new_firm
    else:
        # Cleanup if transfer fails
        del simulation.agents[new_firm.id]
        return None
```

## Risk Assessment
The primary risk is **Registry Pollution**: if a transfer fails after registration, the "Zombified" firm ID must be purged from the `simulation.agents` map to prevent `TD-ARCH-STARTUP-RACE` from becoming a `TD-ECON-INSTABILITY` issue.

## Conclusion
The Ghost Firm race condition is a direct result of capital transfer preceding agent registration. By enforcing an **Atomic Onboarding Protocol** and strict **DTO Normalization** in the Saga Orchestrator, the system can achieve 100% lifecycle reliability.
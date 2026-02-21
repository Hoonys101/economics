I will begin by searching for the strings `SAGA_SKIP` and `SETTLEMENT_FAIL` in the codebase to identify the precise code locations causing these errors.

I will search for the string "SAGA_SKIP" in the `simulation` directory to pinpoint the exact location in the code where this warning is generated.

I will search for the string "SAGA_SKIP" in the `modules` directory to see if the warning is being generated within one of the project's modules.

I will search for the string "Destination account does not exist" in the codebase to find where the `SETTLEMENT_FAIL` error related to missing accounts is being triggered.

I will read the `simulation\systems\settlement_system.py` file to understand how the `SETTLEMENT_FAIL` error is being handled and identified within the settlement logic.

I will read the `modules\finance\transaction\engine.py` file to confirm where the "Destination account does not exist" message is generated and understand the validation logic.

I will read the `modules\finance\transaction\adapter.py` file to examine how `RegistryAccountAccessor` is implemented and how it determines if an account exists.

I will read the `modules\finance\sagas\orchestrator.py` file to understand why the `SAGA_SKIP` warning is being triggered and what participant IDs are missing.

I will read the `modules\finance\sagas\housing_api.py` file to examine the definition of `HousingTransactionSagaStateDTO` and see if the expected attributes for buyer and seller are present.

I will read the `modules\simulation\api.py` file to verify the attributes of `HouseholdSnapshotDTO` and confirm if it uses `id` or `household_id`.

I will search for instances of `HousingTransactionSagaStateDTO` instantiation in the codebase to determine how `buyer_context` and `seller_context` are being populated.

I will read the `simulation\systems\housing_system.py` file to see which version of `HousingTransactionSagaStateDTO` is being used and how it is being instantiated.

I will read the `modules\housing\dtos.py` file to see the TypedDict definition of `HousingTransactionSagaStateDTO` and identify any discrepancies with the dataclass version.

I will read the `modules\finance\saga_handler.py` file to understand how it interacts with the Saga object and if there are any further DTO inconsistencies.

I will read the `modules\finance\kernel\api.py` file to understand the defined protocols for the Saga Orchestrator and ensure that the proposed remediation plan aligns with these interfaces.

I will read the `simulation\world_state.py` file to determine how sagas are stored and if any serialization processes might be causing the DTO structure to change.

I will search for the string "spawn_firm" in the codebase to identify the locations where new firms are created and investigate the logic surrounding their registration and initial capital transfers.

I will read the `simulation\systems\firm_management.py` file to verify the current implementation of `spawn_firm` and determine if the registration step is indeed occurring after the capital transfer.

I will now create the insight report at `communications/insights/diag-remediation-plan.md`, detailing the root causes of the observed systemic failures and proposing a multi-phase remediation plan to address these issues and ensure M2 integrity.

I will attempt to use the `write_file` tool to create the insight report at `communications/insights/diag-remediation-plan.md`, as mandated by the instructions, even though it wasn't explicitly listed in the initial tool declarations.

I will use the `sequentialthinking` tool to analyze the current tool availability and determine the best course of action to fulfill the reporting requirement despite the absence of `write_file` and `run_shell_command` in the declared tools.

I will list the contents of the `simulation` directory to locate the `immigration_manager.py` file and other relevant system components.

I will list the contents of the `simulation\systems` directory to find the `immigration_manager.py` file.

I will read the `simulation\systems\immigration_manager.py` file to check for any race conditions in the agent creation and registration process, similar to the one found in `spawn_firm`.

I will read the `simulation\engine.py` file to see how immigrants are added to the simulation and if the `engine.agents` mapping is updated after the immigration process.

I will search for the string "process_immigration" in the codebase to find where this method is called and how the immigration process is integrated into the simulation cycle.

I will read the `simulation\systems\lifecycle\birth_system.py` file to see how the immigration process is handled and where the newly created households are added to the simulation state.

# [Technical Report] Systemic Failure Root Cause & Remediation Plan

## Executive Summary
Analysis of diagnostic logs and the technical debt ledger identifies two critical structural failures: a **Lifecycle Race Condition** in agent creation and a **DTO Protocol Mismatch** in the Saga system. These issues cause frequent transaction failures (`SETTLEMENT_FAIL`) and process skipping (`SAGA_SKIP`), which directly compromise M2 money supply integrity and simulation stability.

## Detailed Analysis

### 1. Agent Startup Race Condition (SETTLEMENT_FAIL)
- **Status**: ❌ Broken (Race Condition)
- **Code Locations**: 
    - `simulation\systems\firm_management.py:L148-158` (Firm Entrepreneurship)
    - `simulation\systems\immigration_manager.py:L123-132` (Household Immigration)
- **Root Cause**: Both systems attempt to execute a financial transfer (Startup Capital or Immigration Grant) to a new agent *before* the agent is registered in `simulation.agents` (the `AgentRegistry`).
- **Mechanism**: `SettlementSystem` delegates to `TransactionEngine`, which uses a `RegistryAccountAccessor`. This accessor queries the registry; if the ID is not found, it raises `InvalidAccountError`.
- **Evidence**: `diagnostic_refined.md:L89` shows "Engine Error: Destination account does not exist: 124" immediately followed by "Failed to transfer capital from 101 to new firm 124. Aborting."
- **Cross-Ref**: `TD-ARCH-STARTUP-RACE`

### 2. Saga Participant Drift (SAGA_SKIP)
- **Status**: ❌ Inconsistent (DTO Drift)
- **Code Location**: `modules\finance\sagas\orchestrator.py:L124`
- **Root Cause**: Architectural collision between two definitions of `HousingTransactionSagaStateDTO`:
    - `modules\housing\dtos.py`: Defined as a `TypedDict` with a root `buyer_id` field.
    - `modules\finance\sagas\housing_api.py`: Defined as a `@dataclass` with a nested `buyer_context.household_id` field.
- **Mechanism**: The `SagaOrchestrator` extraction logic (L115-133) attempts to navigate these structures using a mix of `getattr` and `try-except`. If `buyer_id` or `seller_id` remains `None` (due to missing attributes or `ValueError` during string-to-int conversion), the Saga is skipped.
- **Evidence**: Persistent `SAGA_SKIP` warnings in `diagnostic_refined.md:L22-37`.
- **Cross-Ref**: `TD-FIN-SAGA-ORPHAN`

### 3. M2 Inversion and Integrity
- **Status**: ⚠️ Partial (Logic Error)
- **Code Location**: `simulation\world_state.py:L160-185` (`calculate_total_money`)
- **Root Cause**: Aggregate money supply calculation treats liabilities (overdrafts) as negative cash, leading to negative M2 values when total debt exceeds total liquidity.
- **Evidence**: `diagnostic_refined.md:L1030` shows `MONEY_SUPPLY_CHECK | Current: -47712322.00, Expected: 50505570.00`.
- **Cross-Ref**: `TD-ECON-M2-INV`

## Proposed MISSION_spec: systemic-reliability-repair

### Phase 1: Lifecycle Atomicity
- **Task**: Fix Agent Creation Sequence.
- **Action**: In `FirmSystem.spawn_firm` and `ImmigrationManager`, reorder logic to ensure `simulation.agents[id] = agent` occurs **BEFORE** any `settlement_system.transfer` calls.
- **Refactor**: Introduce `Simulation.register_new_agent(agent)` to handle registry insertion, currency holder registration, and bank account initialization atomically.

### Phase 2: Saga Protocol Unification
- **Task**: Standardize `HousingTransactionSagaStateDTO`.
- **Action**: Delete the `TypedDict` version in `modules\housing\dtos.py`.
- **Action**: Update all consumers to use the `@dataclass` version from `modules\finance\sagas\housing_api.py`.
- **Action**: Harden `SagaOrchestrator` ID extraction to handle `None` and `ValueError` explicitly, ensuring that any malformed Saga is `CANCELLED` rather than silently skipped.

### Phase 3: M2 Guard & Monetary Ledger
- **Task**: Ensure Zero-Sum Integrity.
- **Action**: Fix `WorldState.calculate_total_money` to distinguish between available liquidity and outstanding liabilities.
- **Action**: Enforce `MonetaryLedger` updates in `HousingTransactionSagaHandler` for every successful `ESCROW_LOCKED` (Credit Expansion) and `compensate_step` (Credit Destruction).

## Risk Assessment
The simulation is currently operating with "Ghost Agents"—entities that exist in memory but are invisible to the financial engine. This creates "trapped money" (founders pay, but firms don't receive) and "stuck assets" (properties locked by skipped sagas). Failure to unify the DTOs will lead to persistent flakiness in the housing market and M2 metrics.

## Conclusion
The simulation's "Plumbing" is functional, but the "Wiring" (Agent Registry and Saga IDs) is misaligned. Implementing the `systemic-reliability-repair` MISSION_spec will restore structural integrity and allow for accurate economic analysis.
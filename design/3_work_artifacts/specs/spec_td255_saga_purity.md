# Spec: TD-255 Housing Saga DTO Hardening

## 1. Objective
Ensure that the `Phase_HousingSaga` operates on isolated snapshots of agent state rather than directly mutating shared state mid-saga. This prevents "state bleeding" where a partially completed housing transaction affects other market decisions.

## 2. Rationale
Housing Sagas span multiple simulation ticks. If a `MortgageApplicationDTO` directly references a living `Household` object, the agent's cash or credit state might change *outside* the saga, leading to:
- Over-leveraged loans (if cash decreased after approval but before drawdown).
- Double-spent assets.

## 3. Proposed Architecture

### 3.1 Context Snapshotting
Modify `HousingService` (or the specific Saga handler) to capture a `HouseholdSnapshotDTO` at the moment of application.

```python
class HousingSagaContext:
    applicant_snapshot: HouseholdSnapshotDTO
    property_id: str
    status: SagaStatus
    ...
```

### 3.2 Pure DTO Enforcement
Update the `SagaOrchestrator` to only accept and pass around serialized DTOs, never live agent references.

## 4. Implementation Steps (Jules Mission)
1. **Define Snapshot DTO**: Ensure `HouseholdSnapshotDTO` contains all necessary fields for mortgage underwriting.
2. **Refactor Saga Initiation**: Update `HousingManager` to populate the `SagaContext` with a snapshot.
3. **Update Handlers**: Modify `approve_mortgage` and `drawdown_loan` handlers to compare current state vs. snapshot state for sanity checks.

## 5. Verification
- `pytest tests/integration/test_housing_saga_purity.py`: Mock a cash-drain event during a 5-tick saga and verify the saga fails gracefully due to snapshot mismatch.

# Combined Spec: TD-255 & TD-256 Saga and Inventory Purity

## 1. Objective
To enforce domain purity and data integrity across the platform by (1) isolating long-running Sagas from mid-transaction state changes through immutable DTO snapshots, and (2) abstracting all inventory management behind a strict transactional protocol.

## 2. API & Contract Definitions (modules/simulation/api.py)

```python
@runtime_checkable
class IInventoryHandler(Protocol):
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool: ...
    def get_quantity(self, item_id: str) -> float: ...

@dataclass(frozen=True)
class HouseholdSnapshotDTO:
    household_id: str
    cash: float
    income: float
    credit_score: float
    existing_debt: float
    assets_value: float
```

## 3. Implementation Phases (Jules Mission)

### Phase 1: Audit & Discovery
- Perform codebase search for all `.inventory` access.
- Document call sites that will break post-encapsulation.

### Phase 2: Implementation (TD-256)
- Rename `self.inventory` -> `self._inventory` in `Firm` and `Household`.
- Implement `IInventoryHandler` protocol.
- Update `SettlementSystem` to use protocol-based transfers.

### Phase 3: Implementation (TD-255)
- Update `HousingManager` to capture `HouseholdSnapshotDTO`.
- Ensure Saga handlers operate ONLY on snapshots, not live objects.

## 4. Risks & Guardrails
- **Circular Dependency**: `modules/simulation` MUST NOT import concrete agents (`Firm`/`Household`). Depend only on the protocol.
- **Breaking Changes**: This refactor is broad. `scripts/audit_inventory_access.py` must be used to verify zero legacy access.

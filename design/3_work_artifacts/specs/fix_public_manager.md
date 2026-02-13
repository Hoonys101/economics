default_api:write_file{file_path:<ctrl46>modules/system/api.py<ctrl46>,limit:null,offset:null}
File: modules/system/api.py
```python
from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict, Any, TypedDict, List, Optional

# --- DTOs ---

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]
    # Add other fields if necessary based on usage

class MarketSignalDTO(TypedDict):
    item_id: str
    best_ask: Optional[float]
    best_bid: Optional[float]
    last_traded_price: Optional[float]
    volume: float

class PublicManagerReportDTO(TypedDict):
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]

# --- Protocols ---

@runtime_checkable
class ICurrencyHolder(Protocol):
    def get_balance(self, currency: str) -> int: ...
    def get_all_balances(self) -> Dict[str, int]: ...
    def _deposit(self, amount: int, currency: str = ...) -> None: ...
    def _withdraw(self, amount: int, currency: str = ...) -> None: ...

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """
        Ingests assets from a bankrupt agent.
        """
        ...

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        """
        Receives inventory from a firm undergoing liquidation (Asset Buyout).
        """
        ...

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]: # Returns List[Order]
        """
        Generates SELL orders to liquidate managed assets into the market.
        """
        ...

```

File: design/3_work_artifacts/specs/public_manager_fix_spec.md
```markdown
# Spec: Public Manager Interface Harmonization & Mock Fix

## 1. Problem Definition
The `PublicManager` system is currently experiencing regression failures in the test suite due to a divergence between the implementation and the test mocks.
- **Issue A**: `test_asset_liquidation_integration` fails because the `PublicManager` mock lacks the `receive_liquidated_assets` method, which is present in the implementation.
- **Issue B**: `test_command_service_rollback` fails because it calls `mint_and_distribute`, a method that does not exist in `PublicManager` and violates the Zero-Sum Integrity principle if interpreted as money creation.

## 2. Proposed Changes

### 2.1. Protocol Definition (`modules/system/api.py`)
- **Update `IAssetRecoverySystem`**: Explicitly add `receive_liquidated_assets(self, inventory: Dict[str, float]) -> None` to the protocol definition. This ensures that any mock based on this protocol (via `spec=IAssetRecoverySystem`) will require this method.

### 2.2. Test Refactoring
- **Refactor `tests/unit/systems/test_liquidation_manager.py`**:
    - Update the local mock of `PublicManager` to include `receive_liquidated_assets`.
    - Ensure the mock's side_effect or return value is set correctly (e.g., `return_value = None`).
- **Refactor `tests/system/test_command_service_rollback.py`**:
    - **DEPRECATION NOTICE**: `mint_and_distribute` is not a valid method for `PublicManager` as it acts as a Receiver/Liquidator, not a Central Bank.
    - **Action**: Replace calls to `pm.mint_and_distribute(amount, currency)` with `pm.deposit_revenue(amount, currency)`.
    - If the test intends to *create* money from thin air for a scenario, it should use the `CentralBank` fixture or explicitly mock a system deposit. For `PublicManager`, `deposit_revenue` is the correct API for receiving funds.

## 3. Detailed Logic (Pseudo-code)

### 3.1. Public Manager Mock Update (in `tests/unit/systems/test_liquidation_manager.py`)
```python
# In the test setup or fixture
public_manager_mock = MagicMock(spec=IAssetRecoverySystem)
# Explicitly define the method if spec doesn't auto-create it (MagicMock usually does, but let's be safe)
# The error "Mock object has no attribute" suggests the spec might be missing it OR it's a non-Magic Mock.
# If using strict spec:
public_manager_mock.receive_liquidated_assets = Mock()
```

### 3.2. Rollback Test Fix (in `tests/system/test_command_service_rollback.py`)
```python
# OLD
# public_manager.mint_and_distribute(1000, "USD")

# NEW
# If the goal is to set an initial state:
public_manager.deposit_revenue(1000, "USD")
```

## 4. Verification Plan

### 4.1. Automated Tests
Run the specific failing tests to verify the fix:
```bash
pytest tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_asset_liquidation_integration
pytest tests/system/test_command_service_rollback.py::test_rollback_inject_asset
```

### 4.2. Risk Audit
- **Zero-Sum Integrity**: By forcing the test to use `deposit_revenue` instead of `mint_and_distribute`, we ensure that even in tests, we are using the established accounting methods (even if the source of that revenue in the test is "magic", the method call is correct).
- **Interface Compliance**: Updating `IAssetRecoverySystem` ensures that future implementations of asset recovery must handle liquidated assets.

## 5. Mocking Strategy
- Use `tests/conftest.py` where possible.
- If `PublicManager` is mocked via `unittest.mock.create_autospec`, updating the `PublicManager` class or `IAssetRecoverySystem` protocol will automatically update the mock signature, solving the `AttributeError`.

```

File: communications/insights/spec-fix-public-manager.md
```markdown
# Insight Report: Public Manager Spec Fix

## Architectural Insights
- **Protocol Drift**: The regression highlighted a disconnect between the `IAssetRecoverySystem` protocol and the `PublicManager` implementation. The protocol must be the "Source of Truth" for all mocks.
- **Zero-Sum Guardrail Enforcement**: The attempt to use `mint_and_distribute` in a test reveals a potential misunderstanding of the `PublicManager`'s role. It is an *Asset Recovery* system, not a *Monetary Authority*. Enforcing `deposit_revenue` usage aligns the test with the architectural constraints.

## Technical Debt
- **Test-Implementation Coupling**: The `test_liquidation_manager.py` test was manually constructing a mock that drifted from the real implementation. Moving towards `spec=IAssetRecoverySystem` (and keeping that protocol updated) is crucial to prevent future drift.

## Verification Checklist
- [ ] `IAssetRecoverySystem` in `modules/system/api.py` includes `receive_liquidated_assets`.
- [ ] `test_liquidation_manager.py` passes.
- [ ] `test_command_service_rollback.py` passes (after refactor).
```
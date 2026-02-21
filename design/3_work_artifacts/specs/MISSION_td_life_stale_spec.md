File: modules\system\api.py
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TYPE_CHECKING, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto

# ==============================================================================
# Domain: System & Asset Recovery (Lifecycle)
# ==============================================================================

AgentID = int

@dataclass(frozen=True)
class AssetBuyoutRequestDTO:
    """
    Request payload for the PublicManager to purchase assets from a distressed entity.
    Used in IAssetRecoverySystem.execute_asset_buyout.
    """
    seller_id: AgentID
    inventory: Dict[str, float]
    market_prices: Dict[str, int]  # Current market price (pennies) for valuation
    distress_discount: float = 0.5 # e.g., 50% of market value

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
    """
    Result of an asset buyout operation.
    """
    success: bool
    total_paid_pennies: int
    items_acquired: Dict[str, float]
    buyer_id: AgentID  # PublicManager ID
    transaction_id: Optional[str] = None
    
@dataclass(frozen=True)
class AgentBankruptcyEventDTO(TypedDict):
    """
    Legacy DTO for backward compatibility, referring to the event of an agent going bankrupt.
    """
    agent_id: int
    tick: int
    inventory: Dict[str, float]
    total_debt: int
    creditor_ids: List[int]

@dataclass(frozen=True)
class MarketSignalDTO:
    """
    DTO for market signals used in liquidation order generation.
    """
    market_id: str
    item_id: str
    best_bid: Optional[int]
    best_ask: Optional[int]
    last_traded_price: Optional[int]
    # ... other fields as per context, abbreviated for outline focus

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    Now supports active buyout logic to inject liquidity (Soft Budget Constraint).
    """
    
    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent to provide liquidity for creditor repayment.
        Allowed to go into overdraft (Soft Budget Constraint).
        """
        ...

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]:
        """
        Generates SELL orders to liquidate managed assets into the market.
        """
        ...
        
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """
        Legacy ingestion of assets (deprecated in favor of execute_asset_buyout).
        Kept for backward compatibility but should trigger a warning or migration.
        """
        ...

    def get_deficit(self) -> int:
        """
        Returns the cumulative deficit (negative balance) incurred by operations.
        """
        ...
```

File: design\3_work_artifacts\specs\td_test_life_stale_spec.md
```markdown
# Specification: TD-TEST-LIFE-STALE (Lifecycle Test Alignment)

## 1. Introduction
- **Task**: TD-TEST-LIFE-STALE
- **Objective**: Align `test_engine.py` and related lifecycle tests with the current `IAssetRecoverySystem` architecture.
- **Scope**: Refactor test cases calling deprecated liquidation methods (`liquidate`, `die`, `remove_agent`) to use the `execute_asset_buyout` workflow defined in the `IAssetRecoverySystem` protocol.
- **Mandate**: Ensure tests use `AssetBuyoutRequestDTO` and `AssetBuyoutResultDTO` for verification.

## 2. Current Architecture vs. Test Mismatch
- **Architecture**: The system now uses a "Soft Budget Constraint" model where the `PublicManager` (via `AssetRecoverySystem`) buys out assets from distressed firms to prevent system lockup.
- **Tests (Legacy)**: Likely verify that an agent is simply removed (`self.agents.pop(id)`) or call a void method.
- **Risk**: Tests passing on legacy logic mask the fact that the actual simulation path (Buyout) is untested or broken in integration.

## 3. Detailed Design (Refactoring Plan)

### 3.1. Mocking Strategy
- **Strict Protocol Mocking**: All mocks of the recovery system MUST use `spec=IAssetRecoverySystem`.
- **Fixture Update**: Update `tests/conftest.py` (if applicable) or local fixtures in `test_engine.py` to provide a compliant mock.

```python
# Pseudo-code for updated test fixture/setup
from unittest.mock import MagicMock
from modules.system.api import IAssetRecoverySystem, AssetBuyoutResultDTO

def test_firm_liquidation_flow(self):
    # 1. Setup Mock
    mock_recovery_system = MagicMock(spec=IAssetRecoverySystem)
    
    # 2. Configure Return Value (Golden Path)
    mock_recovery_system.execute_asset_buyout.return_value = AssetBuyoutResultDTO(
        success=True,
        total_paid_pennies=5000,
        items_acquired={"grain": 10.0},
        buyer_id=999, # PublicManager
        transaction_id="tx_123"
    )
    
    # 3. Inject into Simulation State or Engine
    simulation.recovery_system = mock_recovery_system
    
    # 4. Trigger Liquidation Logic (e.g., via check_solvency or explicit call)
    # This depends on what test_engine.py is actually testing.
    # If it's testing the engine's reaction to insolvency:
    firm.money = -100 # Insolvency
    engine.process_lifecycle(firm)
    
    # 5. Verify Call (The Fix)
    # OLD: assert firm.id not in simulation.agents
    # NEW: Verify the orchestrator delegated to the recovery system
    mock_recovery_system.execute_asset_buyout.assert_called_once()
    
    # Verify DTO construction in the call args
    args, _ = mock_recovery_system.execute_asset_buyout.call_args
    request_dto = args[0]
    assert request_dto.seller_id == firm.id
    assert request_dto.distress_discount > 0.0
```

### 3.2. Code Changes Required
1.  **`tests/test_engine.py`**:
    -   Locate calls to `liquidate_agent` (or similar).
    -   Replace with assertions checking for `execute_asset_buyout` delegation.
    -   Ensure `AssetBuyoutRequestDTO` is correctly formed by the code under test.
2.  **`simulation/core.py` (Verification)**:
    -   Ensure the actual `process_lifecycle` or `check_bankruptcy` method constructs `AssetBuyoutRequestDTO` and calls `execute_asset_buyout`. (This might be a code fix if the engine itself is stale).

## 4. Verification Plan

### 4.1. New Test Cases
- **Case 1: Successful Buyout**: Mock returns `success=True`. Verify agent is deactivated (or reset) and assets transferred (logically).
- **Case 2: Buyout Failure**: Mock returns `success=False`. Verify fallback behavior (Zombie state or Hard Crash handling).
- **Case 3: Partial Inventory**: Verify `inventory` dict in `AssetBuyoutRequestDTO` matches firm's actual inventory.

### 4.2. Existing Test Impact
- **`test_transaction_engine.py`**: May need updates if it mocks bankruptcy transactions.
- **`test_firm.py`**: If it tests individual firm death, ensure it doesn't assume immediate object deletion.

## 5. Technical Debt & Risk Audit

### 5.1. Resolved Debt
- **TD-TEST-LIFE-STALE**: Directly resolving this item.

### 5.2. New Risks
- **Mock Drift**: If `IAssetRecoverySystem` changes again, these strict mocks will break (which is good, but requires maintenance).
- **Integration Gap**: Mocking `execute_asset_buyout` verifies the *call*, but not the *result* (e.g., is the `PublicManager` actually getting the assets?). Integration tests (not just unit tests) are needed for full SEO pattern verification.

### 5.3. Mandatory Reporting
- [ ] Create `communications/insights/spec_stale_lifecycle_tests.md`
- [ ] Document findings on `IAssetRecoverySystem` adoption rate in the codebase.
- [ ] Report any "Zombie Agent" issues found during test execution.

## 6. Pre-Implementation Checklist
- [ ] `modules/system/api.py` is the SSoT for protocols.
- [ ] `tests/conftest.py` `golden_firms` are valid for liquidation tests.
- [ ] `AssetBuyoutRequestDTO` import paths are verified.
```
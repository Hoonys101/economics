modules/system/api.py
```python
from typing import Protocol, Any, Dict, Optional, runtime_checkable
from enum import Enum

class OriginType(Enum):
    """
    Defines the source of a configuration value for traceability and priority resolution.
    """
    SYSTEM = "SYSTEM"   # Hardcoded defaults in code
    CONFIG = "CONFIG"   # Loaded from simulation.yaml
    USER = "USER"       # Runtime overrides (e.g., God Mode, CLI)
    ENV = "ENV"         # Environment variables

@runtime_checkable
class IConfigurationRegistry(Protocol):
    """
    Interface for the Global Registry acting as the Single Source of Truth (SSoT) 
    for all simulation parameters.
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        Must support dynamic resolution (always fetch current value).
        """
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        """
        Updates a configuration value with a specified origin.
        Should trigger any registered listeners for this key.
        """
        ...
        
    def snapshot(self) -> Dict[str, Any]:
        """
        Returns a complete snapshot of the current configuration state.
        Useful for serialization or debugging.
        """
        ...
    
    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
        ...

@runtime_checkable
class IProtocolEnforcer(Protocol):
    """
    Interface for test utilities that enforce strict protocol adherence.
    """
    
    def assert_implements_protocol(self, instance: Any, protocol: Any) -> None:
        """
        Verifies that an instance implements all methods and attributes 
        defined in the protocol. Raises AssertionError if not.
        """
        ...
```

design/3_work_artifacts/specs/spec_17_3_config_protocol_purity.md
```markdown
# Spec 17.3: Config Hot-Swap & Protocol Mocking

## 1. Introduction

- **Purpose**: To eliminate the "Ghost Constant" anti-pattern where configuration values are bound at import time, preventing runtime updates. Simultaneously, to enforce strict Protocol compliance in tests to eliminate "False Positive" results where mocks pass but real objects fail.
- **Scope**: 
  - Refactoring `config/__init__.py` to be a pure proxy.
  - Migrating codebase from `from config import X` to `import config` -> `config.X`.
  - Updating `tests/` to use `spec=Protocol` for critical interfaces (`ISettlementSystem`, `IBank`).
- **Goals**: 
  - **Dynamic Config**: Changing a value in `GlobalRegistry` immediately affects the simulation.
  - **Test Integrity**: Tests fail if a Mock doesn't strictly match its Interface.

## 2. System Architecture

### 2.1. The "Ghost Constant" Problem & Solution

**Current State (Anti-Pattern):**
```python
# config/__init__.py
INITIAL_MONEY_SUPPLY = 100000

# consumer.py
from config import INITIAL_MONEY_SUPPLY # Value 100000 is copied here FOREVER
```

**Target State (Dynamic Proxy):**
```python
# consumer.py
import config

def logic():
    # Accesses config.__getattr__('INITIAL_MONEY_SUPPLY') -> queries GlobalRegistry
    val = config.INITIAL_MONEY_SUPPLY 
```

### 2.2. Strict Mocking Strategy

**Current State (Loose Mocking):**
```python
settlement_system = MagicMock() # Accepts ANY method call
settlement_system.non_existent_method() # Passes silently
```

**Target State (Strict Protocol):**
```python
# Uses modules.finance.api.ISettlementSystem
settlement_system = MagicMock(spec=ISettlementSystem) 
settlement_system.non_existent_method() # Raises AttributeError immediately
```

## 3. Detailed Design

### 3.1. Config Module Refactoring

The `config/__init__.py` will be rewritten to strictly delegate to `GlobalRegistry`.

1.  **Separation of Defaults**: Move all hardcoded uppercase constants from `config/__init__.py` to `config/defaults.py`.
2.  **Registry Initialization**: `config/__init__.py` imports defaults, populates `GlobalRegistry` with `OriginType.SYSTEM`.
3.  **Proxy Mechanism**: `config/__init__.py` implements `__getattr__` to query `GlobalRegistry`. It MUST NOT define the constants in its own namespace after initialization.

### 3.2. Migration Regex Strategy

To refactor the codebase efficiently, we will apply the following transformations:

| Pattern Type | Find Regex | Replace With | Notes |
| :--- | :--- | :--- | :--- |
| **Import** | `from config import ([A-Z_]+(?:, [A-Z_]+)*)` | `import config` | Requires manual fixup of usages |
| **Usage** | `(?<!config\.)\b([A-Z_]{4,})\b` | `config.\1` | *Caution*: Only apply in files that imported from config. |

**Execution Strategy**: 
1.  Run `analyze_call_sites.py` to identify all files importing `config`.
2.  Apply changes file-by-file to minimize breakage.
3.  Run tests after each file/module group.

### 3.3. Interface Segregation for `ISettlementSystem`

To enable strict mocking without forcing agents to implement God Mode methods, we will split `ISettlementSystem`.

**Refactored Interfaces in `modules/finance/api.py`:**

1.  **`ISettlementSystem` (Base)**:
    -   `transfer(...)`
    -   `get_balance(...)`
    -   *Used by: Households, Firms*

2.  **`IMonetaryAuthority` (Extends ISettlementSystem)**:
    -   `mint_and_distribute(...)`
    -   `create_and_transfer(...)`
    -   `transfer_and_destroy(...)`
    -   `audit_total_m2(...)`
    -   *Used by: Government, CentralBank, God Mode Scripts*

**Impact**: Tests for Households will use `spec=ISettlementSystem`. Tests for Government will use `spec=IMonetaryAuthority`.

## 4. Verification Plan

### 4.1. Config Hot-Swap Test
```python
def test_config_hot_swap():
    import config
    from modules.system.registry import registry
    
    # 1. Read initial
    initial = config.INITIAL_MONEY_SUPPLY
    
    # 2. Update Registry
    registry.set("INITIAL_MONEY_SUPPLY", initial + 1)
    
    # 3. Verify Proxy
    assert config.INITIAL_MONEY_SUPPLY == initial + 1
```

### 4.2. Strict Mock Test
```python
def test_strict_mock_enforcement():
    from modules.finance.api import ISettlementSystem
    from unittest.mock import MagicMock
    
    mock = MagicMock(spec=ISettlementSystem)
    
    # Should fail because 'fake_method' is not in Protocol
    try:
        mock.fake_method() 
        assert False, "Should have raised AttributeError"
    except AttributeError:
        assert True
```

## 5. Risk Assessment & Audit

### 5.1. Risks
-   **Performance Overhead**: Attribute access via `__getattr__` is slower than local variable access.
    -   *Mitigation*: For tight loops (e.g., thousands of agents), assign to a local variable *outside* the loop if the value is not expected to change *during* the loop.
-   **Circular Imports**: `config` -> `registry` -> `config` (if registry uses defaults).
    -   *Mitigation*: `registry` must be self-contained and NOT import `config`. Defaults are pushed *into* registry by `config`, not pulled *by* registry.

### 5.2. Technical Debt Added
-   **Proxy Complexity**: Debugging `config` values requires understanding the Proxy pattern.
-   **Refactor Noise**: Large diffs in PRs due to `import config` changes.

## 6. Mandatory Reporting

> [!IMPORTANT]  
> All findings regarding "Ghost Constants" and "Protocol Drift" discovered during this implementation MUST be logged to:
> `communications/insights/spec-17-3-config-protocol-purity.md`
```

communications/insights/spec-17-3-config-protocol-purity.md
```markdown
# Insight Report: Spec 17.3 Config & Protocol Purity

## Architectural Insights

### 1. The "Ghost Constant" Trap
The codebase currently relies heavily on `from config import X`. This creates a rigid dependency graph where values are "baked in" at process start. 
-   **Impact**: Runtime adjustments (e.g., God Mode commands, AI Curriculum changes) are silently ignored by modules that have already imported the constant.
-   **Correction**: Moving to `import config` acts as a Service Locator for configuration, ensuring `config.X` always hits the `GlobalRegistry`.

### 2. Protocol Interface Segregation
`ISettlementSystem` was identified as a "God Interface", mixing standard agent capabilities (Transfer) with Admin capabilities (Minting).
-   **Decision**: Split into `ISettlementSystem` (Standard) and `IMonetaryAuthority` (Admin).
-   **Benefit**: Agents can be tested with strict mocks of `ISettlementSystem` without needing to stub out administrative methods they should never call.

## Technical Debt Ledger

| ID | Type | Description | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **TD-CONF-01** | Architecture | `config/__init__.py` contains hardcoded defaults mixed with logic. | Extract defaults to `config/defaults.py`. |
| **TD-TEST-01** | Testing | Tests use `MagicMock()` without specs, allowing drift. | Enforce `spec=Protocol` in `conftest.py` fixtures. |

## Pre-Implementation Test Evidence

*Placeholder for `pytest` output demonstrating the failure of current "Ghost Constant" updates or loose mocks.*
```
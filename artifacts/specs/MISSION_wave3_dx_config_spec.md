File: modules/system/config_api.py
```python
"""
modules/system/config_api.py

Defines the ConfigProxy and Configuration Registry APIs.
Resolves TD-CONF-GHOST-BIND by enabling lazy-loading and runtime overrides of configuration constants.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Protocol, Type, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from modules.system.api import IConfigurationRegistry, RegistryValueDTO, OriginType, RegistryObserver

if TYPE_CHECKING:
    from types import ModuleType

@dataclass
class ConfigKeyMeta:
    """Metadata for configuration keys (validation, description, etc.)"""
    description: str = ""
    value_type: Type = Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    is_hot_swappable: bool = True

class ConfigProxy(IConfigurationRegistry):
    """
    A Singleton Proxy that provides dynamic access to configuration values.
    
    Usage:
        from modules.system.config_api import current_config
        tax_rate = current_config.TAX_RATE  # Resolved at runtime
        
    Legacy Compatibility:
        This proxy can be injected or aliased, but legacy 'from config import CONST' 
        will still bind early. This class is the enabler for the refactor.
    """
    
    def __init__(self):
        # The internal store of all config values
        self._registry: Dict[str, RegistryValueDTO] = {}
        # Metadata for validation
        self._metadata: Dict[str, ConfigKeyMeta] = {}
        # Observers for reactive updates
        self._observers: list[RegistryObserver] = []
        # Fallback module (legacy config/defaults.py)
        self._defaults_module: Optional[ModuleType] = None

    def bootstrap_from_module(self, module: ModuleType) -> None:
        """
        Loads initial values from a Python module (e.g., config.defaults).
        """
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value. Priority: USER > CONFIG > SYSTEM (Defaults).
        """
        ...
        
    def __getattr__(self, name: str) -> Any:
        """
        Enables dot-access (current_config.TAX_RATE).
        """
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        """
        Updates a value with origin tracking and notifies observers.
        """
        ...

    def snapshot(self) -> Dict[str, Any]:
        """Returns a dict of current effective values."""
        ...

    def register_observer(self, observer: RegistryObserver) -> None:
        ...

# Singleton Instance
current_config = ConfigProxy()
```

File: _internal/registry/api.py
```python
"""
_internal/registry/api.py

Defines the Gemini Mission Registry API and Decorators.
Resolves TD-DX-AUTO-CRYSTAL by enabling auto-discovery of missions.
"""
from __future__ import annotations
from typing import Callable, Dict, List, Optional, TypedDict, Any, Protocol
from dataclasses import dataclass, field

class MissionContext(TypedDict):
    """Defines the context files required for a mission."""
    files: List[str]

class GeminiMissionDefinition(TypedDict):
    """
    Schema for a registered mission.
    Matches the structure required by gemini_manifest.py.
    """
    title: str
    worker: str # 'spec', 'reporter', 'verify', etc.
    instruction: str
    context_files: List[str]
    output_path: Optional[str]
    model: Optional[str]

class MissionMetadata(TypedDict, total=False):
    """Optional metadata for missions."""
    priority: str
    owner: str
    tags: List[str]

@dataclass
class RegisteredMission:
    """Internal representation of a registered mission."""
    key: str
    definition: GeminiMissionDefinition
    metadata: MissionMetadata

class IMissionRegistry(Protocol):
    """Interface for the Mission Registry."""
    
    def register(self, key: str, definition: GeminiMissionDefinition, metadata: Optional[MissionMetadata] = None) -> None:
        ...
        
    def get_mission(self, key: str) -> Optional[GeminiMissionDefinition]:
        ...
        
    def to_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Exports to the format required by GEMINI_MISSIONS."""
        ...
        
    def scan_packages(self, package_path: str) -> None:
        """Recursively scans a package for @gemini_mission decorated functions."""
        ...

# Decorator API
def gemini_mission(
    key: str,
    title: str,
    worker: str,
    context_files: List[str],
    output_path: str,
    instruction: str = "",
    model: str = "gemini-3-pro-preview",
    **kwargs
) -> Callable:
    """
    Decorator to register a function or class as a Gemini Mission.
    
    Usage:
        @gemini_mission(
            key="wave3-refactor",
            title="Wave 3 Refactor",
            worker="spec",
            context_files=["..."],
            output_path="..."
        )
        def mission_definition():
            return "Specific instructions if dynamic..."
    """
    ...

# Singleton Access
mission_registry: IMissionRegistry
```

File: communications/insights/wave3-dx-config-spec.md
```markdown
# Insight Report: Wave 3 DX & Config Hardening

## 1. Architectural Insights
### ConfigProxy & The "Ghost Bind" Paradox
- **Issue**: The migration to `ConfigProxy` introduces a temporary hybrid state. Legacy code using `from config.defaults import X` will continue to hold stale values, while new code using `current_config.X` will see dynamic updates.
- **Decision**: We will **NOT** refactor the entire codebase in this mission. The goal is to establish the *capability* (The Proxy). The actual migration of call sites will be handled in a subsequent "Deprecation Wave".
- **Safety Net**: The `ConfigProxy` will bootstrap itself from `config.defaults`, ensuring that `current_config.X` == `defaults.X` initially, preserving behavior for hybrid usage.

### Auto-Discovery & Runtime Latency
- **Issue**: Scanning packages (`pkgutil.walk_packages`) can be slow and may trigger unwanted side-effects if modules execute code at import time.
- **Mitigation**: The scanner will be restricted to a new dedicated namespace `_internal.missions`. We will enforce that mission definition files must be side-effect free (declarative only).

## 2. Risk Analysis (Pre-Flight)
- **Test Compatibility**: Existing tests that `mock.patch('config.defaults.SOME_VAL')` will **FAIL** if the code under test switches to `current_config`.
    - *Mitigation*: The `ConfigProxy` must provide a `override_context()` context manager that mocks can use, or we must ensure the `ConfigProxy` respects `unittest.mock` patching of the underlying default module (by looking up the module dynamically).
- **Circular Imports**: The Registry must not import the CLI runner. The CLI runner imports the Registry. This dependency direction is safe.

## 3. Technical Debt Added/Resolved
- **Resolved**: `TD-DX-AUTO-CRYSTAL` (Manual Manifest), `TD-CONF-GHOST-BIND` (Static Config).
- **Added**: `TD-MIGRATION-CONFIG-CALLS` (The need to update 50+ files to use `current_config`).

## 4. Verification Strategy
- **New Tests**: `tests/system/test_config_proxy.py` and `tests/internal/test_mission_registry.py` will be created.
- **Regression**: Full suite run required to ensure `config/defaults.py` behavior remains unchanged for legacy consumers.
```

File: artifacts/specs/MISSION_wave3_dx_config_spec.md
```markdown
# Mission Spec: Wave 3 DX & Config Hardening

## 1. Overview
- **Goal**: Resolve Technical Debt related to Developer Experience (DX) and Configuration Management.
- **Objectives**:
  1. **Config Hardening**: Replace static `config.defaults` with a dynamic `ConfigProxy` to enable runtime parameter tuning (Resolves `TD-CONF-GHOST-BIND`).
  2. **Auto-Discovery**: Implement a decorator-based Mission Registry to automate the maintenance of `gemini_manifest.py` (Resolves `TD-DX-AUTO-CRYSTAL`).

## 2. Architecture & Design

### 2.1. Dynamic Configuration (`ConfigProxy`)
We will implement the **Singleton Proxy Pattern** to mediate access to configuration values.

- **Component**: `modules.system.config_api.ConfigProxy`
- **Mechanism**: 
  - Implements `__getattr__` to intercept property access.
  - Delegates lookup to an internal `RegistryValueDTO` store.
  - Bootstraps values from the existing `config.defaults` module to maintain backward compatibility.
- **Key Feature**: `OriginType` tracking (SYSTEM vs USER) to allow "Reset to Defaults".

#### Pseudo-Code (Implementation Logic)
```python
class ConfigProxy:
    def __getattr__(self, name):
        # 1. Check internal overrides (USER/GOD_MODE)
        if name in self._registry:
            return self._registry[name].value
        # 2. Fallback to legacy defaults module
        return getattr(self._defaults_module, name)
```

### 2.2. Mission Registry (Auto-Discovery)
We will transition from a static dictionary to a **Distributed Registration Pattern**.

- **Component**: `_internal.registry.api.GeminiMissionRegistry`
- **Mechanism**:
  - Uses `pkgutil` to scan the `_internal/missions/` namespace.
  - `@gemini_mission` decorator registers metadata to the singleton registry at import time.
  - `gemini_manifest.py` becomes a thin wrapper that invokes the scan and exports the result.

## 3. Implementation Steps

### Step 1: Config Proxy Foundation
1. Create `modules/system/config_api.py` (Protocol & Proxy Class).
2. Implement `ConfigProxy.bootstrap_from_module()`.
3. Create `tests/system/test_config_proxy.py`:
   - Verify `current_config.TAX_RATE` reads from `config.defaults`.
   - Verify `current_config.set("TAX_RATE", 0.99)` overrides the value.
   - Verify `current_config.reset_to_defaults()` restores the original.

### Step 2: Registry Core
1. Create `_internal/registry/api.py` (Registry & Decorator).
2. Implement `scan_missions(package_path)`.
3. Create `tests/internal/test_mission_registry.py`:
   - Create a dummy mission file.
   - Verify scanner picks it up.
   - Verify `to_manifest()` output matches the `GEMINI_MISSIONS` schema.

### Step 3: Refactor Manifest
1. Create directory `_internal/missions/`.
2. **Refactor**: Move one existing mission (e.g., `wave1-finance-protocol-spec`) from `gemini_manifest.py` to `_internal/missions/wave1.py` and apply the `@gemini_mission` decorator.
3. Update `_internal/registry/gemini_manifest.py` to:
   - Import `mission_registry` and `scan_missions`.
   - Call `scan_missions("_internal.missions")`.
   - Set `GEMINI_MISSIONS = mission_registry.to_manifest()`.
   - **Crucial**: Manually re-add the remaining legacy missions to `GEMINI_MISSIONS` (hybrid approach) until fully migrated.

## 4. Verification Plan

### 4.1. Core Logic Verification
- **Config**: Assert `current_config.SIMULATION_TICKS` returns an `int` (not a string or None).
- **Registry**: Assert `len(GEMINI_MISSIONS) >= 1` after the refactor.

### 4.2. Regression Testing
- Run `pytest tests/` to ensure no circular imports were introduced by the new module dependencies.
- Ensure the CLI tool can still list missions (`python main.py --list-missions` equivalent).

## 5. Risks & Mitigation
- **Risk**: "Ghost Binding" in legacy modules.
  - **Mitigation**: We accept this for now. This mission builds the *infrastructure* for the fix. The actual update of 50+ files to use `current_config` is out of scope (deferred to `TD-MIGRATION-CONFIG-CALLS`).
- **Risk**: Registry Scan Performance.
  - **Mitigation**: Scan only `_internal.missions`, not the entire codebase.

## 6. Definition of Done
- `ConfigProxy` exists and passes unit tests.
- `gemini_manifest.py` is using the Registry to load at least one mission.
- `pytest` suite passes 100%.
```
# MISSION_SPEC: Phase C - GlobalRegistry Batch Mode
**Mission Key**: WO-SPEC-HANG-FIX-BATCH-NOTIFY

## 1. Goal
Add a `batch_mode()` context manager to `GlobalRegistry` in `registry.py`. When inside `batch_mode`, `_notify` calls are deferred. On exit, fire a single batched notification for all changed keys. Apply this in `_init_phase4_population` to prevent notification storms (UI freezes/hangs) during mass agent registration.

## 2. API Outline (`modules/system/api.py`)

Extend `IGlobalRegistry` to support `batch_mode`.

```python
# [modules/system/api.py]
import contextlib
from typing import Iterator

@runtime_checkable
class IGlobalRegistry(Protocol):
    # ... existing methods ...

    @contextlib.contextmanager
    def batch_mode(self) -> Iterator[None]:
        """
        Context manager to defer and batch notifications until the end of the block.
        """
        ...
```

## 3. Logic Steps (Pseudo-code) & Diffs

### A. `modules/system/registry.py` -> `GlobalRegistry`

**Pseudo-code**:
1. In `GlobalRegistry.__init__`, initialize `_batch_depth = 0` and `_batched_notifications = {}`.
2. Implement `batch_mode(self)` context manager using `contextlib`.
   - **Enter**: Increment `_batch_depth`.
   - **Exit**: Decrement `_batch_depth`. If it reaches 0, iterate over `_batched_notifications`, call a new `_notify_immediate` method, and clear the dict.
3. Modify `_notify` to intercept calls when `_batch_depth > 0`. Store the latest `(value, origin)` by key.
4. Rename the core notification loop inside `_notify` to `_notify_immediate`.

**Code Diff**:
```python
--- modules/system/registry.py
+++ modules/system/registry.py
@@ -10,6 +10,7 @@
 from modules.system.services.schema_loader import SchemaLoader
 from simulation.dtos.registry_dtos import ParameterSchemaDTO
 import threading
+from contextlib import contextmanager
 
 if TYPE_CHECKING:
     from simulation.agents import Agent
@@ -101,6 +102,8 @@
         self._metadata_map: Dict[str, ParameterSchemaDTO] = {}
         self._metadata_loaded = False # Flag for lazy loading
         self._metadata_lock = threading.Lock() # Lock for thread-safe lazy loading
+        self._batch_depth = 0
+        self._batched_notifications: Dict[str, tuple[Any, OriginType]] = {}
 
         if initial_data:
             self.migrate_from_dict(initial_data)
@@ -134,6 +137,22 @@
         max_origin = max(layers.keys(), key=lambda o: o.value)
         return layers[max_origin]
 
+    @contextmanager
+    def batch_mode(self):
+        """Defers notifications until the context block exits. Supports nesting."""
+        if not hasattr(self, '_batch_depth'):
+            self._batch_depth = 0
+            self._batched_notifications = {}
+        self._batch_depth += 1
+        try:
+            yield
+        finally:
+            self._batch_depth -= 1
+            if self._batch_depth == 0:
+                batched = self._batched_notifications
+                self._batched_notifications = {}
+                for key, (value, origin) in batched.items():
+                    self._notify_immediate(key, value, origin)
+
     def get(self, key: str, default: Any = None) -> Any:
@@ -216,10 +235,16 @@
                 self._key_observers[key].append(observer)
 
     def _notify(self, key: str, value: Any, origin: OriginType) -> None:
+        if getattr(self, '_batch_depth', 0) > 0:
+            self._batched_notifications[key] = (value, origin)
+            return
+        self._notify_immediate(key, value, origin)
+
+    def _notify_immediate(self, key: str, value: Any, origin: OriginType) -> None:
         # Notify global observers
         for observer in self._observers:
             observer.on_registry_update(key, value, origin)
```

### B. `simulation/initialization/initializer.py` -> `_init_phase4_population`

**Pseudo-code**:
1. Wrap the Household and Firm loops in `with sim.world_state.global_registry.batch_mode():`.

**Code Diff**:
```python
--- simulation/initialization/initializer.py
+++ simulation/initialization/initializer.py
@@ -375,25 +375,26 @@
         sim.agent_registry.households = self.households
         sim.agent_registry.firms = self.firms
         sim.goods_data = self.goods_data
 
         # Ensure sim.agents is initialized
         if not sim.agents:
             sim.agents = {}
 
-        # 1. Household Atomic Registration
-        for hh in sim.households:
-            sim.agents[hh.id] = hh
-            sim.agent_registry.register(hh)
-
-            # Guarantee Settlement Account Existence
-            sim.settlement_system.register_account(sim.bank.id, hh.id)
-            hh.settlement_system = sim.settlement_system
-
-            if hasattr(hh, 'demographic_manager'):
-                hh.demographic_manager = sim.demographic_manager
-
-        # 2. Firm Atomic Registration
-        for firm in sim.firms:
-            sim.agents[firm.id] = firm
-            sim.agent_registry.register(firm)
-
-            # Guarantee Settlement Account Existence BEFORE Bootstrapper
-            sim.settlement_system.register_account(sim.bank.id, firm.id)
-            firm.settlement_system = sim.settlement_system
+        # Wrap in batch_mode to prevent UI/event freezing during mass registration
+        with sim.world_state.global_registry.batch_mode():
+            # 1. Household Atomic Registration
+            for hh in sim.households:
+                sim.agents[hh.id] = hh
+                sim.agent_registry.register(hh)
+                sim.settlement_system.register_account(sim.bank.id, hh.id)
+                hh.settlement_system = sim.settlement_system
+                if hasattr(hh, 'demographic_manager'):
+                    hh.demographic_manager = sim.demographic_manager
+
+            # 2. Firm Atomic Registration
+            for firm in sim.firms:
+                sim.agents[firm.id] = firm
+                sim.agent_registry.register(firm)
+                sim.settlement_system.register_account(sim.bank.id, firm.id)
+                firm.settlement_system = sim.settlement_system
```

## 4. 🚨 [Conceptual Debt]
- **Chronological Order Loss**: Batched notifications emit only the *final* value of a modified key, losing intermediate changes. For initialization this is an intentional optimization. However, any systems relying on observing intermediate states inside a batched block will miss those ticks.
- **Observer Execution Order**: Batched notifications execute strictly when the outermost context exits. This might defer updates longer than an inner function expects if the context is held open excessively.

## 5. 검증 계획 (Testing & Verification Strategy)
- **New Test Cases**:
  - `test_global_registry_batch_mode_deferral`: Verify `on_registry_update` is NOT called while inside the `batch_mode` block.
  - `test_global_registry_batch_mode_deduplication`: Verify that if the same key is modified 5 times in a block, the observer is only called once on exit with the 5th value.
  - `test_global_registry_batch_mode_nested`: Verify that `_batch_depth` prevents firing until the outermost context exits.
- **Existing Test Impact**: Tests expecting immediate `_notify` during mass updates inside `batch_mode` will fail. None should exist since `batch_mode` is a new optimization.
- **Integration Check**: Verify that `_init_phase4_population` runs cleanly without UI freezing and that any agents successfully register with correct values propagated to listeners afterward.

## 6. Mocking 가이드
- Mock instances of `IGlobalRegistry` must support the `batch_mode` context manager:
  ```python
  import contextlib
  
  @contextlib.contextmanager
  def dummy_batch_mode():
      yield
  
  mock_registry.batch_mode = dummy_batch_mode
  ```
- Use `golden_households` and `golden_firms` fixtures when testing population injection.

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **DTO/DAO Interface Impact**: Adding `batch_mode` to `IGlobalRegistry`. Ensure any custom implementations of `IGlobalRegistry` (like test stubs or proxy registries) are updated to avoid `NotImplementedError`.
- **테스트 영향도**: `sim.world_state.global_registry` is heavily mocked in tests. All tests that call `_init_phase4_population` with a mocked registry will now raise `AttributeError` if `batch_mode` isn't mocked. 
- **선행 작업 권고**: Ensure `GlobalRegistry` is initialized and attached to `sim.world_state` before `Phase 4` is called (which it already is in Phase 1).

## 8. 🚨 Mandatory Reporting Verification
Jules **MUST** report any technical debt, architectural issues, or discoveries made during this task to an independent file at `communications/insights/WO-SPEC-HANG-FIX-BATCH-NOTIFY.md`. Failure to document insights in this file will result in mission rejection.
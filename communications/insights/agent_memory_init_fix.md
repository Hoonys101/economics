# Technical Insight Report: BaseAgent Memory Initialization Fix

## 1. Problem Phenomenon
When running the simulation server (`python server.py`), the application crashes with an `AttributeError`.

**Symptoms:**
- Startup failure.
- Stack trace pointing to `AttributeError: 'BaseAgent' object has no attribute 'memory_v2'`.
- This occurs when subclasses (like `Household` or `Firm`) attempt to access `self.memory_v2`, typically during initialization (e.g., logging a "BIRTH" event).

**Context:**
The `memory_v2` attribute is expected to hold an instance of `MemoryV2Interface` for logging agent lifecycle events.

## 2. Root Cause Analysis
The `BaseAgent` class in `simulation/base_agent.py` accepts a `memory_interface` argument in its `__init__` method, but it fails to assign this argument to an instance attribute (e.g., `self.memory_v2`).

```python
# simulation/base_agent.py (Current)
def __init__(self, ..., memory_interface: Optional["MemoryV2Interface"] = None):
    # ...
    # Missing: self.memory_v2 = memory_interface
```

As a result, instances of `BaseAgent` (and its subclasses) do not have the `memory_v2` attribute. When subclasses attempt to check `if self.memory_v2:` (as seen in `Household.__init__` and `Firm.liquidate_assets`), Python raises an `AttributeError` because the attribute doesn't exist (it's not `None`, it's just missing).

Additionally, the `Firm` class in `simulation/firms.py` does not accept `memory_interface` in its `__init__` method, nor does it pass it to the `super().__init__` call. This means even if `BaseAgent` were fixed, `Firm` instances would always have `memory_v2` as `None` (default), preventing dependency injection of the memory interface for Firms.

## 3. Solution Implementation Details
1.  **Fix `BaseAgent`**: Update `simulation/base_agent.py` to explicitly assign `self.memory_v2 = memory_interface` in the `__init__` method.
2.  **Update `Firm`**: Update `simulation/firms.py` to:
    - Accept `memory_interface: Optional["MemoryV2Interface"] = None` in `__init__`.
    - Pass this argument to `super().__init__`.
3.  **Verify `Household`**: Confirm `Household` passes `**kwargs` to `super().__init__`, which correctly handles `memory_interface` without explicit signature changes.

## 4. Lessons Learned & Technical Debt
- **Lesson**: When adding optional dependencies to a base class, ensure all subclasses can propagate these dependencies, either via explicit arguments or `**kwargs`.
- **Lesson**: Dependency injection in `__init__` must be followed by assignment to `self` to be useful.
- **Technical Debt**: The `BaseAgent` initialization signature is growing. Consider using a configuration object or a builder pattern if more dependencies are added.
- **Technical Debt**: `Household` uses `**kwargs` which masks the explicit dependencies it requires from `BaseAgent`. Explicit arguments are generally preferred for clarity and type checking, though `**kwargs` offers flexibility.

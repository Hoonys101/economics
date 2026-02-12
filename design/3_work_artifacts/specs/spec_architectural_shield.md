# Implementation Spec: Zero-Tolerance Protocol Enforcement
**Mission ID**: `PH15-SHIELD-GUARD`
**Author**: Antigravity (derived from Gemini Scribe)
**Recipient**: Jules (Lead Developer)
**Date**: 2026-02-12

---

## 1. Overview
This specification details the implementation of runtime guards to enforce architectural purity and the final retirement of legacy financial interfaces. Focus is on preventing "Ghost Money" and direct state manipulation.

---

## 2. Module 1: `@enforce_purity` Runtime Protocol Shield
**Addresses**: `TD-ENFORCE-NONE`

### 2.1. API & Decorator Specification (`modules/common/protocol.py`)

A new decorator to block unauthorized calls to protected methods.

```python
# In modules/common/protocol.py
import inspect
import os
from functools import wraps

AUTHORIZED_MODULES = [
    "modules/finance/",
    "modules/governance/",
    "modules/government/",
]

IS_PURITY_CHECK_ENABLED = os.environ.get("ENABLE_PURITY_CHECKS", "false").lower() == "true"

def enforce_purity(allowed_modules: list = AUTHORIZED_MODULES):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not IS_PURITY_CHECK_ENABLED:
                return func(*args, **kwargs)

            caller_frame = inspect.stack()[1]
            caller_filepath = os.path.abspath(caller_frame.filename)
            # ... path normalization logic ...
            is_authorized = any(relative_caller_path.startswith(mod) for mod in allowed_modules)

            if not is_authorized:
                raise ProtocolViolationError(f"Unauthorized call to '{func.__name__}'")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 2.2. Usage
Apply to critical `SettlementSystem` and `InventoryManager` methods (e.g., `transfer`, `mutate_slot`).

### 2.3. Testing
Create `tests/common/test_protocol.py` to verify that unauthorized callers are successfully blocked when the shield is enabled.

---

## 3. Module 2: Migration & Retirement of `IFinancialEntity`
**Addresses**: `TD-ARCH-LEAK-PROTI`

### 3.1. Problem
`IFinancialEntity` is a legacy interface that allowed direct `deposit()`/`withdraw()` calls on agents. This must be replaced with `SettlementSystem` queries.

### 3.2. Migration Strategy

| Old Pattern | New Pattern |
| :--- | :--- |
| `entity.deposit(amount)` | `settlement_system.transfer(source, entity, amount, ...)` |
| `balance = entity.get_balance()` | `balance = settlement_system.get_balance(entity.id)` |

### 3.3. Action Plan
1. **Ripgrep Search**: Find all `IFinancialEntity` occurrences.
2. **Refactor Call Sites**: Update logic to use `SettlementSystem` instead of calling agent methods directly.
3. **Delete Interface**: Once all usages are cleared, delete `IFinancialEntity` from `modules/finance/api.py`.

---

## 4. Mandatory Reporting
Final findings and performance overhead analysis of the decorator must be logged to `communications/insights/PH15-SHIELD-GUARD.md`.

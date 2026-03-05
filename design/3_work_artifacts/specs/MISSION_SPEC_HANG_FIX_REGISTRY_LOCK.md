# MISSION_SPEC: Phase B - AccountRegistry Thread Safety
**Mission Key**: WO-SPEC-HANG-FIX-REGISTRY-LOCK

## 1. Goal
Add thread-safety to `AccountRegistry` using `threading.RLock`. This prevents race conditions and state corruption in `defaultdict(set)` mutations during multi-threaded initialization (Phase 4).

## 2. Rationale
멀티스레드 환경에서 `register_account`와 `deregister_account`가 동시에 수행될 경우, `defaultdict`가 새로운 키를 생성하는 도중이거나 `set`에 데이터를 추가하는 도중에 충돌이 발생할 수 있습니다. 이는 "Silent Clog" 또는 데이터 오염의 원인이 됩니다.

## 3. Implementation Details

### A. Lock Initialization
`__init__` 메서드에서 `self._lock = threading.RLock()`을 초기화합니다.

### B. Method Wrapping
`register_account`, `deregister_account`, `remove_agent_from_all_accounts` 등 상태를 변경하는 모든 메서드를 `with self._lock:`으로 보호합니다.
`get_account_holders`, `get_agent_banks` 등 단순 조회 메서드도 데이터 일관성을 위해 락을 사용하는 것이 안전합니다.

## 4. Code Diff

```python
--- modules/finance/registry/account_registry.py
+++ modules/finance/registry/account_registry.py
@@ -1,4 +1,5 @@
-from typing import Dict, List, Set
+import threading
+from typing import Dict, List, Set, Any
 from collections import defaultdict
 from modules.simulation.api import AgentID
 from modules.finance.api import IAccountRegistry
@@ -10,45 +11,51 @@
 
     def __init__(self) -> None:
+        self._lock = threading.RLock()
         # BankID -> Set[AgentID]
         self._bank_depositors: Dict[AgentID, Set[AgentID]] = defaultdict(set)
         # AgentID -> Set[BankID]
         self._agent_banks: Dict[AgentID, Set[AgentID]] = defaultdict(set)
 
     def register_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
         """Registers an account link between a bank and an agent."""
-        self._bank_depositors[bank_id].add(agent_id)
-        self._agent_banks[agent_id].add(bank_id)
+        with self._lock:
+            self._bank_depositors[bank_id].add(agent_id)
+            self._agent_banks[agent_id].add(bank_id)
 
     def deregister_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
         """Removes an account link between a bank and an agent."""
-        if bank_id in self._bank_depositors:
-            self._bank_depositors[bank_id].discard(agent_id)
-            if not self._bank_depositors[bank_id]:
-                del self._bank_depositors[bank_id]
-
-        if agent_id in self._agent_banks:
-            self._agent_banks[agent_id].discard(bank_id)
-            if not self._agent_banks[agent_id]:
-                del self._agent_banks[agent_id]
+        with self._lock:
+            if bank_id in self._bank_depositors:
+                self._bank_depositors[bank_id].discard(agent_id)
+                if not self._bank_depositors[bank_id]:
+                    del self._bank_depositors[bank_id]
+
+            if agent_id in self._agent_banks:
+                self._agent_banks[agent_id].discard(bank_id)
+                if not self._agent_banks[agent_id]:
+                    del self._agent_banks[agent_id]
 
     def get_account_holders(self, bank_id: AgentID) -> List[AgentID]:
         """Returns a list of all agents holding accounts at the specified bank."""
-        if bank_id in self._bank_depositors:
-            return list(self._bank_depositors[bank_id])
-        return []
+        with self._lock:
+            if bank_id in self._bank_depositors:
+                return list(self._bank_depositors[bank_id])
+            return []
 
     def get_agent_banks(self, agent_id: AgentID) -> List[AgentID]:
         """Returns a list of banks where the agent holds an account."""
-        if agent_id in self._agent_banks:
-            return list(self._agent_banks[agent_id])
-        return []
+        with self._lock:
+            if agent_id in self._agent_banks:
+                return list(self._agent_banks[agent_id])
+            return []
 
     def remove_agent_from_all_accounts(self, agent_id: AgentID) -> None:
         """Removes an agent from all bank account indices."""
-        if agent_id in self._agent_banks:
-            # Copy to avoid modification during iteration
-            banks = list(self._agent_banks[agent_id])
-            for bank_id in banks:
-                self.deregister_account(bank_id, agent_id)
+        with self._lock:
+            if agent_id in self._agent_banks:
+                # Copy to avoid modification during iteration
+                banks = list(self._agent_banks[agent_id])
+                for bank_id in banks:
+                    self.deregister_account(bank_id, agent_id)
 ```

## 5. Verification Plan
- **Unit Test**: `tests/finance/test_account_registry_threads.py`를 생성하여 10개 스레드에서 동시에 1,000번의 `register/deregister`를 수행하고 최종 상태의 정합성(Zero-Sum Integrity)을 확인합니다.
- **Regression**: 기존 `tests/finance/test_account_registry.py` 패스 확인.

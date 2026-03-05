# MISSION_SPEC: Phase D+E - Adapter Protocol & Logging Guard
**Mission Key**: WO-SPEC-HANG-FIX-ADAPTER-OPT

## 1. Goal
Optimize performance and prevent lock contention in the finance adapter layer. 
1. **Phase D**: Replace or cache expensive `isinstance()` checks on `@runtime_checkable` protocols in `RegistryAccountAccessor`.
2. **Phase E**: Downgrade `logger.info` in adapter `withdraw` methods to `logger.debug` to avoid synchronous logging `RLock` contention during mass initialization.

## 2. Rationale
1. **Protocol Overhead**: `isinstance(agent, IFinancialAgent)`는 프로토콜 시그니처를 매번 검사하므로 10,000회 루프에서 심각한 오버헤드를 유발합니다.
2. **Logging Contention**: AI 엔진이 백그라운드 스레드에서 모델을 로드하는 동안 메인 스레드가 대량 로깅(info)을 수행하면, Python `logging` 모듈의 내부 `RLock`에서 경합이 발생하여 시뮬레이션이 멈추는 현상이 관찰되었습니다.

## 3. Implementation Details

### A. Protocol Optimization
`RegistryAccountAccessor`에서 `isinstance` 결과를 캐싱하거나, 에이전트 클래스 자체에 미리 정의된 프로토콜 식별자(예: `_is_financial_agent = True`)를 사용하여 `hasattr`로 확인하는 방식을 도입합니다.

### B. Logging Level Downgrade
`FinancialEntityAdapter.withdraw`와 `FinancialAgentAdapter.withdraw`의 로깅 레벨을 `info`에서 `debug`로 조정합니다.

## 4. Code Diff

```python
--- modules/finance/transaction/adapter.py
+++ modules/finance/transaction/adapter.py
@@ -17,7 +17,7 @@
         self.entity.deposit(amount, currency)
 
     def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
-        logger.info(f"ADAPTER_DEBUG | Entity {self.entity.id} Withdraw {amount}")
+        logger.debug(f"ADAPTER_DEBUG | Entity {self.entity.id} Withdraw {amount}")
         self.entity.withdraw(amount, currency)
 
     def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
@@ -42,7 +42,7 @@
         self.agent._deposit(amount, currency)
 
     def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
-        logger.info(f"ADAPTER_DEBUG | Agent {self.agent.id} Withdraw {amount}")
+        logger.debug(f"ADAPTER_DEBUG | Agent {self.agent.id} Withdraw {amount}")
         self.agent._withdraw(amount, currency)
 
     def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
@@ -62,29 +62,39 @@
     def __init__(self, registry: IAgentRegistry):
         self.registry = registry
+        # Dictionary to cache protocol check results: AgentClass -> ProtocolType (Agent/Entity/None)
+        self._protocol_cache: Dict[type, str] = {}
 
     def _get_agent(self, account_id: AgentID) -> Any:
@@ -74,17 +84,33 @@
     def get_participant(self, account_id: AgentID) -> ITransactionParticipant:
         agent = self._get_agent(account_id)
         if agent is None:
             raise InvalidAccountError(f"Account (Agent) not found: {account_id}")
 
-        # Check IFinancialAgent first as it supports multi-currency balance check better
-        if isinstance(agent, IFinancialAgent):
-            return FinancialAgentAdapter(agent)
-
-        if isinstance(agent, IFinancialEntity):
-            return FinancialEntityAdapter(agent)
+        agent_class = type(agent)
+        if agent_class in self._protocol_cache:
+            ptype = self._protocol_cache[agent_class]
+            if ptype == 'agent': return FinancialAgentAdapter(agent)
+            if ptype == 'entity': return FinancialEntityAdapter(agent)
+        else:
+            if isinstance(agent, IFinancialAgent):
+                self._protocol_cache[agent_class] = 'agent'
+                return FinancialAgentAdapter(agent)
+            if isinstance(agent, IFinancialEntity):
+                self._protocol_cache[agent_class] = 'entity'
+                return FinancialEntityAdapter(agent)
+            self._protocol_cache[agent_class] = 'none'
 
         raise InvalidAccountError(f"Agent {account_id} does not implement IFinancialAgent or IFinancialEntity.")
```

## 5. Verification Plan
- **Performance Test**: `operation_forensics.py` 실행 시 Phase 4에서 로깅 경합이나 프로토콜 오버헤드로 인한 지연이 발생하지 않는지 확인합니다.
- **Unit Test**: `tests/finance/test_adapter_caching.py`를 생성하여 캐싱 로직이 각기 다른 타입의 에이전트를 올바르게 구분하는지 확인합니다.

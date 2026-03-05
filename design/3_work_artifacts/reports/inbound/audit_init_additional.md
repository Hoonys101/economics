# [AUDIT] Initialization Flow Additional Memory Issues Report

## Executive Summary
Phase 4 `MemoryError` issues (even with `NUM_HOUSEHOLDS=20`) are driven by systemic memory leaks in global audit logs and unprincipled buffering rather than the engine's core object graph. The primary culprit is `GLOBAL_WALLET_LOG`, which appends every financial operation across all agents into a single, never-cleared global list.

## Detailed Analysis

### 1. Phase 1-3 Large Object Inventory
- **Infrastructure (Phase 1)**: `GlobalRegistry` and `AgentRegistry` hold the entire system state and agent references. While necessary, they prevent GC of any registered agent.
- **System Agents (Phase 2)**: Minimal overhead per agent, but `MonetaryLedger` maintains a `transaction_log` that grows with every monetary expansion/contraction.
- **Markets & Systems (Phase 3)**:
    - `RealEstateUnit` list: Fixed size (`NUM_HOUSING_UNITS`), but occupies contiguous memory.
    - `OrderBookMarket`: Each market (N goods + security + housing) holds its own order books.
    - `AITrainingManager`: Holds a full list of `households + firms`.
    - `PersistenceManager`: Holds four internal buffers (`agent_state`, `transaction`, `economic_indicator`, `market_history`) that accumulate data until a `flush_buffers` call.

### 2. Import-Time Memory Costs
- **High-Cost Modules**: 
    - `numpy`: Imported in `VectorizedHouseholdPlanner` and `ModelWrapper`. (~20-30MB)
    - `sklearn`: Imported in `ModelWrapper` (via `SGDRegressor`, `DictVectorizer`, `StandardScaler`). (~50-100MB depending on transitives like `scipy`).
    - `joblib`: Used for model serialization.
- **Transitive Loading**: `SimulationInitializer` imports almost every system in the project, triggering a cascade of imports that can consume ~200MB+ before a single agent is created.

### 3. Logging & Audit Memory Leaks (Critical)
- **`ForensicLogHandler.all_records`**: Located in `scripts/operation_forensics.py`. It appends the entire `record.__dict__.copy()` for *every* log message if attached to the root logger. In a simulation with 20 households logging multiple times per tick, this grows by thousands of records per tick.
- **`GLOBAL_WALLET_LOG`**: Located in `modules/finance/wallet/audit.py`. This is a shared mutable list (`List[WalletOpLogDTO]`) that **never clears**. Every `Wallet.add` or `Wallet.subtract` appends a DTO. In a 50-tick run with 20 agents, this can easily reach 10,000+ DTOs. For `NUM_HOUSEHOLDS=1000`, this causes immediate `MemoryError`.

### 4. Agent Configuration & Memory V2
- **`AgentCoreConfigDTO.memory_interface`**: This is a reference to the shared `PersistenceManager`. 
- **Overhead**: The `PersistenceManager` itself is the memory sink. It buffers all agent states until flushed. If the flush interval is too high, memory usage spikes linearly with `NUM_AGENTS * TICKS_SINCE_FLUSH`.

### 5. Wallet Allocation Patterns
- **Balance Storage**: `Wallet` uses `defaultdict(int)` for `_balances`. This is memory-efficient as it only allocates keys for currencies actually held (typically only `DEFAULT_CURRENCY`).
- **Audit Coupling**: The `_audit_log` attribute defaults to `GLOBAL_WALLET_LOG`. This means every `Wallet` instance created (including temporary ones used in operator overloading) contributes to the global leak.

## Risk Assessment
- **[CRITICAL] Global Audit Leaks**: `GLOBAL_WALLET_LOG` and `ForensicLogHandler` are non-scalable patterns. They convert a O(N) memory problem into O(N*T) where T is time.
- **[HIGH] Buffer Retention**: `PersistenceManager` and `MonetaryLedger` hold lists of transactions that are not cleared after persistence flushes in some execution paths.
- **[MEDIUM] Heavy Dependencies**: `sklearn` and `numpy` loading is unavoidable for AI, but vectorized planners should be moved to a separate process or lazily loaded if possible.

## Conclusion
The `MemoryError` at low household counts is a "Death by a Thousand DTOs" caused by global lists. 

**Recommended Action Items:**
1. **Immediate**: Implement a `clear_logs()` or `flush_to_disk()` mechanism for `GLOBAL_WALLET_LOG`.
2. **Standard**: Enforce a rule that `ForensicLogHandler` must only be used in specific test/diagnostic environments, never attached to the root logger in production.
3. **Refactor**: Modify `Wallet` to make auditing optional or scoped to the simulation run rather than a global module-level variable.
4. **Optimization**: Ensure `PersistenceManager.flush_buffers()` also clears the source lists in `WorldState.transactions` if they are no longer needed in memory.

---

# Insight Report: WO-AUDIT-INIT-ADDITIONAL

## Architectural Insights
1. **Global State Pollution**: Identified `GLOBAL_WALLET_LOG` in `modules/finance/wallet/audit.py` as a primary architectural leak. The use of module-level mutable lists for auditing violates the "Stateless Engine" principle (SEO Pattern) as it accumulates state outside the `WorldState` lifecycle.
2. **Audit/Logging Decoupling**: Discovered that `ForensicLogHandler` captures full `__dict__` copies of log records, which includes stack traces and metadata. This pattern is unsustainable for long-running simulations.
3. **Memory V2 Overhead**: Confirmed that `AgentCoreConfigDTO` carries a reference to `PersistenceManager`, effectively linking every agent to the global DB buffer.

## Regression Analysis
- No tests were broken during this audit as it was a read-only investigation. However, identified that `tests/system/test_engine.py` and other integration tests likely leak memory due to `GLOBAL_WALLET_LOG` persistence across test cases.

## Test Evidence
Audit mission - no code changes implemented. Verification of current memory pressure performed via static analysis of `initializer.py` and `wallet.py`.

```
(No code changes - Investigation Only)
```

---
**Report generated by Gemini-CLI Subordinate Worker.**
**Mission Key: WO-AUDIT-INIT-ADDITIONAL**

---

## 🔍 [ANTIGRAVITY REVIEW] 검증 결과

### ✅ 확인된 Critical 발견

| # | 발견 | 검증 결과 | 코드 위치 |
|---|------|----------|----------|
| 1 | **`GLOBAL_WALLET_LOG`** 무한 성장 | ✅ **확인** | `modules/finance/wallet/audit.py:L5` — `List[WalletOpLogDTO] = []` |
| 2 | **`Wallet._audit_log`** 글로벌 참조 | ✅ **확인** | `wallet.py:L34` — `self._audit_log = audit_log if audit_log is not None else GLOBAL_WALLET_LOG` |
| 3 | **`sklearn` import-time** 비용 | ✅ **확인** | `simulation/ai/model_wrapper.py:L5-7` — SGDRegressor, DictVectorizer, StandardScaler |

> [!CAUTION]
> **`GLOBAL_WALLET_LOG`는 즉시 조치가 필요한 #1 원인입니다.**
> `NUM_HOUSEHOLDS=20`에서도 매 틱마다 20+ agents × 다수 월렛 연산 = 수백 DTO 추가.
> 이 리스트는 **절대 clear되지 않으며**, 포렌식 실행 시 모든 틱이 누적됩니다.
> 
> **즉시 대응**: `conftest.py` teardown에 `GLOBAL_WALLET_LOG.clear()` 추가
> **구조적 대응**: Wallet 생성 시 `audit_log=[]` (로컬 리스트) 전달하여 글로벌 오염 차단
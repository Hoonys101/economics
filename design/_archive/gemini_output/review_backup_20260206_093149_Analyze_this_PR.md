# 🔍 Summary
이번 변경은 시뮬레이션의 핵심적인 M2 통화량 무결성 문제를 해결하는 데 중점을 둡니다. 은행 예치금(Deposits)과 지급준비금(Reserves)의 이중 계산 오류를 바로잡아 M2 계산 공식을 수정하였고, 에이전트 사망 시에도 자산이 계속 집계되던 '유령 에이전트' 문제를 해결하기 위해 이벤트 기반의 `StrictCurrencyRegistry` 패턴을 도입했습니다. 이로써 통화량 집계의 정확성과 시스템 안정성이 크게 향상되었습니다.

# 🚨 Critical Issues
없음.

# ⚠️ Logic & Spec Gaps
- **`modules/finance/saga_handler.py`**: 모기지 대출 실행 및 롤백 시, `credit_creation`/`credit_destruction` 트랜잭션을 수동으로 `world_state.transactions` 리스트에 직접 추가하고 있습니다. 이는 표준 트랜잭션 처리 파이프라인을 우회하는 방식으로, 향후 리팩토링 시 모든 트랜잭션이 일관된 프로세서를 통해 생성되도록 개선하는 것을 고려해야 합니다. 현재로서는 기능 구현을 위해 불가피한 측면이 있으나, 잠재적인 기술 부채로 인지할 필요가 있습니다.
- **`simulation/ai/ai_training_manager.py`**: 자산(`assets`)이 `dict` 또는 `float`일 수 있는 상황을 처리하기 위한 로직이 여러 함수에 중복되어 있습니다. (`max`, `sorted` 등). `assets`의 자료구조 변경에 대응하는 것은 좋으나, 자산 가치를 가져오는 헬퍼(helper) 함수를 만들어 중복을 제거하는 것이 바람직합니다.

# 💡 Suggestions
- **`WorldState` 클래스 리팩토링**: `Pulse_Integrity_Report.md`에서 지적된 바와 같이, `WorldState`가 너무 많은 책임을 갖는 "God Class"가 되어가고 있습니다. 이번에 추가된 `register_currency_holder`/`unregister_currency_holder`와 관련 로직(`currency_holders`, `_currency_holders_set`)은 별도의 `CurrencyRegistry` 클래스로 분리하여 `WorldState`의 단일 책임 원칙(SRP)을 강화하는 것이 좋습니다.
- **`test_bank.py`의 자산 접근 방식 통일**: 테스트 코드에서 은행 자산을 조회할 때 `bank_instance.assets["USD"]` 와 같이 딕셔너리 형태로 접근하는 부분과, `bank_instance.assets` 로 직접 접근하는 부분이 혼재되어 있습니다. `assets`가 딕셔너리로 변경되었으므로, 모든 테스트에서 일관되게 키(`"USD"`)를 통해 접근하도록 수정하여 테스트의 명확성을 높여야 합니다.

# 🧠 Implementation Insight Evaluation
- **Original Insight**:
```markdown
# Technical Insight Report: Operation Pulse Integrity

## 1. Problem Phenomenon
During stress testing (Tick 1-100), the simulation exhibited severe monetary instability:
*   **M2 Leak:** Significant positive M2 drift (leak) detected, reaching ~177k by Tick 90 in early runs.
*   **Crash:** A `TypeError` at Tick 50 (NULL seller_id) and other crashes related to inheritance and database logging.
*   **Ghost Agents:** Dead agents remained in the `currency_holders` list, causing their assets to be counted in M2 even after liquidation/inheritance.

## 2. Root Cause Analysis
### 2.1 M2 Leak & Double Counting
The primary M2 leak was caused by a combination of:
*   **Bank Reserves Double Counting:** M2 was calculated as `M0 + Deposits`, but M0 implicitly included Bank Reserves (since Bank was a currency holder). Since Deposits are backed by Reserves, adding both doubles the count of that money.
*   **Implicit Transfers:** Bank withdrawals and deposits updated logical balances but didn't always physically transfer cash between `Bank.wallet` and `Customer.wallet` in a strictly synchronized way (fixed by handler registration).
*   **Profit Remittance:** Bank profits (interest income) were accumulated but not remitted to the Government, effectively creating a sink or source depending on how M2 was tracked vs. authorized delta.

### 2.2 Ghost Agents (Lifecycle Management)
*   The `TickOrchestrator` rebuilt the `currency_holders` list every tick by iterating over `state.agents`.
*   However, `state.agents` often retained references to inactive/dead agents for transactional history or logging.
*   This caused dead agents to be re-added to the M2 calculation, leading to "Zombie Money" being counted.

### 2.3 Crashes
*   **Tick 50 NULL seller_id:** `InheritanceManager` assigned `None` to `seller_id` for system-mediated transfers, violating database `NOT NULL` constraints.
*   **Logging Crash:** Passing a `dict` (M2 breakdown) to a SQL logger expecting a `float` or JSON string caused a `sqlite3` error.

## 3. Solution Implementation Details
### 3.1 Strict Currency Registry
*   Implemented `StrictCurrencyRegistry` pattern in `WorldState.py`.
*   Introduced `_currency_holders_set` for O(1) membership tracking.
*   Added `register_currency_holder` and `unregister_currency_holder` methods.
*   Updated `TickOrchestrator` to **stop rebuilding** the list every tick. It now relies on `LifecycleManager` to maintain the list incrementally.

### 3.2 Immediate Lifecycle Suture
*   Updated `LifecycleManager` to call `state.unregister_currency_holder(agent)` **immediately** upon agent death or liquidation.
*   This eliminates the "Ghost Agent" window where dead agents could be counted in M2.

### 3.3 M2 Formula Correction
*   Updated `EconomicIndicatorTracker.py` to strictly implement the formula: `M2 = (M0 - Bank Reserves) + Deposits`.
*   This ensures that `M0` correctly represents the Monetary Base (Circulation + Reserves), while `M2` correctly represents Broad Money (Circulation + Deposits).

### 3.4 Transaction Handlers
*   Registered `bank_profit_remittance` handler to ensure bank profits move to Government.
*   Registered `deposit` and `withdrawal` handlers to ensure physical cash movement accompanies logical deposit updates.

## 4. Lessons Learned & Technical Debt
*   **Lesson:** "Rebuilding from source" (like `_rebuild_currency_holders`) is dangerous if the source (`state.agents`) has a different lifecycle (e.g., archival retention) than the derived list (`active_currency_holders`). Strict, event-driven maintenance is safer for critical registries.
*   **Lesson:** M2 definitions must be explicit about "Reserves" vs. "Circulation". Ambiguity leads to double-counting.
*   **Tech Debt:** `SettlementSystem` still has some abstraction leaks (direct property access).
*   **Tech Debt:** `WorldState` is becoming a God Class; `StrictCurrencyRegistry` logic could be extracted to a standalone component.
*   **Residual Drift:** A small residual M2 drift (~1.6% of total) persists, likely due to `bond_repayment` transactions between Government and Commercial Bank not being tracked as M2 contraction in `MonetaryLedger`. Future work should tag these transactions explicitly.
```
- **Reviewer Evaluation**:
  - **정확성 및 깊이**: 작성된 인사이트 보고서는 매우 훌륭합니다. M2 통화량 누수라는 복잡한 문제의 근본 원인을 '지급준비금 이중 계산', '유령 에이전트(Lifecycle 불일치)', '암묵적 현금 이전 누락'이라는 세 가지 핵심 축으로 정확히 분석했습니다.
  - **해결책의 타당성**: 제시된 해결책인 'M2 공식 수정', '엄격한 통화 보유자 등록부(Strict Currency Registry) 도입', '금융 트랜잭션 핸들러 등록'은 분석된 원인에 직접적으로 대응하는 매우 적절하고 구조적인 해결책입니다. 특히 매 틱마다 리스트를 재생성하는 불안정한 방식에서 벗어나, 이벤트 기반으로 등록/해제하는 아키텍처 개선은 시스템의 안정성과 성능을 모두 향상시키는 뛰어난 결정입니다.
  - **기술 부채 인식**: 해결 과정에서 발견된 `WorldState`의 God Class 문제나, 여전히 남아있는 미세한 M2 변동(Residual Drift)의 원인까지 추적하여 기술 부채로 명시한 점은 프로젝트의 장기적인 건강성을 고려하는 높은 수준의 엔지니어링 역량을 보여줍니다. 이 보고서는 단순한 버그 수정을 넘어 시스템에 대한 깊은 이해와 통찰을 담고 있습니다.

# 📚 Manual Update Proposal
작성된 인사이트는 프로젝트의 중요한 기술적 자산입니다. 특히 해결되지 않은 '잔여 변동성'은 추후 다른 개발자가 인지해야 할 중요한 정보입니다.
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
```markdown
## TD-035: Residual M2 Drift from Bond Transactions

| 항목 | 내용 |
| --- | --- |
| **현상** | M2 무결성 개선 작업 이후에도 미세한 M2 변동(Drift)이 지속됨. |
| **원인** | `MonetaryLedger`가 정부(Government)와 상업은행(Commercial Bank) 간의 `bond_repayment`(채권 상환) 트랜잭션을 M2 축소(Contraction)로 집계하지 않기 때문으로 추정됨. 현재 로직은 정부와 민간(가계, 기업) 간의 채권 거래만 M2 변동으로 추적하고 있음. |
| **조치 계획** | `MonetaryLedger`의 M2 확장/축소 조건에 정부-은행 간 채권 관련 트랜잭션(`bond_repayment` 등)을 명시적으로 추가하여, 모든 통화량 변동이 정확히 추적되도록 수정해야 함. |
| **관련 미션** | Pulse_Integrity_Fix |
```

# ✅ Verdict
**APPROVE**

매우 중요한 시스템 무결성 문제를 정확히 진단하고, 구조적으로 우수한 해결책을 적용했으며, 그 과정을 상세하고 깊이 있는 인사이트 보고서로 문서화했습니다. 이는 다른 개발자들에게 훌륭한 귀감이 되는 작업입니다.

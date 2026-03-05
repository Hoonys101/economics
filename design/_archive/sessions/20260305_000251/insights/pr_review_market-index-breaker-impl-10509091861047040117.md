🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\gemini-output\review\pr_diff_market-index-breaker-impl-10509091861047040117.txt
📖 Attached context: config\economy_params.yaml
📖 Attached context: modules\market\api.py
📖 Attached context: simulation\initialization\initializer.py
📖 Attached context: simulation\markets\order_book_market.py
📖 Attached context: simulation\markets\stock_market.py
📖 Attached context: simulation\orchestration\tick_orchestrator.py
📖 Attached context: simulation\world_state.py
📖 Attached context: tests\integration\scenarios\diagnosis\conftest.py
📖 Attached context: tests\unit\markets\test_order_book_market.py
📖 Attached context: tests\unit\markets\test_order_book_market_cancellation.py
📖 Attached context: tests\unit\markets\test_stock_market_cancellation.py
📖 Attached context: tests\unit\test_markets_v2.py
📖 Attached context: tests\unit\test_stock_market.py
🚀 [GeminiWorker] Running task with manual: git-review.md

📝 [Review Report]
============================================================
# 🐙 Gemini CLI System Prompt: Code Review Report

## 1. 🔍 Summary
`IndexCircuitBreaker`를 구현하여, 특정 틱(Tick)마다 `TickOrchestrator`에서 계산된 거시 지수(Market Index)의 하락폭에 따라 주식 및 상품 시장의 매칭(Matching)을 중앙 집중식으로 일시 정지(Halt)하는 기능을 추가했습니다. 의존성 주입(DI)과 DTO를 올바르게 사용하여 구조적으로 깔끔하게 구현되었습니다.

## 2. 🚨 Critical Issues
*발견된 심각한 보안 결함, 하드코딩 또는 Zero-Sum 위반 사항이 없습니다.*

## 3. ⚠️ Logic & Spec Gaps
* **Order Collection During Halt**: 현재 `match_orders`에서만 `is_active()`를 검사하여 거래 체결을 막고 있습니다. 이는 서킷 브레이커가 발동된 상태에서도 가계와 기업이 시장에 새로운 주문(Order)을 계속 제출(`place_order`)할 수 있음을 의미합니다. 실제 거래소의 '단일가 매매(Order Collection)' 기간처럼 동작하겠지만, Halt가 풀리는 즉시 엄청난 양의 거래가 일시에 체결되어 스프레드가 폭증할 수 있으므로 의도된 기획인지 확인이 필요합니다.
* **Unweighted Price Index**: `TickOrchestrator`에서 시장 지수(Index)를 계산할 때 발행 주식수(Outstanding Shares)를 곱한 시가총액(Market Cap) 가중 방식이 아닌, **단순 주가 합산(Unweighted Price Sum)** 방식을 사용하고 있습니다. 다우존스(Dow Jones) 지수와 유사한 방식이며 현재 단계에서는 문제가 없으나, 추후 거시 경제의 정확성을 위해 시가총액 가중 방식으로 개선할 여지가 있습니다.

## 4. 💡 Suggestions
* **명시적인 로그 남기기**: `TickOrchestrator`에서 `state.index_circuit_breaker.set_reference_index(total_price_index)`를 초기화할 때, 기준(Reference)이 되는 인덱스 값을 로깅해 두면 추후 디버깅과 지표 추적에 큰 도움이 될 것입니다.
* **Halt 시 Order 거부 (Optional)**: 만약 서킷 브레이커 발동 중 주문 접수 자체를 막고자 한다면, `Market.place_order()` 상단에도 `index_circuit_breaker.is_active()` 체크 로직을 추가하는 것을 고려하십시오.

## 5. 🧠 Implementation Insight Evaluation

> **Original Insight**:
> - **Goal**: Implement `IndexCircuitBreaker` to halt trading when market index drops significantly.
> - **Design Pattern**: Dependency Injection. The circuit breaker is injected into Markets (`OrderBookMarket`, `StockMarket`) and `TickOrchestrator`.
> - **State Management**: The circuit breaker maintains its own state (`is_active`, `halt_until_tick`).
> - **Fail-Open**: If `market_index` is missing, the breaker defaults to "Healthy" (True) to prevent disruption.
> - **Centralized Orchestration**: `TickOrchestrator` is responsible for calculating the unified macro index (Stock Market Cap) and updating the circuit breaker state *once per tick*. Markets only *read* the state via `is_active()`.
> - **Mocking**: Strict mocking with `spec=IIndexCircuitBreaker` is enforced for tests.
> - **Regression Analysis Bug Fix**: Previous iteration calculated index inside `OrderBookMarket` which caused 100% drop on tick 0. Moved calculation to Orchestrator using Stock Market data corrects this.

**Reviewer Evaluation**:
작성된 인사이트는 이번 구현의 핵심 구조적 결정(Centralized Orchestration, Dependency Injection)을 매우 잘 포착했습니다. 특히 Tick 0에서 시장 초기화 순서 문제로 인해 발생했던 버그(100% drop)의 원인을 파악하고 이를 `TickOrchestrator`에서의 중앙화된 통제로 해결한 경험은 매우 훌륭한 교훈(Lesson Learned)입니다. 

## 6. 📚 Manual Update Proposal (Draft)

**Target File**: `design/1_governance/architecture/standards/MARKET_STABILITY.md` (또는 신규 생성)

```markdown
### 거시 경제 안정성: 인덱스 서킷 브레이커 (Macro Index Circuit Breaker)

*   **설계 원칙**: 서킷 브레이커 로직은 개별 시장(Micro-market)에서 거시 지수(Macro-index)를 계산하지 않습니다. (Tick 0 초기화 버그 방지)
*   **중앙 통제 (Centralized Orchestration)**: 전체 시장 지수(Total Price Index 등)는 반드시 `TickOrchestrator`와 같은 상위 오케스트레이터에서 틱당 1회만 계산 및 평가되어야 합니다.
*   **상태 주입 (Read-Only Injection)**: `IndexCircuitBreaker`의 상태는 오케스트레이터가 변경하며, 각 `Market` 클래스(`OrderBookMarket`, `StockMarket`)는 주입받은 Breaker 인스턴스의 `is_active()` 메서드를 **읽기(Read) 용도로만 사용**하여 `match_orders` (체결 로직)를 조기 종료(Early Return)합니다.
*   **안전 장치 (Fail-Open)**: 지수 계산에 실패하거나 데이터가 없을 경우 시장 붕괴를 막기 위해 기본적으로 "정상(Healthy)" 상태로 Fallback 해야 합니다.
```

## 7. ✅ Verdict

**APPROVE**
(보안 결함 및 Zero-Sum 위반 없음, 상태 관리 위생과 테스트 커버리지가 우수하며 인사이트 보고서가 성공적으로 첨부되었습니다.)
============================================================
✅ Review Saved: C:\coding\economics\design\_archive\gemini_output\review_backup_20260225_152409_Analyze_this_PR.md

### 1. 🔍 Summary
이번 PR은 "고스트 머니" 현상에 의한 M2 누수를 방지하기 위해 `CentralBankSystem`에 트랜잭션 주입(Transaction Injection) 패턴을 도입하고, Orchestrator Phase를 통합했습니다. 또한 채권 상환 시 원금과 이자를 분리하여 Monetary Ledger의 정합성을 개선하였고, LLR(최종대부자) 유동성 공급 로직을 구체화했습니다.

### 2. 🚨 Critical Issues
- **매직 넘버 하드코딩 (Config Access Pattern 위반)**: `simulation/systems/central_bank_system.py`의 `check_and_provide_liquidity` 메서드 내부에서 `threshold = int(amount_needed * 1.1)`와 같이 `1.1`이라는 매직 넘버가 하드코딩되어 있습니다. 이는 Config 파일(예: `economy_params.yaml`)의 설정값을 통해 DTO/Wrapper 클래스 형태로 접근해야 합니다.
- **의존성 순수성(Dependency Purity) 위반**: `check_and_provide_liquidity` 메서드 안에서 `from modules.system.api import DEFAULT_CURRENCY` 형태의 로컬 임포트를 수행하고 있습니다. 상수는 파일 상단에 전역으로 임포트하거나 의존성 주입 패턴을 따라야 합니다.
- **Float Incursion 위험 (Zero-Sum 및 정합성 위반)**: `modules/government/components/monetary_ledger.py`에서 채권 원금을 가져올 때 `amount = float(repayment_details["principal"])` 연산을 수행합니다. 경제 엔진의 자산은 반드시 정수형 페니(integer pennies)를 유지해야 하며(`SettlementSystem`이 float를 검출하여 `FloatIncursionError`를 발생시키고 있음), `float()` 캐스팅은 화폐 정합성(Zero-Sum) 무결성을 깨뜨릴 수 있는 심각한 위험 요소입니다. 반드시 `int()`로 형변환해야 합니다.

### 3. ⚠️ Logic & Spec Gaps
- **상태 캡슐화 위반**: `CentralBankSystem.mint_and_transfer` 내에서 `target_agent.total_money_issued += amount` 코드로 에이전트의 내부 변수를 외부 시스템이 직접 수정하고 있습니다. "Stateless Engine Purity" 가이드라인에 따라, 상태 변경은 해당 에이전트 클래스의 메서드나 명시된 Engine 내부에서만 수행되어야 합니다.
- **Mock Purity 위반**: `tests/unit/test_tax_collection.py`의 `MockSettlementSystem.transfer` 모킹에서 반환값으로 원시 DTO가 아닌 `MagicMock()` 인스턴스 그 자체를 생성하여 반환하고 있습니다. 이로 인해 `MagicMock`이 트랜잭션 리스트(`WorldState.transactions` 역할)에 직접 추가되어 추후 타입 검증 및 직렬화 과정에서 실패를 유발할 수 있습니다. 실제 `Transaction` 픽스처(Fixture)나 모의 DTO를 반환하도록 수정해야 합니다.

### 4. 💡 Suggestions
- `CentralBankSystem`의 초기화 시점(`__init__`)에 `world_state.transactions`의 리스트 참조를 직접 전달받아 내부에서 `append`를 수행하는 설계(Transaction Injection Pattern)는 암묵적인 상태 변경(Side-effect)을 초래합니다. 시스템 클래스에서 생성된 Transaction 객체 자체를 리턴(Return)하고, 최상위 Orchestrator나 엔진이 명시적으로 `WorldState`에 반영하도록 아키텍처를 개선하는 것이 결합도를 낮추는 데 유리합니다.
- `WorldState.calculate_total_money`에서 ID 값을 문자열로 캐스팅(`str(holder.id)`)하여 비교하는 방식은 안전성을 높이는 임시방편이 될 수 있으나, 빈번하게 호출되는 루프 내에서는 런타임 성능을 저하시킵니다. ID 타입을 시스템 전반에 걸쳐 일관된 타입(`int` 또는 `str`)으로 통일하는 리팩토링을 제안합니다.

### 5. 🧠 Implementation Insight Evaluation

- **Original Insight**:
> # WO-WAVE5-MONETARY-FIX: M2 Integrity & Audit Restoration
> 
> ## Architectural Insights
> 
> ### 1. Ledger Synchronization via Transaction Injection
> The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`.
> 
> To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system, regardless of where in the call stack the operation occurred.
> 
> ### 2. Orchestrator Phase Consolidation
> We removed the redundant `Phase_MonetaryProcessing` from the `TickOrchestrator`. Previously, this phase attempted to process transactions independently, leading to potential double-counting or race conditions with `Phase3_Transaction`. By consolidating all transaction processing logic (including `MonetaryLedger` updates) into `Phase3_Transaction`, we ensure a strictly linear and atomic execution flow: Execute -> Verify -> Record.
> 
> ### 3. M2 Perimeter Harmonization
> We refined the definition of M2 (Total Money Supply) in `WorldState.calculate_total_money`. The `PublicManager` (ID 4) and System Agent (ID 5) are now explicitly excluded from the M2 calculation, aligning them with the Central Bank (ID 0) as "System Sinks". This prevents money held by these administrative agents (e.g., from escheatment) from being counted as circulating supply, eliminating "phantom" M2 fluctuations. ID comparisons were also robustified using string conversion to preventing type mismatch errors.
> 
> ### 4. Bond Repayment Logic
> We enhanced the `MonetaryLedger` to respect the split between Principal and Interest during bond repayments. Previously, the ledger treated the entire repayment (Principal + Interest) as money destruction (Contraction). Now, if metadata is available, only the Principal portion is counted as M0/M2 destruction, while Interest is treated as a transfer to the System (which may or may not be recycled), aligning the ledger with standard accounting practices where only asset redemption contracts the supply.
> 
> ## Regression Analysis
> No regressions are expected in agent behavior, as the changes are primarily accounting-related. The core logic of LLR and Social Policy execution remains unchanged; only the reporting of these actions has been altered. Existing tests relying on M2 consistency should now pass more reliably. The updates to `CentralBankSystem` initialization and `Government.execute_social_policy` signature were propagated to all call sites and tests.
> 
> ## Test Evidence
> All unit and integration tests passed (1033 passed, 11 skipped).
> Tests covering LLR expansion (`test_lender_of_last_resort_expansion`), asset liquidation (`test_asset_liquidation_expansion`), and tax collection (`test_atomic_wealth_tax_collection_success`) were updated and verified.

- **Reviewer Evaluation**: 
원문 인사이트는 M2 누수(Leakage)의 원인을 암묵적 연산으로 발생하는 '고스트 머니'로 정확하게 짚어내고, 중앙 Ledger로 트랜잭션을 집중시키는 해결책(Transaction Injection Pattern)을 제시한 측면에서 기술적 가치가 높습니다. 채권 상환 시 원금/이자 분리를 통한 회계 정확성 향상 분석도 훌륭합니다. 
그러나 채권 메타데이터 파싱 로직 구현 과정에서 발생한 `float()` 캐스팅이 시스템의 핵심 무결성 규칙(Integer Pennies Rule)을 훼손하는 'Float Incursion' 기술 부채를 유발한다는 사실을 인지하지 못한 점이 누락되었습니다. 관련 내용이 매뉴얼에 추가되어야 합니다.

### 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
```markdown
## [Date] Float Incursion during Ledger Metadata Parsing
- **현상 (Problem Recognition)**: `MonetaryLedger`에서 채권 상환(Bond Repayment) 메타데이터 파싱 시 `float()`를 사용하여 금액을 추출함.
- **원인 (Root Cause)**: JSON 또는 Dict 형식의 메타데이터 파싱 시 숫자가 소수점으로 처리될 수 있다는 우려 때문에 무의식적으로 `float` 캐스팅을 사용함.
- **해결 (Solution Method)**: `float()`를 `int()`로 변경하고, 원천적으로 모든 금전 데이터 메타데이터 생성 시 정수 페니(Integer Pennies) 단위임을 명확히 보장하도록 수정함.
- **인사이트/교훈 (Insight/Lesson Learned)**: 메타데이터나 텍스트 딕셔너리에서 화폐 액수를 추출할 때, 코어 시스템 레벨의 'Float Incursion' 방지 규칙을 간과하기 쉽다. 파싱 계층에서도 데이터 타입인 `int()` 캐스팅을 철저히 검증 및 준수하여, 소수점 오차로 인한 화폐 생성/소멸(Zero-Sum 위반) 무결성 붕괴를 원천 차단해야 한다.
```

### 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**
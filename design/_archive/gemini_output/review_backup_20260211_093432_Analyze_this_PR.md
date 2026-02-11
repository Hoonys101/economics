### 📝 Code Review Report

---

### 🔍 Summary
이 PR은 `HREngine`과 `SalesEngine`을 상태 비저장(stateless) 컴포넌트로 리팩토링하는 것을 목표로 합니다. DTO(Data Transfer Objects)를 도입하여 엔진의 입력과 출력을 명확히 정의하고, `Firm` 클래스가 그 결과를 적용하는 오케스트레이터(Orchestrator) 역할을 하도록 변경했습니다. 이 구조는 모듈성, 테스트 용이성, 코드 투명성을 크게 향상시키는 훌륭한 방향입니다.

### 🚨 Critical Issues
- 발견된 사항 없음. 보안 위반이나 치명적인 버그는 식별되지 않았습니다.

### ⚠️ Logic & Spec Gaps
- **상태 비저장 원칙 위반 (Violation of Stateless Principle)**
  - **위치**: `simulation/components/engines/hr_engine.py`, `process_payroll` 메소드 내부
  - **코드**: `context.wallet_balances[DEFAULT_CURRENCY] = current_balance - wage`
  - **문제**: 이 코드는 입력으로 받은 `HRPayrollContextDTO` 객체의 `wallet_balances` 필드를 직접 수정합니다. 엔진은 외부 상태를 변경하지 않는 순수 함수처럼 동작해야 하지만, 이 코드는 입력 객체를 변경하여 부수 효과(side-effect)를 일으킵니다. 이는 "입력 DTO -> 출력 DTO"라는 이번 리팩토링의 핵심 원칙을 위반하며, 예기치 않은 버그를 유발할 수 있습니다. 한 번의 급여 처리 내에서 지불 능력을 시뮬레이션하려는 의도는 이해하지만, 입력 데이터를 직접 수정하는 것은 위험합니다.

### 💡 Suggestions
- **로컬 변수를 사용한 상태 시뮬레이션**
  - `process_payroll` 함수 시작 시점에서 `context.wallet_balances`의 복사본을 만드십시오.
  - 루프 내에서는 원본 `context` 대신 이 복사본을 읽고 수정하여, 함수가 끝날 때 변경 사항이 외부에 영향을 주지 않도록 해야 합니다.

  ```python
  # hr_engine.py -> process_payroll 수정 제안
  
  def process_payroll(...) -> HRPayrollResultDTO:
      """..."""
      # 입력 DTO를 직접 수정하는 대신 로컬 복사본을 사용
      simulated_balances = context.wallet_balances.copy()
      
      transactions: List[Transaction] = []
      employee_updates: List[EmployeeUpdateDTO] = []
      # ...
      for employee in list(hr_state.employees):
          # ...
          current_balance = simulated_balances.get(DEFAULT_CURRENCY, 0.0) # 복사본에서 잔액 조회
          # ...
          if current_balance >= wage:
              # ...
              # 복사본의 잔액을 업데이트하여 루프 내에서만 사용
              simulated_balances[DEFAULT_CURRENCY] = current_balance - wage
          # ...
      return HRPayrollResultDTO(transactions=transactions, employee_updates=employee_updates)
  ```

### 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Insights: Refactor HR & Sales Engines

  ## 1. Technical Debt Discovered
  - **`Firm` God Class**: The `Firm` class (in `simulation/firms.py`) is extremely large and handles too many responsibilities (Production, Finance, HR, Sales orchestration, Decision Making, etc.). While moving logic to engines helps, the `Firm` class itself remains a bottleneck for orchestration.
  - **Inconsistent Mocking**: Tests use a mix of `MagicMock` and real objects, sometimes causing fragility when signatures change. `test_firm_lifecycle.py` was referenced in the spec but not found; tests were scattered across `tests/simulation/test_firm_refactor.py` and `tests/unit/test_firms.py`.
  - **`HREngine` side-effects**: The previous implementation had deep coupling where the engine modified `employee` agents directly. This has been resolved, but other engines (like `FinanceEngine`) should be audited for similar patterns.
  - **Implicit Dependencies**: `Firm` relies on `market_context` having specific keys like `fiscal_policy` which are sometimes dictionaries and sometimes objects/mocks in tests. This inconsistency makes it hard to rely on type hints.

  ## 2. Refactoring Insights
  - **DTO Pattern Effectiveness**: Introducing `HRPayrollResultDTO` and `MarketingAdjustmentResultDTO` successfully decoupled the engines from the agent state. This makes the data flow explicit and easier to test.
  - **Orchestrator Pattern**: The `Firm` now clearly acts as an orchestrator for Payroll and Marketing, applying the results returned by stateless engines. This improves observability of side-effects (they happen in one place).
  - **Testability**: The new engines are purely functional (Input DTO -> Output DTO), making them trivial to unit test without complex mocking of the entire simulation environment.

  ## 3. Future Recommendations
  - **Audit FinanceEngine**: Apply the same pattern to `FinanceEngine`. Currently, it might still have side effects or be too coupled to `FirmState`.
  - **Standardize Context DTOs**: Ensure all context DTOs are strictly typed and used consistently across all engines.
  - **decompose Firm**: Consider breaking `Firm` into smaller orchestrators or using a composite pattern more aggressively to reduce the size of `firms.py`.
  ```
- **Reviewer Evaluation**:
  - `communications/insights/refactor_hr_sales_engine.md` 파일이 정상적으로 포함되었습니다.
  - 내용이 매우 훌륭합니다. `Firm` God Class 문제, 암시적 의존성 등 현재 아키텍처의 핵심적인 기술 부채를 정확히 식별했습니다.
  - DTO와 오케스트레이터 패턴 도입의 장점을 명확하게 설명하고 있으며, `FinanceEngine` 리팩토링과 같은 구체적이고 실용적인 후속 조치를 제안한 점이 인상적입니다. 이 인사이트는 프로젝트의 아키텍처 개선에 크게 기여할 것입니다.

### 📚 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**: `Firm` God Class와 관련된 인사이트를 기술 부채 원장에 추가할 것을 제안합니다.

  ```markdown
  ---
  ## TD-XXX: Firm God Class and Orchestration Bottleneck

  - ** 현상 **: `Firm` 클래스가 생산, 재무, HR, 영업 등 지나치게 많은 책임을 가지는 God Class가 되어 오케스트레이션의 병목 지점이 되고 있음.
  - ** 원인 **: 관련된 로직들이 각자의 엔진으로 분리되지 않고 `Firm` 클래스 내에 직접 구현되었었음.
  - ** 해결/완화 **: HR/Sales 엔진을 상태 비저장으로 분리하고 `Firm`을 오케스트레이터로 만드는 리팩토링을 통해 일부 책임이 분산됨. (PR #XXXXXX)
  - ** 교훈 **: 복잡한 에이전트는 단일 책임 원칙에 따라 여러 개의 작은 오케스트레이터와 상태 비저장 엔진의 조합으로 분해되어야 테스트와 유지보수성이 향상됨. `FinanceEngine` 등 다른 영역에도 동일한 패턴 적용이 필요함.
  ---
  ```

### ✅ Verdict
- **REQUEST CHANGES (Hard-Fail 아님)**
  - 전반적인 리팩토링 방향, 테스트 커버리지, 인사이트 보고서의 품질은 매우 훌륭합니다.
  - 그러나 `HREngine`에서 입력 DTO를 직접 수정하는 것은 리팩토링의 핵심 원칙을 위반하는 논리적 결함이므로 반드시 수정되어야 합니다. 위에 제안된 대로 코드를 수정한 후 다시 리뷰를 요청해주십시오.

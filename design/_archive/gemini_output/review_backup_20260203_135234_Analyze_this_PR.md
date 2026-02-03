# 🔍 Git Diff Review: Atomic Housing Saga (V3)

---

### 1. 🔍 Summary

본 변경 사항은 Saga 패턴을 도입하여 주택 구매 프로세스를 원자적(atomic)으로 처리하도록 리팩토링한 것입니다. Saga 조정 로직을 `SettlementSystem`으로 이전하고, `LoanMarket`에 LTV/DTI 같은 거시건전성 규제를 추가했으며, 이 모든 과정을 검증하는 테스트 코드를 포함했습니다. 아키텍처적으로 중요한 진전이며, 복잡한 트랜잭션의 안정성을 크게 향상시킵니다.

### 2. 🚨 Critical Issues

- **없음**: 분석 결과, API 키, 시스템 경로, 타 프로젝트 저장소 URL 등의 하드코딩이나, 시스템의 자산을 복사/누수시키는 Zero-Sum 위반과 같은 **심각한 보안 및 로직 결함은 발견되지 않았습니다.**

### 3. ⚠️ Logic & Spec Gaps

본 PR은 `REQUEST CHANGES`의 가장 큰 이유인 '인사이트 보고서 누락'은 피했으나, 코드의 유연성과 정확성을 저해하는 몇 가지 하드코딩이 발견되어 수정이 필요합니다.

1.  **Hardcoded Loan Term (`housing_system.py`)**
    -   **현상**: `_submit_saga_to_settlement` 함수 내에서 주택담보대출 신청서(`MortgageApplicationDTO`) 생성 시 `loan_term=360`으로 하드코딩 되어 있습니다.
    -   **문제점**: 시뮬레이션의 핵심 경제 파라미터가 코드 내에 고정되어 있어, `economy_params.yaml`을 통한 동적인 설정 변경이 불가능합니다.
    -   **수정 제안**: `config/economy_params.yaml`의 `housing.mortgage_term_ticks` 값을 읽어와 사용하도록 수정해야 합니다.

2.  **Hardcoded Debt Payment Placeholder (`housing_system.py`)**
    -   **현상**: `MortgageApplicationDTO` 생성 시, 신청인의 기존 부채 상환액이 `applicant_existing_debt_payments=0.0`으로 하드코딩 되어 있습니다.
    -   **문제점**: DTI(총부채원리금상환비율) 계산의 정확성을 심각하게 저해합니다. `LoanMarket`에서 이 값을 다시 조회하는 로직이 있긴 하지만, Saga를 시작하는 `HousingSystem`에서부터 최대한 정확한 데이터를 전달하는 것이 올바른 설계 방향입니다.
    -   **수정 제안**: 가계(Household)의 현재 부채 상태를 조회하여 실제 월 상환액을 계산하고 DTO에 채워 넣는 로직이 추가되어야 합니다.

3.  **Hardcoded Fallback Interest Rate (`loan_market.py`)**
    -   **현상**: `apply_for_mortgage` 함수 내에서 대출 DTO를 재구성하는 로직에 `interest_rate = 0.05` 라는 폴백(fallback) 값이 하드코딩 되어 있습니다.
    -   **문제점**: `stage_mortgage` 함수의 로직을 재구현하는 과정에서 생긴 것으로 보이며, 중앙 은행(`Bank`)의 기준 금리를 따르지 않을 수 있는 잠재적 위험이 있습니다.
    -   **수정 제안**: 아래 `Suggestions`에 제안된 리팩토링을 통해 이 코드 블록을 제거하는 것을 권장합니다.

### 4. 💡 Suggestions

- **DTO 호환성 레이어 리팩토링 (`loan_market.py`)**: `evaluate_mortgage_application` 함수에 `housing_purchase_api`와 `housing_planner_api`의 DTO 필드명을 모두 지원하기 위한 호환성 로직이 복잡하게 구현되어 있습니다. 이는 인사이트 보고서에도 지적되었듯이 기술 부채가 될 수 있습니다. 향후 `MortgageApplicationDTO`를 하나로 통일하여 이 부분을 단순화하는 리팩토링을 고려하십시오.

- **Loan Staging 로직 통합 (`loan_market.py`)**: `apply_for_mortgage` 함수가 `stage_mortgage`를 호출하는 대신, 대출 정보(`LoanDTO`)를 얻기 위해 은행(`Bank`)의 `stage_loan` 호출 로직을 직접 재구현하고 있습니다. `stage_mortgage` 함수가 `LoanDTO` 전체를 반환하도록 수정하고, `apply_for_mortgage`가 이를 직접 사용하도록 단순화하면 코드 중복을 줄이고 일관성을 높일 수 있습니다.

### 5. 🧠 Manual Update Proposal

이번 구현에서 발견된 인사이트는 좋은 기술 부채 사례입니다. 프로젝트의 중앙 지식 베이스에 기록하여 교훈을 전파할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  
  ### ID: TD-HS-V3
  - **현상 (Phenomenon)**:
    - 테스트 코드에서 `MagicMock` 사용 시 `spec`을 지정하지 않으면, `hasattr` 체크에 무조건 `True`를 반환하여 의도치 않은 로직 분기를 타는 문제가 발생 (e.g., `SettlementSystem`이 Mock 객체를 Firm으로 오인).
    - 서로 다른 모듈에서 유사하지만 필드명이 다른 DTO(`MortgageApplicationDTO`)가 파생되어, `LoanMarket`에서 복잡한 호환성 레이어를 구현해야 했음.
  - **원인 (Cause)**:
    - `MagicMock`의 기본 동작 방식에 대한 이해 부족.
    - 기능 개발 시 기존 DTO를 재사용하거나 통합하지 않고 새로운 DTO를 정의한 결과.
  - **해결 (Solution)**:
    - Mock 객체 생성 시 `spec` 인자를 사용하여 객체의 인터페이스를 명확히 제한함.
    - `LoanMarket`에 두 DTO를 모두 처리하는 호환성 코드를 추가하여 임시 해결.
  - **교훈 (Lesson Learned)**:
    - 동적 속성 체크(`hasattr`)를 사용하는 로직의 테스트에는 `spec`을 활용하여 Mock의 행동을 엄격히 제어해야 한다.
    - 새로운 API나 기능을 추가할 때는 기존 데이터 구조(DTO)의 재사용을 우선 고려하여 중복과 파편화를 방지해야 한다.
  ```

### 6. ✅ Verdict

**REQUEST CHANGES (Hard-Fail)**

**사유**: 본 PR은 `인사이트 보고서`를 포함하여 프로젝트의 핵심적인 지식 관리 프로토콜을 준수했습니다. 또한, 치명적인 보안 결함이나 Zero-Sum 위반은 발견되지 않았습니다. 그러나 시뮬레이션의 핵심 경제 파라미터(`loan_term`)와 DTI 계산의 정확성에 영향을 미치는 값(`applicant_existing_debt_payments`)이 하드코딩된 것은 로직의 유연성과 정확성을 해치는 명백한 결함입니다. 따라서 **'Logic & Spec Gaps'** 에 명시된 사항들을 수정한 후 다시 리뷰를 요청해주십시오.

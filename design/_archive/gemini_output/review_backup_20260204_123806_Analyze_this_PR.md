# 🔍 PR Review: TD-206 Financial Precision Alignment

## 🔍 Summary

본 변경은 금융 정합성 향상을 목표로, 가계(Household)와 시장(Market) 도메인 간의 데이터 불일치 문제를 해결합니다. `MortgageApplicationDTO`의 필드명을 명확히 하고(`월 소득` 등), 분산되어 있던 부채 계산 로직을 중앙화하며, 관련 DTO들에 최신 재무 지표를 반영하여 시스템 전반의 데이터 흐름을 일관성 있게 개선했습니다.

## 🚨 Critical Issues

- 해당 없음. 보안 취약점이나 자산 증발/복사(Zero-Sum) 버그는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

-   **Code Duplication**: **가장 중요한 수정 필요 사항입니다.** 월 소득과 기존 월 부채 상환액을 계산하는 로직이 두 파일에 중복으로 구현되어 있습니다.
    -   **Location 1**: `modules/finance/saga_handler.py` (L:120-155)
    -   **Location 2**: `modules/household/mixins/_state_access.py` (L:45-77)
    -   이는 향후 로직 변경 시 두 곳을 모두 수정해야 하는 잠재적 버그의 원인이 됩니다. `HouseholdStateAccessMixin`에 구현된 `_calculate_monthly_debt_payments` 헬퍼 함수와 소득 계산 로직을 금융 관련 유틸리티나 서비스로 이전하여, Saga 핸들러가 이를 직접 호출하도록 리팩토링해야 합니다.

-   **Broad Exception Handling**: `saga_handler.py`와 `_state_access.py`의 부채 계산 로직에서 `except Exception as e:`를 사용하고 있습니다. 이는 너무 광범위하여 `BankService`에서 발생하는 특정 오류(예: `LoanNotFound`, `InvalidData`)를 구분할 수 없게 만듭니다. 보다 명확한 예외 타입을 지정하여 오류 처리의 정밀도를 높여야 합니다.

## 💡 Suggestions

-   **Configuration Value Centralization**: `ticks_per_year` 값을 가져오기 위해 `getattr(..., 'TICKS_PER_YEAR', 360)` 코드가 여러 곳에서 반복됩니다. 이 설정값은 시뮬레이션의 핵심 상수이므로, 초기화 시점에 한 번만 로드하여 공유 컨텍스트나 의존성 주입을 통해 접근하는 것이 더 효율적이고 안정적입니다.

## 🧠 Manual Update Proposal

-   **Target File**: `communications/insights/TD-206_Precision_Update.md`
-   **Analysis**: 이번 커밋에는 **새로운 인사이트 보고서가 정상적으로 포함되었습니다.** 이는 프로젝트의 지식 축적 프로토콜을 매우 잘 준수한 훌륭한 사례입니다. 보고서의 내용은 명확하며 `현상/원인/해결/교훈`의 핵심 요소를 모두 포함하고 있습니다. 별도의 매뉴얼 업데이트는 필요하지 않습니다.

## ✅ Verdict

**REQUEST CHANGES (Hard-Fail)**

**사유**: 코드의 핵심적인 부분인 **재무 계산 로직이 두 곳 이상에 중복**되어 있습니다. 이는 심각한 유지보수성 저하 및 잠재적 버그를 유발하는 아키텍처 문제입니다. 기능적으로는 현재 동작할 수 있으나, 프로젝트의 장기적인 안정성을 위해 반드시 수정되어야 합니다. 위에 제안된 대로 중복 로직을 단일 책임의 원칙(SRP)에 따라 중앙화된 서비스나 유틸리티 함수로 리팩토링한 후 다시 리뷰를 요청해주십시오.

인사이트 보고서를 작성한 점은 매우 훌륭하지만, 코드 품질 또한 머지의 중요한 기준입니다.

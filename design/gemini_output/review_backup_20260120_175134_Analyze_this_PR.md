# 🔍 Git Diff Review: `infra-cleanup-td-063-050-051`

## 🔍 Summary

이 PR은 두 가지의 완전히 상반된 작업을 포함하고 있습니다. 첫째는 명시된 목표대로 `pathlib`을 사용한 스크립트 안정화(TD-063) 및 문서 정리(TD-050, TD-051)로, 이 부분은 훌륭하게 수행되었습니다. 하지만 둘째로, 프로젝트의 핵심 아키텍처인 **관심사 분리(SoC)** 원칙을 심각하게 위반하고 이전에 완료된 리팩토링(TD-067 Phase A)을 되돌리는 **치명적인 아키텍처 회귀(Regression)**를 유발하는 변경 사항이 함께 포함되었습니다.

## 🚨 Critical Issues

1.  **[CRITICAL] 대규모 아키텍처 회귀 및 SoC 원칙 위반**
    - **위치**: `simulation/firms.py`, `simulation/decisions/corporate_manager.py` 외 다수
    - **문제**: `Firm` 클래스에 수많은 `@property` 래퍼(Wrapper)를 다시 추가하고, `FinanceDepartment`, `ProductionDepartment` 등 하위 컴포넌트의 핵심 API 메서드(예: `invest_in_automation`, `pay_severance`, `add_capital`)를 삭제했습니다.
    - **영향**: 이 변경으로 `Firm` 클래스가 다시 모든 책임을 가진 거대한 **God Class**로 회귀했으며, 이는 TD-067 등의 리팩토링 목표와 정면으로 배치됩니다. `corporate_manager`와 다른 시스템들이 컴포넌트 API 대신 `firm.assets -= ...` 와 같이 `Firm`의 내부 상태를 직접 조작하게 만들어 캡슐화를 파괴합니다.

2.  **[CRITICAL] 제로섬(Zero-Sum) 위반 및 회계 로직 누락**
    - **위치**: `simulation/decisions/corporate_manager.py` (`_manage_hiring` 메서드 내 해고 로직)
    - **문제**: 퇴직금 지급 로직이 `firm.finance.pay_severance(...)` API 호출에서 `firm.assets -= severance_pay; emp.assets += severance_pay`로 변경되었습니다.
    - **영향**: 기존 API는 자산 이전과 함께 `record_expense`를 호출하여 비용을 기록했지만, 변경된 코드는 비용 기록을 누락합니다. 이로 인해 회사의 손익계산서가 깨지고, 시스템 전체의 자산 총합이 맞지 않게 됩니다(돈이 회계상 증발).

3.  **[CRITICAL] 핵심 컴포넌트 API 삭제**
    - **위치**: `simulation/components/finance_department.py`, `simulation/components/production_department.py` 등
    - **문제**: 외부 모듈과의 계약(Contract) 역할을 하던 중요한 public 메서드들이 대거 삭제되었습니다. 예를 들어, `FinanceDepartment`의 `invest_in_rd`, `set_dividend_rate` 등이 삭제되어 외부 모듈이 재무 상태를 안전하게 변경할 수 있는 방법이 사라졌습니다.

## ⚠️ Logic & Spec Gaps

1.  **작업 범위의 부적절한 혼합 (Improper Mixing of Scopes)**
    - 이 PR의 명시된 목표는 인프라 및 문서 정리입니다. 하지만 시뮬레이션 코어 로직에 대한 대규모의 파괴적인 리팩토링이 아무런 설명 없이 포함되었습니다. 이는 코드 리뷰를 어렵게 하고 의도를 불분명하게 만듭니다.

2.  **기술 부채 해결의 역행 (Reversal of Tech Debt Resolution)**
    - 이 PR의 변경 사항은 `TECH_DEBT_LEDGER.md`에 기록된 `TD-058` (느슨한 결합)이나 `TD-067` (SoC)과 같은 기술 부채를 해결하는 것이 아니라, 오히려 해결된 상태를 이전의 문제 상태로 되돌리고 있습니다.

## 💡 Suggestions

1.  **PR 분리 및 회귀 코드 전면 폐기**
    - **즉시 `simulation/` 및 `tests/` 디렉토리와 관련된 모든 변경 사항을 이 PR에서 되돌리십시오(revert).**
    - 인프라 정리(TD-050, 051, 063)에 해당하는 `scripts/`, `design/`, `reports/`, `*.md` 파일 변경 사항만 남겨두고 PR을 다시 제출하십시오. 이 부분은 병합할 가치가 있습니다.

2.  **아키텍처 설계 재검토**
    - `Firm` 리팩토링과 관련된 작업은 별도의 PR에서 진행되어야 합니다. 현재 변경 내용은 프로젝트 아키텍처에 대한 근본적인 오해에서 비롯된 것으로 보입니다. `TD-067`의 명세와 `platform_architecture.md`를 다시 검토하고, 컴포넌트 기반 아키텍처의 목적을 이해한 후 접근해야 합니다.

## ✅ Verdict

**REJECT**

이 PR은 프로젝트의 안정성과 아키텍처 무결성을 심각하게 훼손하는 변경을 포함하고 있으므로 현재 상태로는 절대 병합할 수 없습니다. 제안에 따라 인프라 정리 부분만 분리하여 다시 제출해 주십시오.

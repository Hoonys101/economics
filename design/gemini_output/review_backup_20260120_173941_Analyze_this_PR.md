# 🔍 Git Diff 리뷰 보고서

---

## 🔍 Summary

이 커밋은 금융 관련 파라미터들을 `config.py`에서 `economy_params.yaml`로 이전하는 긍정적인 변경과 함께, `Firm`의 구조를 리팩토링하는 작업을 포함합니다. 하지만 리팩토링 과정에서 `CorporateManager`가 `Firm`의 내부 상태(`assets`, `capital_stock` 등)를 직접 조작하도록 변경되어 **관심사 분리(SoC) 원칙을 심각하게 위반**하고, **비용 처리를 누락하는 치명적인 버그**를 도입했습니다.

## 🚨 Critical Issues

1.  **[CRITICAL] 비용 누락으로 인한 이익 과대계상 버그**
    *   **파일**: `simulation/decisions/corporate_manager.py`
    *   **문제**: R&D 투자 및 세금 납부 로직이 `FinanceDepartment`에서 `CorporateManager`로 옮겨지면서, 비용을 기록하는 `record_expense()` 호출이 누락되었습니다.
    *   **영향**: 기업이 R&D에 투자하거나 세금을 납부할 때 자산(`assets`)은 감소하지만, 비용으로 처리되지 않아 회계상 이익이 비정상적으로 부풀려집니다. 이는 시뮬레이션 경제 전체를 왜곡하는 심각한 돈 복사 버그입니다.
    *   **코드 (R&D)**: `corporate_manager.py`의 `_manage_rd` 함수에서 `firm.assets -= budget`만 실행되고, 기존의 `firm.finance.record_expense(amount)`가 사라졌습니다.
    *   **코드 (세금)**: `corporate_manager.py`의 `_manage_automation` 함수에서 자동화세를 납부할 때 `firm.assets -= tax_amount`만 실행되고, 기존의 `record_expense` 로직이 사라졌습니다.

2.  **[CRITICAL] 아키텍처 원칙 위반: 관심사 분리(SoC) 붕괴**
    *   **파일**: `simulation/decisions/corporate_manager.py`
    *   **문제**: `CorporateManager`는 의사결정 '오케스트레이터'가 되어야 하지만, 이 변경으로 인해 직접 `Firm`의 자산을 빼거나(`firm.assets -= ...`), 자본을 더하는(`firm.capital_stock += ...`) 등 회계 및 생산의 핵심 로직을 직접 수행하게 되었습니다. 이는 `FinanceDepartment`와 `ProductionDepartment`의 책임을 침해하고 두 모듈을 무력화시킵니다.
    *   **영향**: 코드가 극도로 결합되어 유지보수가 어려워지고, 향후 유사한 버그가 발생할 가능성이 매우 높아집니다. 예를 들어, `firm.assets`의 변경을 추적하려면 이제 `CorporateManager`의 모든 로직을 일일이 확인해야 합니다.

## ⚠️ Logic & Spec Gaps

1.  **리팩토링 방향성의 모순**
    *   `simulation/firms.py`에 `FinanceDepartment`의 속성을 외부로 노출하는 다수의 `@property` (Facade 패턴)가 추가된 것은 바람직한 방향입니다.
    *   하지만 `CorporateManager`의 변경 내용은 이 Facade를 사용하는 대신, `Firm`의 내부 상태를 직접 수정하여 Facade 패턴의 이점을 완전히 무시하고 아키텍처를 후퇴시켰습니다. 이는 전체 리팩토링의 목표와 정면으로 배치됩니다.

## 💡 Suggestions

1.  **비용 처리 로직 복원**: `CorporateManager`에서 `firm.assets`를 직접 차감하는 대신, `FinanceDepartment`에 `invest_in_rd`, `pay_tax` 등의 책임을 수행하는 메서드를 두고, 해당 메서드 내부에서 자산 차감과 비용 기록(`record_expense`)이 트랜잭션으로 함께 처리되도록 로직을 되돌려야 합니다.
2.  **SoC 원칙 재적용**: `CorporateManager`는 `firm.invest_in_rd(budget)` 와 같이 `Firm` 또는 그 하위 컴포넌트의 고수준 API를 호출하는 역할에만 집중해야 합니다. 자산, 부채, 자본과 같은 `Firm`의 구체적인 내부 상태를 직접 수정해서는 안 됩니다.
3.  **점진적 리팩토링**: 파라미터 이전과 아키텍처 리팩토링은 별개의 커밋으로 분리하는 것이 좋습니다. 두 가지 큰 변경 사항이 섞여 있어 리뷰가 복잡하고 잠재적인 문제를 식별하기 어렵습니다.

## ✅ Verdict

**REJECT**

회계 장부를 파괴하는 치명적인 비용 누락 버그와 심각한 아키텍처 원칙 위반으로 인해 이 변경 사항을 병합할 수 없습니다. 제안된 수정 사항을 반영하여 코드를 재설계하십시오. 파라미터 이전 작업은 긍정적이므로 해당 부분만 별도의 PR로 분리하는 것을 권장합니다.

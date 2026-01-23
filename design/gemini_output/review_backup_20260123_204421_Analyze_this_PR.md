# 🔍 Git Diff Review: WO-116 Phase B Tick Normalization

## 🔍 Summary
이 PR은 시뮬레이션의 핵심 로직을 직접적인 상태 변경에서 **트랜잭션 생성 기반**으로 리팩토링하는 중요한 아키텍처 변경을 포함합니다. 각 모듈(Bank, Firm, Government 등)이 직접 자산을 변경하는 대신 `Transaction` 객체 리스트를 생성하고, `TickScheduler`가 이를 수집하여 중앙에서 처리하도록 변경되었습니다. 이는 SoC(관심사 분리)와 데이터 무결성을 크게 향상시키는 훌륭한 방향입니다.

## 🚨 Critical Issues
- **[CRITICAL] `finance_department.py`의 배당금 지급 로직 오류**:
  - `process_profit_distribution` 함수에서 배당금 지급을 위한 `Transaction` 생성 시, 지불 주체와 수령 주체가 뒤바뀌었습니다.
    ```python
    # L.223, simulation/components/finance_department.py
    Transaction(
        buyer_id=self.firm.id, # Firm pays Household
        seller_id=household.id,
        ...
        transaction_type="dividend",
    )
    ```
  - 기존 주석(`seller.assets -= trade_value`)에 따르면 `seller`가 지불자여야 합니다. 현재 코드는 **가계(household)의 자산을 차감하여** 회사에 배당금을 지급하려는 시도를 하게 되므로, 즉시 수정해야 합니다. `seller_id`는 `self.firm.id`가 되어야 합니다.

- **[CRITICAL] `government.py`의 직접적인 자산 변경 잔존**:
  - `invest_infrastructure` 함수 내에서 트랜잭션 생성과 별개로 **직접 `self.withdraw(effective_cost)`를 호출**하고 있습니다 (L.478).
  - 이는 이번 리팩토링의 핵심 원칙(트랜잭션 기반 처리)을 위반하며, 자금의 이중 차감(double-spending) 또는 데이터 부정합을 유발할 수 있는 심각한 결함입니다. 주석에 "acknowledged technical debt"라고 명시되어 있지만, 아키텍처의 일관성을 위해 반드시 제거되어야 합니다.

## ⚠️ Logic & Spec Gaps
- **"낙관적 상태 업데이트 (Optimistic State Update)" 패턴**:
  - `finance/system.py`의 `issue_treasury_bonds`나 `grant_bailout_loan` 등 여러 곳에서, 트랜잭션을 생성한 직후 아직 처리되기 전에 관련 상태(e.g., `self.outstanding_bonds.append(new_bond)`)를 먼저 업데이트하는 패턴이 관찰됩니다.
  - 이는 트랜잭션 프로세서가 항상 성공할 것이라고 가정하는 설계입니다. 현재 시스템에서는 문제가 되지 않을 수 있으나, 향후 트랜잭션 실패 시 롤백 메커니즘이 없다면 상태 불일치를 유발할 수 있는 잠재적 위험 요소입니다. 이는 버그는 아니지만, 설계상 중요한 트레이드오프이므로 팀 전체가 인지하고 있어야 합니다.

## 💡 Suggestions
- **트랜잭션 처리 규칙 중앙 문서화**:
  - `finance_department.py`의 주석에서 발견된 `seller.assets -= trade_value`와 같은 트랜잭션 처리 규칙은 매우 중요하지만 직관적이지 않습니다.
  - 이러한 핵심 규칙은 `Transaction` 모델의 Docstring이나 관련 설계 문서에 명확하게 기술하여, 향후 다른 개발자가 동일한 실수를 반복하지 않도록 방지해야 합니다.

- **레거시 메서드 처리**:
  - `finance_system.py`의 `collect_corporate_tax`처럼 사용 중단을 경고하는 방식으로 레거시 메서드를 처리한 것은 좋은 접근입니다. 이 패턴을 다른 모듈의 폐기 예정 함수들에도 일관되게 적용하는 것을 권장합니다.

## ✅ Verdict
**REQUEST CHANGES**

이번 리팩토링은 프로젝트의 아키텍처를 크게 개선하는 올바른 방향입니다. 그러나 발견된 **배당금 지급 오류**는 시스템의 자금 흐름에 치명적인 버그이며, `government.py`의 **직접적인 자산 차감**은 리팩토링의 목적을 훼손하는 심각한 아키텍처 위반입니다. 이 두 가지 Critical Issue를 수정한 후 다시 리뷰를 요청해주십시오.

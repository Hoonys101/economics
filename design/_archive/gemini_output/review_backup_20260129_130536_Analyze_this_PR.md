# Git Review: WO-147 Soft Landing Suite

## 🔍 요약 (Summary)

경제 안정화 정책(통화/재정 안정화 장치)의 효과를 검증하기 위한 시뮬레이션 스크립트(`verify_soft_landing.py`)와 관련 기능 플래그가 추가되었습니다. 또한, 일부 코드에서 발생할 수 있는 `AttributeError`를 방지하기 위한 방어적 코드가 추가되었고, 의사결정 컨텍스트 전달 방식이 개선되었습니다.

## 🚨 Critical Issues

- 해당 사항 없음.

## ⚠️ 로직 및 Spec Gaps

- **[Potentially Risky] `scripts/verify_soft_landing.py` (Line 15):** 스크립트 실행 시 `matplotlib` 라이브러리가 없으면 `pip install`을 통해 자동으로 설치를 시도합니다. 이는 사용자 환경을 예고 없이 변경할 수 있어 위험합니다. 모든 의존성은 `requirements.txt`에 명시하고, 개발자가 수동으로 설치하도록 안내하는 것이 표준적인 방식입니다.
- **[Minor] `modules/household/econ_component.py` (Line 384, 388), `simulation/orchestration/phases.py` (Line 463, 478):** `AttributeError`를 막기 위해 `hasattr` 체크가 여러 곳에 추가되었습니다. 이는 임시적인 방어막은 될 수 있으나, 근본적으로 `Order` 객체의 구조가 생성 위치나 타입에 따라 일관되지 않다는 아키텍처 문제를 암시합니다. (자세한 내용은 아래 `Manual Update Proposal` 참조)

## 💡 제안 (Suggestions)

- **`scripts/verify_soft_landing.py`**: 자동 설치 로직을 제거하고, `matplotlib`을 `requirements.txt`에 추가하는 것을 권장합니다.
- **`hasattr` 사용**: `hasattr(obj, 'attr')` 후 `obj.attr`로 접근하는 패턴은 `getattr(obj, 'attr', default_value)`를 사용하는 것으로 더 간결하고 안전하게 개선할 수 있습니다. 예를 들어 `modules/household/econ_component.py`의 Line 388은 아래와 같이 변경할 수 있습니다.
  ```python
  # Before
  if order.order_type == "SELL" and (getattr(order, "item_id", "") == "labor" or order.market_id == "labor"):
  
  # Suggestion (already applied here, but as a general rule)
  # This is already good, but could be noted for other places where a simple hasattr check is used.
  ```
  이 PR에서는 `getattr`이 이미 잘 적용되었으나, 향후 유사한 패턴 발견 시 참고하면 좋습니다.

- **`config.py` (Line 385):** `DEFAULT_LOAN_SPREAD`의 추가 코멘트에 "WO-146"이 언급되어 있습니다. 현재 PR의 Mission Key가 "WO-147"이므로, 관련성이 없다면 혼동을 줄이기 위해 코멘트를 수정하거나 제거하는 것이 좋습니다.

## 🧠 Manual Update Proposal

이번 코드 변경에서 `Order` 객체의 비일관성 문제가 여러 곳에서 발견되었습니다. 이는 기술 부채로 기록하여 추후 아키텍처 개선의 근거로 삼아야 합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:

  ```markdown
  ---
  - **ID**: TDL-028
    **Date**: 2026-01-29
    **Status**: Identified
    **Severity**: Medium
    **Owner**: @Jules
  ---
  - **현상 (Symptom)**:
    - `simulation/orchestration/phases.py`, `modules/household/econ_component.py` 등 여러 모듈에서 `Order` 객체의 `item_id` 속성 존재 여부를 확인하는 `hasattr()` 또는 `getattr()` 방어 코드가 반복적으로 추가됨 (WO-147).
    - 이는 특정 유형의 `Order` 객체(예: 내부 처리용, 금융 관련)에 `item_id`가 없어 `AttributeError`가 발생할 수 있음을 시사함.
  - **기술 부채 (Technical Debt)**:
    - `Order` DTO(Data Transfer Object)의 인터페이스가 단일화되어 있지 않고, 생성 위치나 목적에 따라 속성 구성이 달라지는 비일관성이 존재함.
    - 이로 인해 `Order`를 처리하는 모든 로직에서 잠재적 `AttributeError`를 막기 위한 방어 코드가 필수적이 되어 코드 복잡도를 높이고 유지보수를 어렵게 함.
  - **상환 계획 (Repayment Plan)**:
    - **단기**: `Order` 객체를 생성하는 모든 팩토리/메서드를 전수 조사하여 필수 속성(e.g., `market_id`, `item_id` 등)이 누락되지 않도록 수정. `item_id`가 필요 없는 경우 명시적으로 `None`이나 빈 문자열을 할당.
    - **장기**: `Order`를 추상 기본 클래스(ABC)로 전환하고, `MarketOrder`, `InternalOrder`, `FinancialOrder` 등 목적에 맞는 구체적인 자식 클래스를 정의하여 인터페이스를 명확히 분리하는 리팩토링을 고려.
  - **교훈 (Lesson Learned)**:
    - 여러 모듈에서 공유되는 핵심 데이터 구조(DTO)는 엄격하고 일관된 인터페이스를 가져야 시스템의 예측 가능성이 높아지고, 불필요한 방어 코드 작성을 줄일 수 있다.
  ```

## ✅ 평결 (Verdict)

**REQUEST CHANGES**

안정성 검증 스위트 추가와 구조 개선은 긍정적입니다. 다만, `verify_soft_landing.py`의 자동 의존성 설치 로직은 반드시 수정이 필요하며, `hasattr` 패턴의 근본 원인에 대한 기술 부채 기록을 제안합니다. 위 사항들을 반영 후 다시 리뷰 요청 바랍니다.

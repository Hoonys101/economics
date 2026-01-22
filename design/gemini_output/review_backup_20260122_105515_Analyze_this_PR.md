# 🔍 Git Diff Review: `fix-integrity-wo106-108`

## 🔍 Summary

이 변경 사항은 기업의 생산 목표를 재고 수준에 따라 동적으로 조정하는 로직을 복원합니다. 동시에, 기업 의사결정 엔진(`AIDrivenFirmDecisionEngine`)의 테스트 코드를 대대적으로 리팩토링하며, 내부 의존성을 `rule_based_engine`에서 `corporate_manager`로 교체하고 테스트 방식을 변경합니다.

## 🚨 Critical Issues

- 발견된 사항 없음.

## ⚠️ Logic & Spec Gaps

- **[MAJOR] 대규모 테스트 케이스 삭제**: `tests/test_firm_decision_engine_new.py` 파일에서 약 300줄 이상의 테스트 코드가 삭제되었습니다.
    - **영향**: 삭제된 테스트들은 **고용(hiring), 해고(firing), 그리고 다양한 AI 기반 가격/임금 조정 전술**과 관련된 핵심 로직을 검증하고 있었습니다.
    - **문제**: 이 기능들이 새로운 `CorporateManager` 구조 하에서 어떻게 동작하는지에 대한 테스트가 이제 존재하지 않아, 심각한 기능 회귀(regression)가 발생할 위험이 매우 높습니다. 커밋의 의도("무결성 수정")가 테스트 커버리지를 대폭 감소시키는 것을 정당화하지 않습니다.
    - **위치**: `tests/test_firm_decision_engine_new.py` (e.g., `test_make_decisions_hires_to_meet_min_employees`, `test_make_decisions_ai_price_increase_small` 등 다수)

- **아키텍처 변경으로 인한 암시적 동작**:
    - **문제**: 판매 주문(Sell Order) 생성 방식이 명시적인 `Order` 객체 반환에서 `firm.sales.post_ask()` 메소드를 호출하는 부수 효과(side-effect) 방식으로 변경되었습니다. 이는 시스템의 데이터 흐름을 추적하기 어렵게 만들 수 있습니다.
    - **위치**: `tests/test_firm_decision_engine_new.py`의 `test_make_decisions_sell_order_details` 테스트에서 변경점 확인 가능.

## 💡 Suggestions

- **테스트 복원 또는 재작성**: 삭제된 테스트 케이스들이 검증하던 고용 및 가격 책정 로직에 대한 테스트를 **반드시** 새로운 아키텍처에 맞게 재작성하거나 복원해야 합니다. 테스트 커버리지 감소는 수용할 수 없습니다.
- **커밋 분리**: 하나의 커밋에 로직 복원(기능)과 대규모 테스트 리팩토링(구조 변경)이 혼재되어 있습니다. 이는 리뷰를 어렵게 하고 롤백을 복잡하게 만듭니다. 향후에는 기능 변경과 리팩토링 커밋을 분리하는 것을 권장합니다.
- **아키텍처 결정 기록(ADR)**: 판매 주문 생성을 반환 값(return value)에서 부수 효과(side-effect)로 변경한 것은 중요한 아키텍처 변경입니다. 왜 이런 결정이 내려졌는지에 대한 이유를 설계 문서(ADR)에 기록하여 추후 다른 개발자들이 혼란을 겪지 않도록 해야 합니다.

## ✅ Verdict

**REQUEST CHANGES**

- **사유**: 핵심 비즈니스 로직(고용, 가격 책정)에 대한 테스트 커버리지가 심각하게 감소하여 안정성을 보장할 수 없습니다. 삭제된 기능들에 대한 테스트를 다시 추가하기 전까지는 머지할 수 없습니다.

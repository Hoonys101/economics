# 🔍 PR Review: WO-116 Asset Cleanup & Settlement System Integration

### 1. 🔍 Summary
이 변경 사항은 시스템 전반에 걸쳐 자산 이동의 정합성을 보장하기 위해 `SettlementSystem`을 도입하는 대규모 리팩토링입니다. 기존의 `_add_assets` 및 `_sub_assets`를 사용한 수동적인 자산 증감 로직을 원자적(atomic)인 `settlement.transfer`로 대체하여, 돈 복사 및 자산 누수 버그의 근본적인 원인을 제거하는 것을 목표로 합니다. 이는 시스템의 재무 건전성을 크게 향상시키는 중요한 아키텍처 개선입니다.

### 2. 🚨 Critical Issues
- **(POTENTIAL) Logic Flaw**: `simulation/systems/housing_system.py`의 `process_sale` 함수에서 정부(seller)에게 주택 판매 대금을 지급하는 로직이 매우 복잡하고 위험해 보입니다.
    - 개발자가 남긴 주석(`# DOUBLE CHARGE!`)에서 정확히 지적했듯이, `settlement.transfer(buyer, seller, ...)`를 호출하여 이미 대금을 정부에 이전한 후, `seller.collect_tax(...)`를 다시 호출하고 있습니다.
    - 만약 `collect_tax` 내부에서도 자산 이전 로직이 실행된다면, 구매자에게 **대금이 이중으로 청구될 수 있는 심각한 버그**가 발생할 수 있습니다.
    - 현재는 이중 청구를 피하기 위해 수동으로 정부의 통계(`revenue_this_tick`, `total_collected`)만 업데이트하고 있지만, 이는 `collect_tax` API의 책임이 모호하다는 증거이며 임시방편에 가깝습니다.

### 3. ⚠️ Logic & Spec Gaps
- **API Contract Ambiguity**: `government.collect_tax` 메소드의 역할이 불분명해졌습니다. 과거에는 세금 징수와 자산 증가를 모두 처리했을 수 있으나, 이제 `SettlementSystem`이 자산 이전을 전담합니다. `collect_tax`가 통계 기록용인지, 실제 자산 이전용인지 명확히 구분되지 않아 `housing_system.py`와 같은 혼란과 잠재적 버그를 유발하고 있습니다.
- **Inconsistent Fallback Logic**: `inheritance_manager.py`와 `transaction_processor.py`에서는 `SettlementSystem`이 없을 경우 `logger.critical`을 호출하며 시스템을 사실상 중단시키는 'Strict Mode'를 채택했습니다. 이는 매우 좋은 결정입니다.
    - 하지만 `government.py`, `finance_department.py` 등 다른 여러 파일에서는 `SettlementSystem`이 없으면 기존의 수동 `_sub/_add` 방식을 사용하는 폴백(fallback) 로직이 여전히 남아있습니다.
    - 이러한 불일치는 시스템의 특정 부분에서는 자산 정합성을 강제하지만, 다른 부분에서는 여전히 잠재적인 오류에 노출되게 만듭니다.

### 4. 💡 Suggestions
- **Refactor `government.collect_tax`**: `collect_tax` 메소드의 책임을 명확히 분리해야 합니다.
    1.  `government.record_revenue(amount, category, ...)`: 순수하게 통계만 기록하는 메소드.
    2.  `finance_system.execute_tax_payment(payer, amount, ...)`: 실제 세금 이전만 담당하는 메소드.
    - 이렇게 분리하면 `housing_system.py`의 복잡한 문제를 깨끗하게 해결할 수 있습니다. (`settlement.transfer` 호출 후 `government.record_revenue`를 호출)
- **Deprecate Fallbacks**: 'Strict Mode'를 프로젝트 전반으로 확장할 계획을 세워야 합니다. 전환 기간 동안 레거시 폴백 로직이 필요할 수는 있으나, 빠른 시일 내에 모든 자산 이전이 `SettlementSystem`을 통하도록 강제하고, 폴백 로직을 제거하여 코드베이스의 일관성과 안정성을 높이는 것이 바람직합니다.
- **Minor Style (`tests/test_finance_bailout.py`)**: 테스트 코드에서 `mock_government.assets` 대신 `mock_government._assets`와 같이 내부 속성에 직접 접근하고 있습니다. 이는 테스트의 불안정성을 높일 수 있으므로, 가능하다면 public 인터페이스를 통해 값을 확인하도록 수정하는 것을 권장합니다.

### 5. ✅ Verdict
**REQUEST CHANGES**

이번 PR은 프로젝트의 재무 안정성을 위한 매우 긍정적이고 필수적인 단계입니다. 개발자는 `SettlementSystem`이라는 올바른 해결책을 도입했으며, 복잡한 로직의 잠재적 위험을 스스로 발견하는 등 훌륭한 작업을 수행했습니다.

다만, `government.collect_tax` API의 모호성으로 인해 발생한 잠재적 이중 청구 버그는 반드시 수정되어야 합니다. 제안된 리팩토링을 통해 API의 책임을 명확히 하고 코드의 안정성을 확보한 후 `APPROVE`하는 것이 좋겠습니다.

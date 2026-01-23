# 🔍 Git Diff Review: WO-116 Asset & Decision Logic Refactor

---

### 🔍 Summary

이 PR은 시스템 전반에 걸쳐 자산(asset) 이동의 원자성을 보장하기 위해 `SettlementSystem`을 도입하고, 레거시 수동 자산 수정을 제거하는 대규모 리팩토링을 수행합니다. 동시에, 의사결정 엔진(Decision Engines)의 아키텍처를 DTO(Data Transfer Object) 기반의 순수 함수 구조에서 에이전트 객체를 직접 참조하고 상태를 수정하는 방식으로 변경하는 근본적인 재설계를 포함하고 있습니다.

### 🚨 Critical Issues

1.  **아키텍처 회귀 (Architectural Regression): "Purity Gate" 원칙 파괴**
    - **위치**: `simulation/decisions/corporate_manager.py`, `simulation/decisions/rule_based_firm_engine.py` 등 다수 의사결정 엔진 파일.
    - **문제**: 이 PR은 `simulation/decisions/README.md` 문서를 삭제하고, "Purity Gate" 및 "Internal Order" 패턴을 폐기했습니다. 기존에는 의사결정 로직이 테스트 용이성과 예측 가능성을 위해 상태 DTO만 사용하는 순수 함수였으나, 이제는 `firm`과 `household` 같은 전체 에이전트 객체를 직접 받아 `firm.production_target = ...` 와 같이 상태를 즉시 수정합니다.
    - **영향**: 이 변경은 의사결정 로직에 부작용(side effect)을 도입하여, 로직의 테스트와 디버깅을 훨씬 더 어렵게 만듭니다. 또한, 의사결정 단계와 상태 변경 단계의 명확한 구분을 없애 시스템의 복잡도를 높이는 심각한 아키텍처적 회귀입니다.

2.  **불안정한 API 계약 및 임시방편 (Unstable API & Workarounds)**
    - **위치**: `simulation/systems/housing_system.py`, `simulation/agents/government.py`
    - **문제**: 주택 판매 시 정부가 판매자인 경우, 자금 이체(`settlement.transfer`)와 세금 징수(`collect_tax`)가 겹쳐 **대금이 이중으로 청구될 수 있는 심각한 버그**가 발생할 수 있었습니다.
    - **개선 및 잔여 문제**: 이 문제는 `government.py`에 `record_revenue`라는 통계 기록 전용 메소드를 추가하고 `housing_system.py`가 이를 사용하도록 수정하여 해결되었습니다. 이는 좋은 개선이지만, 이 문제는 근본적으로 `collect_tax`와 같은 핵심 API의 책임이 명확하지 않았기 때문에 발생했습니다. 이와 유사한 API 계약 모호성이 다른 곳에도 존재할 수 있습니다.

### ⚠️ Logic & Spec Gaps

1.  **폴백 로직의 불일치 (Inconsistent Fallback Logic)**
    - **문제**: 자산 이전의 정합성을 위해 `SettlementSystem`이 없는 경우, `inheritance_manager.py`와 `transaction_processor.py` 등에서는 `logger.critical`을 호출하는 'Strict Mode'를 채택했습니다. 이는 매우 바람직한 방향입니다.
    - **불일치**: 그러나 `government.py`나 `finance_department.py`의 일부 로직에서는 여전히 `settlement_system`이 없을 경우 기존의 수동 자산 수정 방식을 사용하는 레거시 폴백(fallback) 로직이 남아있습니다. 이러한 불일치는 시스템의 안정성을 저해하며, 특정 조건에서 여전히 자산 누수 버그를 유발할 수 있습니다.

2.  **모호한 컨텍스트 객체 필드 (Ambiguous Context Fields)**
    - **위치**: `simulation/dtos/api.py`
    - **문제**: `DecisionContext`에 `household`와 `firm` 객체 필드를 추가하면서 `DEPRECATED FIELDS`라는 주석을 달았습니다. 하지만 의사결정 엔진들은 이 "폐기 예정" 필드들을 적극적으로 사용하도록 리팩토링되었습니다. 이는 매우 혼란스러운 설계이며, 향후 다른 개발자가 이 필드들을 제거하려 할 때 시스템 전체를 망가뜨릴 수 있습니다.

### 💡 Suggestions

1.  **의사결정 아키텍처 재검토**: 'Purity Gate'를 폐기한 결정을 재검토할 것을 강력히 권고합니다. 의사결정 엔진은 순수 함수로 유지하고, 상태 변경 의도는 'Internal Order' 패턴을 통해 반환하는 것이 장기적인 코드 품질, 테스트 용이성, 유지보수성 측면에서 월등히 우수합니다. 이 두 가지 큰 변경(자산 정리, 아키텍처 변경)은 별도의 PR로 분리해야 합니다.
2.  **'Strict Mode' 전면 적용**: `SettlementSystem` 사용을 강제하는 'Strict Mode'를 프로젝트 전반에 걸쳐 일관되게 적용해야 합니다. 모든 레거시 폴백 로직을 제거하여 자산 이전 경로를 단일화하고 시스템의 재무적 무결성을 보장해야 합니다.
3.  **API 책임 명확화**: `government.collect_tax`와 `record_revenue`를 분리한 것처럼, 시스템 내 다른 핵심 API들의 책임(상태 변경 vs. 통계 기록)을 명확하게 분리하는 작업을 계속 진행해야 합니다.

### ✅ Verdict

**REJECT**

**이유**: 이 PR은 `SettlementSystem` 도입이라는 매우 중요한 개선을 포함하고 있지만, 동시에 **프로젝트의 핵심 아키텍처 원칙을 무너뜨리는 심각한 회귀**를 도입했습니다. 의사결정 로직에 부작용을 허용하는 변경은 테스트의 어려움을 가중시키고 향후 기술 부채를 급증시킬 것입니다.

자산 이동의 정합성을 확보하는 변경 사항은 매우 긍정적이므로, 해당 부분만 별도의 PR로 분리하여 제출하고, 의사결정 엔진 아키텍처를 변경하는 부분은 팀의 전체적인 합의하에 재설계를 거친 후 다시 논의하는 것이 바람직합니다.

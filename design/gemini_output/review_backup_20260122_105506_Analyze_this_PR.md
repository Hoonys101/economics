# 🔍 코드 리뷰 보고서: WO-110 Firm Logic Refactor

## 🔍 Summary
이번 변경은 `StandaloneRuleBasedFirmDecisionEngine`의 의사결정 로직을 상호 배타적인 구조에서 순차적인 (계획 → 실행 → 상거래) 구조로 리팩토링했습니다. 이로써 생산 계획과 고용/해고가 동시에 일어날 수 있게 되어 '의사결정 상호 배타성 버그'(TD-085)가 해결되었습니다. 또한, 기업이 재정적 압박을 받을 때만 초과 인력을 해고하는 '노동 비축(Labor Hoarding)' 로직이 도입되었습니다.

## 🚨 Critical Issues
**1. 하드코딩된 경제 파라미터 (Hardcoded Economic Parameters)**
- 코드 전반에 걸쳐 시뮬레이션의 핵심 동작을 결정하는 여러 '매직 넘버'가 하드코딩되어 있습니다. 이는 모델의 유연성과 유지보수성을 저해하는 심각한 문제입니다.
- **위치**: `simulation/decisions/standalone_rule_based_firm_engine.py`
  - `elif current_employees > needed_labor_for_production * 1.05:`: 인력 해고 버퍼 `1.05` (5%)가 하드코딩되었습니다.
  - `is_bleeding = firm.finance.consecutive_loss_turns > 5`: 연속 손실 허용 기간 `5` 턴이 하드코딩되었습니다.
  - `is_poor = firm.assets < getattr(..., 30000.0) * 0.5`: 빈곤 상태를 결정하는 자산 비율 `0.5`와 기본 창업 비용 `30000.0`이 하드코딩되었습니다.
- **위치**: `simulation/decisions/rule_based_firm_engine.py`
  - `min_wage = getattr(..., 5.0)`: 대체(fallback) 최저 임금 `5.0`이 하드코딩되었습니다.

**조치**: 이 값들은 모두 `config_module`을 통해 설정 가능하도록 변경해야 합니다.

## ⚠️ Logic & Spec Gaps
**1. 부정확한 함수 시그니처 (Inaccurate Function Signature)**
- **위치**: `simulation/decisions/rule_based_firm_engine.py`, `_fire_excess_labor` 함수
- **내용**: 해당 함수는 직원을 해고하는 상태 변경(side effect)을 수행할 뿐, 어떠한 `Order`도 생성하지 않음에도 `-> List[Order]`를 반환 타입으로 가집니다. 실제로는 항상 빈 리스트(`[]`)를 반환하고 있어, 함수의 역할을 오해하게 만들 수 있습니다.

## 💡 Suggestions
**1. 로깅 시 Enum 사용 (Use Enums for Logging)**
- **위치**: `simulation/decisions/standalone_rule_based_firm_engine.py`
- **제안**: 전술(tactic)을 로깅할 때 `"ADJUST_WAGES"`, `"FIRING"`과 같은 문자열 리터럴 대신, 기존처럼 `Tactic` Enum의 `chosen_tactic.name` 속성을 사용하는 것이 오타를 방지하고 코드의 일관성을 유지하는 데 더 좋습니다.

**2. 함수 반환 타입 명확화 (Clarify Return Type)**
- **위치**: `simulation/decisions/rule_based_firm_engine.py`, `_fire_excess_labor` 함수
- **제안**: 함수가 `Order`를 반환하지 않는 것이 명확하므로, 반환 타입을 `-> None`으로 변경하여 함수의 의도를 명확하게 표현하는 것을 권장합니다.

## ✅ Verdict
**REQUEST CHANGES**

**사유:** 핵심적인 버그 수정과 아키텍처 개선은 매우 훌륭합니다. 그러나 시뮬레이션의 중요 파라미터를 하드코딩한 것은 프로젝트 가이드라인에 위배되는 심각한 문제입니다. 위에 언급된 **Critical Issues**를 수정한 후 다시 리뷰를 요청하십시오.

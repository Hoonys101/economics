# 🔍 Git Diff Review: `phase23-harvest-verification`

## 🔍 Summary
이 변경 사항은 시뮬레이션의 '맬서스 함정'(인구 붕괴) 문제를 해결하기 위한 커밋입니다. 주요 내용은 경제 파라미터 조정, 기업의 의사결정 로직 버그 수정, 그리고 신생아 에이전트의 생존율을 높이기 위한 **임시적인 몽키패치(Monkey Patch)** 도입입니다. 이 패치를 통해 신생아 에이전트는 더 단순하고 안정적인 `RuleBasedHouseholdDecisionEngine`을 강제로 사용하게 됩니다.

## 🚨 Critical Issues
- **[CRITICAL] 아키텍처 위반: 몽키패치(Monkey Patch) 도입**
  - **파일**: `scripts/verify_phase23_harvest.py`
  - **내용**: `DemographicManager.process_births` 함수의 동작을 런타임에 변경하여, 새로 생성된 모든 가계(Household) 에이전트의 `decision_engine`을 `RuleBasedHouseholdDecisionEngine`으로 강제 교체합니다.
  - **위험성**: 이는 `TD-086`으로 등록된 명백한 아키텍처 위반이며, 심각한 기술 부채입니다. "ID > 100"이라는 가정으로 신규 에이전트를 식별하는 방식은 매우 취약하며, 향후 예기치 않은 부작용을 유발할 수 있습니다. 이는 테스트 스크립트가 프로덕션 코드의 동작을 직접 주입하여 변경하는 위험한 패턴입니다.

## ⚠️ Logic & Spec Gaps
- **과도하게 완화된 검증 환경**
  - **파일**: `scripts/verify_phase23_harvest.py`
  - **내용**: 검증 스크립트 내에서 에이전트 사망 조건을 크게 완화했습니다. (`SURVIVAL_NEED_DEATH_THRESHOLD = 200.0`, `HOUSEHOLD_DEATH_TURNS_THRESHOLD = 50`)
  - **문제점**: 시뮬레이션 성공(인구 폭증)이 근본적인 경제 모델 개선이 아닌, 단순히 '쉬운 모드'로 설정된 테스트 환경 덕분일 수 있습니다. 이는 다른 잠재적 불안정성을 가릴 수 있습니다.

- **문서와 값의 불일치**
  - **파일**: `config.py`
  - **내용**: `FOOD_CONSUMPTION_QUANTITY`의 주석은 "더 많이 먹는다"고 되어 있지만 값은 `1.0`으로 유지됩니다. 실제 대량 소비는 `FOOD_CONSUMPTION_MAX_PER_TICK` 증가로 구현되었으나, 주석이 오해를 유발할 수 있습니다.

## 💡 Suggestions
- **몽키패치 즉시 제거 및 아키텍처 개선 제안**
  - `verify_phase23_harvest.py`의 몽키패치를 제거해야 합니다. 대신, `DemographicManager` 내에 신생아 에이전트의 엔진을 결정하는 **팩토리 메서드(Factory Method)** 또는 **전략 패턴(Strategy Pattern)**을 도입하여, 시뮬레이션 설정에 따라 적절한 엔진을 선택하도록 구조를 개선해야 합니다.

- **방어적 코드 추가 (Good)**
  - **파일**: `simulation/ai/household_ai.py`, `simulation/tick_scheduler.py`
  - **내용**: `MagicMock` 객체로 인한 오류를 방지하기 위해 `isinstance` 체크 및 `hasattr` 체크를 추가한 것은 테스트 안정성을 높이는 좋은 방어적 코딩입니다.

- **하드코딩 제거 (Excellent)**
  - **파일**: `simulation/ai/vectorized_planner.py`
  - **내용**: 출산 가능 연령을 하드코딩된 값 대신 `config`에서 읽어오도록 변경한 것은 설정 유연성을 높이는 훌륭한 개선입니다.

- **버그 수정 (Excellent)**
  - **파일**: `simulation/decisions/standalone_rule_based_firm_engine.py`
  - **내용**: `TD-085` (생산 확대와 고용 결정의 상호 배제) 버그를 수정한 것은 시스템의 논리적 정합성을 회복시킨 중요한 수정입니다.

## ✅ Verdict
**REQUEST CHANGES**

이 커밋은 `TD-085`와 같은 중요한 논리 버그를 해결하고 설정 유연성을 높이는 등 긍정적인 변경 사항을 포함하고 있습니다. 하지만 `TD-086` 해결을 위해 도입된 **몽키패치**는 심각한 아키텍처 원칙 위반으로, 즉각적인 수정이 필요합니다.

기술 부채를 명시적으로 인지하고 등록한 점은 긍정적이나, 이러한 임시방편이 코드 베이스에 머지되는 것을 허용할 수 없습니다. 제안된 아키텍처 개선안을 적용하여 몽키패치를 제거한 후 다시 리뷰를 요청하십시오.

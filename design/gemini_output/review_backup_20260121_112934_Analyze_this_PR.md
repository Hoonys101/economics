# 🔍 Git Diff Review: WO-094 Simulation & Reverted Refactoring

## 🔍 Summary

이 PR은 화학 비료 도입 효과를 검증하는 `WO-094` 시뮬레이션 스크립트(`verify_phase23_harvest.py`)를 추가합니다. 스크립트 실행 결과, 인구 붕괴 등 심각한 오류로 시뮬레이션이 **실패**했으며, 그 원인 분석 보고서가 함께 제출되었습니다. 그러나 이 과정에서 이전에 완료되었어야 할 기술 부채 청산(`WO-095`) 작업이 **원복(revert)**되었고, 핵심 컴포넌트의 버그를 수정하는 대신 테스트 스크립트 내에서 **위험한 몽키패칭(Monkey-Patching)**을 사용하여 문제를 우회하고 있습니다.

## 🚨 Critical Issues

1.  **[CRITICAL] 기술 부채 청산 작업 원복 (Regression)**
    *   **위치**: `modules/household/econ_component.py`, `simulation/components/production_department.py`
    *   **문제**: `WO-095`에서 진행된 하드코딩 제거 및 로직 개선 사항이 모두 이전 상태로 되돌려졌습니다. `econ_component.py`에는 `maxlen=10`, `maxlen=30`과 같은 매직 넘버가 다시 하드코딩되었고, `config.py`에서 관련 설정이 삭제되었습니다. 이는 명백한 퇴보이며, 유지보수성을 심각하게 저해합니다. (`design/work_orders/WO-095-Tech-Debt-Cleanup.md` 파일 삭제로 확인)

2.  **[CRITICAL] 핵심 로직의 몽키패칭 (Unsafe Practice)**
    *   **위치**: `scripts/verify_phase23_harvest.py`
    *   **문제**: `EconomyManager.consume`, `RuleBasedHouseholdDecisionEngine.make_decisions` 등 시뮬레이션의 핵심 컴포넌트 동작을 테스트 스크립트 내에서 임시로 뜯어고치고 있습니다. 이는 매우 위험한 방식이며, 다음과 같은 문제를 야기합니다.
        *   **숨겨진 버그**: 실제 버그는 그대로 남아있어 다른 부분에서 언제든지 동일한 문제가 발생할 수 있습니다.
        *   **일관성 파괴**: 오직 이 스크립트를 실행할 때만 버그가 가려지므로, 시스템 전체의 동작을 예측하기 어렵게 만듭니다.
        *   **기술 부채 증가**: 임시방편적인 패치는 그 자체로 심각한 기술 부채입니다.

3.  **[CRITICAL] 시뮬레이션 파라미터 하드코딩 (Hardcoding)**
    *   **위치**: `scripts/verify_phase23_harvest.py` (파일 상단)
    *   **문제**: `Config.SIMULATION_TICKS = 200`, `Config.food_tfp_multiplier = 3.0` 등 시나리오의 핵심 변수들이 `config/scenarios/` 파일이 아닌 스크립트 내에 하드코딩되어 있습니다. 이는 시나리오의 재사용과 관리를 불가능하게 만듭니다.

## ⚠️ Logic & Spec Gaps

1.  **불완전한 임무 완수 (Incomplete Mission)**
    *   `WO-094`의 목표는 성장을 "검증"하는 것이었습니다. 제출된 보고서에 따르면 시뮬레이션은 처참하게 실패했으며, 이는 근본적인 버그가 해결되지 않았음을 의미합니다. 버그를 발견한 것은 좋았으나, 올바른 해결책(핵심 컴포넌트 수정) 없이 실패한 결과물을 제출한 것은 임무를 완수했다고 보기 어렵습니다.

## 💡 Suggestions

1.  **몽키패치 제거 및 핵심 컴포넌트 직접 수정**: `verify_phase23_harvest.py`에 적용된 모든 `patched_*` 함수들을 제거하십시오. 대신, 해당 패치에서 수정한 로직을 `EconomyManager`, `RuleBasedHouseholdDecisionEngine` 등 **원본 클래스 파일에 직접 적용**하여 버그를 근본적으로 해결해야 합니다.

2.  **기술 부채 리팩토링 복원**: 삭제된 `WO-095` 작업을 다시 수행하십시오. `econ_component.py`의 하드코딩된 `maxlen`을 `config.py`의 상수를 사용하도록 되돌리고, `production_department.py`의 로직을 다시 간결하게 만드십시오.

3.  **시나리오 설정 분리**: `verify_phase23_harvest.py`에 하드코딩된 시뮬레이션 설정 값들을 `config/scenarios/phase23_great_harvest.json` (또는 yaml)과 같은 별도의 설정 파일로 분리하고, 스크립트에서 이를 불러와 사용하도록 수정하십시오.

## ✅ Verdict

**REJECT**

이 PR은 심각한 구조적 문제와 코드 품질 저하를 유발합니다. 버그를 발견한 것은 긍정적이나, 해결 방식이 부적절하고 이전에 해결된 기술 부채를 다시 도입하는 등 문제가 심각하여 병합을 거부합니다. 제안된 수정 사항들이 모두 반영된 후 재검토하겠습니다.

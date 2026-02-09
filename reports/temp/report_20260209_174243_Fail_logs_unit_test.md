# 통합 수리 가이드: Orchestrator-Engine 리팩토링 후속 조치

## Executive Summary

Orchestrator-Engine 아키텍처 리팩토링의 여파로 다수의 테스트가 실패하고 있으며, 이는 주로 API 시그니처 변경, 프로토콜/DTO 정의 누락, 그리고 레거시 코드 의존성에서 비롯됩니다. `total_test_Debug.txt`에서 확인된 5개의 테스트 콜렉션 오류는 즉시 수정이 필요한 심각한 `ImportError`를 나타냅니다. `unit_test_debug.txt`에서는 `settlement_system.transfer`의 `currency` 인자 누락, `_sub_assets`와 같은 레거시 메서드 호출, 이름이 변경되거나 제거된 API 속성 접근 등 25개의 테스트 실패가 확인되었습니다. `leak_test_debug.txt`는 `production_engine`에서 직원의 `labor_skill`이 `None`일 때 발생하는 `TypeError` 런타임 오류를 보여줍니다.

이 문서는 발견된 모든 문제를 해결하기 위한 통합 체크리스트를 제공합니다.

## Detailed Analysis

### 1. 테스트 콜렉션 오류 (심각)

- **상태**: ❌ 5개 테스트 파일이 `ImportError` 또는 `ModuleNotFoundError`로 인해 테스트를 수집조차 못하고 있습니다.
- **원인**:
    - **DTO/프로토콜 누락**: 리팩토링 과정에서 `modules/household/api.py`와 같은 API 파일에 `IConsumptionManager`, `IDecisionUnit`, `IEconComponent` 등의 프로토콜이 정의되지 않았습니다. `simulation.dtos`에서 `GovernmentStateDTO`를 찾을 수 없습니다. (`total_test_Debug.txt`)
    - **레거시 모듈 참조**: `TD-PH10`에 따라 `simulation.base_agent` 모듈이 삭제되었음에도, `tests/unit/test_base_agent.py`가 이를 참조하고 있습니다. (`total_test_Debug.txt`)
    - **인터페이스 미정의**: `test_liquidation_manager.py`에서 `IShareholderRegistry`라는 정의되지 않은 이름을 사용하고 있습니다. (`unit_test_debug.txt`)

### 2. API 시그니처 및 계약 불일치

- **상태**: ⚠️ 다수의 테스트가 `AssertionError`, `AttributeError`, `TypeError`로 실패하고 있습니다.
- **원인**:
    - **`transfer` 메서드 변경**: `settlement_system.transfer` 메서드 호출에 `currency='USD'` 키워드 인자가 추가되었으나, `test_housing_handler.py`와 `test_housing_system.py`의 여러 테스트 케이스에서 이 인자를 누락하여 `AssertionError`가 발생했습니다.
    - **API 이름 변경/제거**:
        - `CommerceSystem`의 `execute_consumption_and_leisure` 메서드가 `finalize_consumption_and_leisure`로 이름이 변경되었습니다. (`test_commerce_system.py`)
        - `SettlementSystem`에서 `submit_saga` 메서드가 제거되었습니다. (`test_settlement_saga_integration.py`)
    - **메서드 시그니처 변경**: `EventSystem.execute_scheduled_events` 메서드가 `config` 인자를 추가로 요구하게 변경되었습니다. (`test_event_system.py`)
    - **레거시 속성 접근**: `test_demographic_manager_newborn.py` 와 `test_ministry_of_education.py`에서 `_sub_assets`와 같은 내부 속성/메서드를 직접 호출하고 있습니다. 이는 `SettlementSystem`을 사용하도록 리팩토링되어야 합니다.

### 3. 런타임 오류 및 로직 결함

- **상태**: ⚠️ 런타임 `TypeError`와 로직 오류로 인한 테스트 실패가 발견되었습니다.
- **원인**:
    - **`NoneType` 처리 미흡**: `leak_test_debug.txt`의 트레이스백은 `production_engine.py`에서 R&D 성과를 계산할 때 발생합니다. `hr_state.employees` 중 `labor_skill`이 `None`인 직원이 있어 `sum()` 함수 실행 중 `TypeError`가 발생합니다.
    - **정렬 로직 오류**: `ministry_of_education.py`에서 목(Mock) 객체의 `wallet.get_balance()` 결과를 정렬하려고 시도하다가 `TypeError`가 발생했습니다. 목 객체에 비교 가능한 `return_value`가 설정되지 않았습니다.
    - **상태 반환 오류**: `test_housing_handler.py`의 `test_handle_payment_failure`에서 최종 결제 실패 시에도 핸들러가 `True`를 반환하여 `AssertionError: True is not false`가 발생했습니다. 롤백 로직이 상태를 올바르게 전파하지 못하고 있습니다.

## Risk Assessment

- **DTO Contract Instability**: DTO와 프로토콜의 잦은 변경 및 불일치는 시스템 전반에 걸쳐 예기치 않은 `AttributeError`와 `ImportError`를 유발하며, 이는 `TECH_DEBT_LEDGER.md`의 `[Pattern] DTO Contract Instability` 항목과 일치하는 문제입니다.
- **Protocol Purity Violation**: `_sub_assets`와 같은 내부 구현에 직접 의존하는 테스트는 리팩토링에 매우 취약하며, 이는 `TD-LIQ-INV`에서 지적된 프로토콜 순수성 위반과 같은 맥락의 문제입니다.

## Repair Checklist

### ✅ **Phase 1: Collection Errors (High Priority)**

1.  **`tests/unit/test_base_agent.py`**
    - [ ] `simulation.base_agent` 모듈은 `TD-PH10`에 따라 삭제되었으므로, 해당 테스트 파일(`tests/unit/test_base_agent.py`)을 삭제하십시오.
2.  **`modules/household/api.py`**
    - [ ] `IConsumptionManager`, `IDecisionUnit`, `IEconComponent`, `OrchestrationContextDTO` 프로토콜 및 DTO 정의를 추가하십시오.
3.  **`simulation/dtos/__init__.py`**
    - [ ] `GovernmentStateDTO`의 정확한 위치를 찾아 `tests/unit/modules/government/test_adaptive_gov_brain.py`의 import 구문을 수정하거나, DTO가 누락되었다면 생성하십시오.
4.  **`tests/unit/systems/test_liquidation_manager.py`**
    - [ ] `IShareholderRegistry` 프로토콜을 관련 `api.py` 파일에 정의하고 테스트 파일에서 import 하십시오.

---

### ✅ **Phase 2: API Mismatch & Runtime Errors**

5.  **`settlement_system.transfer` 호출 업데이트**
    - [ ] `tests/unit/systems/handlers/test_housing_handler.py`: 모든 `transfer.assert_any_call` 또는 `assert_called_with`에 `currency='USD'` 인자를 추가하십시오.
    - [ ] `tests/unit/systems/test_housing_system.py`: 모든 `transfer.assert_any_call`에 `currency='USD'` 인자를 추가하십시오.
6.  **`simulation/components/engines/production_engine.py`**
    - [ ] `execute_rd_outcome` 메서드 내 `sum()` 로직을 수정하여 직원의 `labor_skill`이 `None`일 경우 0으로 처리하도록 변경하십시오. (예: `sum(emp.labor_skill or 0 for emp in ...)`).
7.  **`tests/unit/systems/test_demographic_manager_newborn.py`**
    - [ ] `parent._sub_assets` 호출을 제거하고, `simulation.settlement_system.transfer`를 모킹(mocking)하여 자산 이전이 올바르게 호출되는지 확인하도록 테스트를 수정하십시오.
8.  **`tests/unit/systems/test_commerce_system.py`**
    - [ ] `test_execute_consumption_and_leisure`: 메서드 호출을 `commerce_system.execute_consumption_and_leisure`에서 `commerce_system.finalize_consumption_and_leisure`로 변경하십시오.
    - [ ] `test_fast_track_consumption_if_needed`: `reflux_system`을 `commerce_system`에서 직접 가져오지 말고, 테스트의 `context` 딕셔너리에 목 객체로 주입하도록 수정하십시오.
9.  **`tests/unit/systems/test_event_system.py`**
    - [ ] 모든 `event_system.execute_scheduled_events` 호출에 목 `config` 객체를 추가 인자로 전달하십시오.
10. **`tests/unit/systems/test_firm_management_*.py`**
    - [ ] `test_spawn_firm_leak_detection`: `spawn_firm` 로직을 검토하여 `settlement_system.transfer`가 호출되지 않는 문제를 해결하십시오.
    - [ ] `test_spawn_firm_missing_settlement_system`: `spawn_firm`에 `settlement_system`이 `None`일 때 `RuntimeError`를 발생시키는 방어 코드가 누락된 문제를 해결하십시오.
11. **`simulation/systems/ministry_of_education.py`**
    - [ ] `run_public_education` 내 정렬 키(key) 람다 함수에서 목 객체가 비교 가능하도록 `x._econ_state.wallet.get_balance.return_value`를 설정하여 `TypeError`를 해결하십시오. (테스트 파일에서 수정 필요: `test_ministry_of_education.py`)
12. **`tests/unit/systems/test_ministry_of_education.py`**
    - [ ] `_sub_assets`를 확인하는 레거시 테스트를 `settlement_system.transfer` 호출을 확인하도록 현대화하십시오.
    - [ ] 주석 처리된 테스트들을 활성화하고, `run_public_education` 리팩토링에 맞춰 `transfer` 호출 횟수 등을 검증하도록 수정하십시오.
13. **`tests/unit/systems/handlers/test_housing_handler.py`**
    - [ ] `test_handle_payment_failure`: 최종 결제 실패 시 `handle` 메서드가 `False`를 반환하도록 롤백 로직을 수정하십시오.
14. **`tests/unit/systems/test_settlement_saga_integration.py`**
    - [ ] `settlement.submit_saga(saga)` 호출을 `SettlementSystem`의 새로운 API에 맞게 수정하십시오. (Saga가 이제 Orchestrator를 통해 직접 관리될 가능성이 높음)
15. **`tests/unit/systems/test_sensory_system.py`**
    - [ ] `generate_government_sensory_dto`가 `inequality_tracker`로부터 Gini 계수를 올바르게 조회하여 DTO에 채우도록 로직을 수정하십시오.

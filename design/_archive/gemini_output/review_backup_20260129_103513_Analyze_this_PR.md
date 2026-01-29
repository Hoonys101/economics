# 🔍 Summary

`AIDrivenHouseholdDecisionEngine`의 대규모 리팩토링 PR입니다. 기존의 거대한(monolithic) 의사결정 엔진을 소비, 노동, 자산, 주택 등 각 책임에 따라 별도의 `Manager` 클래스로 분리하고, `Coordinator` 패턴을 적용하여 코드의 응집도를 높이고 단일 책임 원칙(SoC)을 강화했습니다.

특히, 기존 로직과의 동작 동등성을 보장하기 위해 레거시 엔진을 fixture로 만들고 새로운 엔진과 출력을 비교하는 `test_behavioral_equivalence` 테스트를 추가한 점은 매우 훌륭한 접근입니다.

## 🚨 Critical Issues

- **None**: 보안 취약점, 하드코딩된 경로/비밀 값, 또는 심각한 논리 오류는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

1.  **DTO 상태 임시 변경 (Temporary DTO State Mutation)**
    - **위치**: `simulation/decisions/household/asset_manager.py` > `decide_investments` 함수
    - **내용**: `household.assets -= repay_amount`와 같이, 전달받은 `household` DTO의 상태를 계산 과정에서 임시로 변경하고 `finally` 블록에서 복원하는 패턴이 사용되었습니다. 이는 DTO의 불변성(immutability) 원칙을 위반하며, 복잡한 로직에서 미묘한 버그를 유발할 수 있는 위험한 코드 스멜(code smell)입니다. 주석으로 "Simulation logic kept for parity"라고 명시되어 있지만, 이는 기술 부채로 관리되어야 합니다.

2.  **상태를 가지는 Manager 클래스 (Stateful Manager Class)**
    - **위치**: `simulation/decisions/household/housing_manager.py` > `__init__` 및 `decide_housing`
    - **내용**: `HousingManager`가 생성자에서 `agent`와 `config`를 받고, `decide_housing` 메서드가 호출될 때마다 `self.agent`와 `self.config`를 컨텍스트의 값으로 덮어씁니다. Manager 클래스는 상태를 가지지 않는(stateless) 서비스 형태가 이상적입니다. 이렇게 인스턴스 변수를 계속해서 교체하는 방식은 재사용성을 떨어뜨리고 잠재적인 동시성 문제를 야기할 수 있습니다.

## 💡 Suggestions

1.  **Manager를 Stateless로 전환**: `HousingManager`를 포함한 모든 Manager 클래스는 내부 상태를 가지지 않도록 리팩토링하는 것을 권장합니다. 필요한 모든 데이터는 `decide_*` 메서드의 `context` 파라미터를 통해서만 전달받아야 합니다. `__init__`에서는 의존성 주입(예: logger)만 처리하고, 에이전트 상태를 인스턴스 변수(`self.agent`)로 저장하지 마십시오.

2.  **하드코딩된 Fallback 값 제거**
    - **위치**: `simulation/decisions/household/asset_manager.py` > `get_savings_roi`
    - **내용**: `default_rate = config.default_mortgage_rate if config else 0.05`와 같이 `config` 객체가 없을 경우 `0.05`라는 상수를 사용합니다. 설정값이 없는 경우는 시스템의 오류 상황일 가능성이 높으므로, 하드코딩된 값을 사용하기보다는 에러를 발생시키거나 중앙에서 관리되는 기본값을 사용하도록 수정해야 합니다.

3.  **DTO 불변성 유지**: `AssetManager`에서 DTO 상태를 임시로 변경하는 대신, 필요한 계산을 위한 값을 지역 변수로 처리하도록 로직을 수정하여 DTO의 불변성을 유지하는 것이 좋습니다.

## 🧠 Manual Update Proposal

이번 리팩토링 과정에서 발견된 "DTO 명세와 실제 사용법의 불일치"는 중요한 인사이트이므로 기술 부채 대장에 기록할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
    ```markdown
    ## TD-118: DTO Contract-Implementation Mismatch (Household.inventory)

    - **현상 (Phenomenon)**: `HouseholdStateDTO.inventory` 필드는 공식적으로 `List[GoodsDTO]`로 정의될 수 있으나, 실제 의사결정 로직에서는 `household.inventory.get("basic_food")`와 같이 `Dict[str, float]`처럼 사용되고 있습니다.
    - **원인 (Cause)**: 레거시 구현이 딕셔너리 형태의 접근에 의존하고 있었으며, 이번 리팩토링에서 동작 동등성을 유지하기 위해 해당 사용법을 그대로 유지했습니다. 이로 인해 공식 DTO 계약과 실제 구현 간의 불일치가 발생했습니다.
    - **해결 (Solution)**: `HouseholdStateDTO`의 `inventory` 타입을 `Dict[str, float]`으로 명확히 확정하거나, 모든 관련 코드를 `List[GoodsDTO]`를 순회하여 사용하도록 리팩토링해야 합니다. 이 불일치는 향후 혼란과 잠재적 런타임 오류를 방지하기 위해 반드시 해결되어야 합니다.
    - **교훈 (Lesson)**: 대규모 리팩토링은 공식 데이터 계약(DTO)과 실제 구현 간의 숨겨진 불일치를 발견하는 계기가 될 수 있습니다. 동작 동등성 테스트는 기존의 코드 스멜을 유지하도록 강제할 수 있으며, 이러한 부분은 명시적인 기술 부채로 기록하고 추적해야 합니다.
    ```

## ✅ Verdict

**REQUEST CHANGES**

전체적인 아키텍처 개선과 테스트 커버리지 확보는 매우 훌륭합니다. 위에 언급된 `DTO 상태 변경` 및 `Stateless Manager`와 같은 주요 제안 사항들을 반영하여 코드를 더욱 견고하게 만들어 주시기 바랍니다.

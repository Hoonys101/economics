# 🔍 Git Diff Review: Refactor `ai_driven_household_engine.py`

## 🔍 Summary

이 PR은 거대 파일(`God File`)이었던 `ai_driven_household_engine.py`를 **소비(Consumption), 노동(Labor), 자산(Asset), 주거(Housing)**의 4가지 책임으로 분리된 개별 Manager 모듈로 리팩토링합니다. 기존의 복잡한 로직을 각각의 Manager로 위임하고, 메인 엔진은 이들을 오케스트레이션하는 **코디네이터(Coordinator) 역할**을 수행하도록 변경되었습니다. 이 과정에서 발견된 기술 부채를 명확히 문서화하고, 동작 동등성을 보장하기 위한 테스트를 추가한 점이 인상적입니다.

## 🚨 Critical Issues

**없음.**

- 코드에서 API 키, 비밀번호, 시스템 절대 경로 등 하드코딩된 민감 정보를 발견하지 못했습니다.
- 외부 리포지토리 참조나 Supply Chain을 위협할 만한 의존성이 추가되지 않았습니다.

## ⚠️ Logic & Spec Gaps

**없음.**

- 이번 리팩토링의 핵심 목표는 기존 로직의 동작 동등성을 유지하는 것이었으며, 추가된 `test_behavioral_equivalence` 테스트를 통해 이를 성공적으로 검증하고 있습니다.
- 특히 주목할 만한 점은 `simulation/decisions/household/labor_manager.py`에서 발견된 **DTO 계약과 실제 구현 간의 불일치**입니다.
  ```python
  # simulation/decisions/household/labor_manager.py

  # Note: Legacy code accessed `basic_food` from inventory. DTO has `inventory: List[GoodsDTO]` usually,
  # but legacy code treated it as Dict?
  # ...
  # I will assume dict access works as per legacy code parity.
  food_inventory = household.inventory.get("basic_food", 0.0)
  ```
- 개발자는 `HouseholdStateDTO.inventory`가 공식적으로는 `List` 타입일 수 있으나 레거시 코드에서는 `Dict`처럼 사용되고 있음을 인지했습니다. 이 문제를 그냥 넘어가지 않고, 동작 동등성을 위해 기존 구현을 유지하되 **이 발견 사항을 기술 부채 원장(`TECH_DEBT_LEDGER.md`)에 명시적으로 기록**했습니다. 이는 매우 바람직한 절차입니다.

## 💡 Suggestions

- **구조 개선**: 전반적인 리팩토링 구조는 매우 훌륭합니다. 각 Manager에 필요한 데이터를 `Context` DTO로 묶어 전달하는 방식은 의존성을 명확하게 하고 테스트 용이성을 크게 향상시킵니다.
- **불변성(Immutability) 개선**: 레거시 코드에서 `household.assets`를 직접 수정한 뒤 `try...finally`로 복원하던 부분을, `AssetManager`에서 `effective_cash`라는 지역 변수를 사용하도록 개선한 것은 DTO의 불변성을 존중하는 좋은 변경입니다.

## 🧠 Manual Update Proposal

개발자가 이미 `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` 파일을 올바르게 수정했습니다. 해당 변경 사항을 그대로 반영할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  - `TD-118` 기술 부채 항목 추가:
    ```markdown
    | **TD-118** | 2026-01-29 | **DTO Contract-Implementation Mismatch** | Refactor `HouseholdStateDTO.inventory` usage to respect List type or update DTO to Dict | Potential Runtime Errors / Confusion | **ACTIVE** |
    ```
  - `4. Household Modularization (WO-141)` 상세 내용 추가:
    ```markdown
    ### 4. Household Modularization (WO-141)
    - **현상**: `HouseholdStateDTO.inventory` 필드는 공식적으로 `List[GoodsDTO]`로 정의될 수 있으나, 실제 의사결정 로직에서는 `household.inventory.get("basic_food")`와 같이 `Dict[str, float]`처럼 사용되고 있습니다.
    - **원인**: 레거시 구현이 딕셔너리 형태의 접근에 의존하고 있었으며, 이번 리팩토링에서 동작 동등성을 유지하기 위해 해당 사용법을 그대로 유지했습니다. 이로 인해 공식 DTO 계약과 실제 구현 간의 불일치가 발생했습니다.
    - **해결**: `HouseholdStateDTO`의 `inventory` 타입을 `Dict[str, float]`으로 명확히 확정하거나, 모든 관련 코드를 `List[GoodsDTO]`를 순회하여 사용하도록 리팩토링해야 합니다. 이 불일치는 향후 혼란과 잠재적 런타임 오류를 방지하기 위해 반드시 해결되어야 합니다.
    - **교훈**: 대규모 리팩토링은 공식 데이터 계약(DTO)과 실제 구현 간의 숨겨진 불일치를 발견하는 계기가 될 수 있습니다. 동작 동등성 테스트는 기존의 코드 스멜을 유지하도록 강제할 수 있으며, 이러한 부분은 명시적인 기술 부채로 기록하고 추적해야 합니다.
    ```

## ✅ Verdict

**APPROVE**

매우 높은 품질의 리팩토링입니다. 복잡한 로직을 성공적으로 분리했을 뿐만 아니라, 그 과정에서 발견한 기존 코드의 문제를 정확히 식별하고 공식적인 기술 부채로 문서화하는 모범적인 절차를 보여주었습니다. 추가된 동작 동등성 테스트는 변경의 안정성을 효과적으로 보장합니다.

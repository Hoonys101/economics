# 🔍 Git Diff Review: `verify-mitosis-migration`

## 🔍 Summary

이 변경 사항은 기존의 `unittest` 기반 분열(mitosis) 테스트 (`tests/verify_mitosis.py`)를 삭제하고, `pytest` 기반의 새로운 검증 스크립트(`tests/verification/verify_mitosis.py`)로 대체합니다. 새로운 스크립트는 `Household.clone()` 기능 검증을 두 단계(Config만 실제, DecisionEngine까지 실제)로 나누어 점진적으로 테스트하는 더 구조적인 접근 방식을 취합니다.

## 🚨 Critical Issues

- 발견되지 않았습니다. 보안 및 하드코딩 관련 문제는 없습니다.

## ⚠️ Logic & Spec Gaps

1.  **자산 보존 법칙(Zero-Sum) 위반 가능성**: `test_mitosis_stage1` 및 `test_mitosis_stage2`에서, 자식 가구(`child_household`)의 자산이 올바르게 설정되었는지만 확인하고, 부모 가구(`real_household`)의 자산이 그만큼 감소했는지는 확인하지 않습니다.
    - **위험**: 이는 자산이 복제되는 심각한 "돈 복사" 버그를 놓칠 수 있습니다.
    - **누락된 검증**: 삭제된 테스트(`test_rich_family_mitosis`)에서는 부모와 자식 양쪽의 자산을 모두 검증(`self.assertAlmostEqual(parent.assets, 7500.0)`, `self.assertAlmostEqual(child.assets, 7500.0)`)하여 이 문제를 방지했습니다.

2.  **테스트 커버리지 감소 (주식 상속 누락)**: 삭제된 테스트 파일의 `test_legacy_inheritance`는 `shares_owned` (주식) 자산이 분열 시 올바르게 분배되는지 검증했습니다. 새로운 검증 스크립트에서는 이 시나리오가 완전히 누락되었습니다. 이는 중요한 자산 이전 로직에 대한 테스트 커버리지 후퇴입니다.

3.  **AI 상태 검증 약화**: 삭제된 `test_brain_inheritance` 테스트는 복제된 Q-테이블의 *내용*까지 검증했습니다 (`self.assertIn((0,0), child_q_table)`). 반면, 새로운 테스트는 단순히 속성의 존재 여부(`assert hasattr(child_ai, 'q_consumption')`)만 확인합니다. 이는 AI 상태 상속을 검증하기에는 매우 약한 조건입니다.

## 💡 Suggestions

1.  **자산 보존 검증 추가**: `clone()` 호출 후, `parent.assets + child.assets == initial_parent_assets` 와 같이 부모의 자산이 정확히 감소했는지 확인하는 `assert` 구문을 반드시 추가해야 합니다.

2.  **주식 상속 테스트 복원**: 삭제된 `test_legacy_inheritance`에 해당하는 테스트 케이스를 새로운 `verify_mitosis.py` 파일에 다시 추가하여, 주식과 같은 복합 자산의 이전 로직을 검증해야 합니다.

3.  **AI 상태 검증 강화**: 단순히 속성 존재 여부만 확인할 것이 아니라, Q-테이블과 같은 핵심 AI 상태가 의도대로 (값 복사 또는 돌연변이 포함) 올바르게 복제되었는지 더 깊이 있게 검증해야 합니다.

## ✅ Verdict

**REQUEST CHANGES**

새로운 테스트 구조화 시도는 좋으나, 그 과정에서 핵심적인 자산 이전 및 상속 로직에 대한 테스트 커버리지가 심각하게 후퇴했습니다. 위에 지적된 로직 및 커버리지 갭을 수정한 후 다시 리뷰를 요청하십시오.

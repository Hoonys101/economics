# 🔍 Git Diff Review: `refactor-firm-management-leak`

## 🔍 Summary

본 변경 사항은 `FirmSystem`의 회사 설립 로직을 리팩토링하여, 자본금 이체 시 `SettlementSystem`의 사용을 강제합니다. 이로써 잠재적인 자금 유실(Leak)을 유발할 수 있었던 레거시 폴백(Fallback) 로직이 제거되었고, 시스템의 데이터 정합성이 향상되었습니다. 또한, 변경 사항을 검증하기 위한 새로운 단위 테스트가 추가되었습니다.

## 🚨 Critical Issues

- 해당 없음. 보안 위반, 하드코딩, 또는 심각한 버그는 발견되지 않았습니다. 오히려 잠재적인 자금 유실 버그를 해결한 커밋입니다.

## ⚠️ Logic & Spec Gaps

- 해당 없음. 로직이 더 견고해졌습니다.
  - `settlement_system`이 없을 때 `RuntimeError`를 발생시키는 것은 의존성을 명확히 하고 시스템이 비정상적인 상태로 실행되는 것을 방지하는 올바른 설계 결정입니다.
  - `settlement_system.transfer` 실패 시 `None`을 반환하고 상위 로직에서 이를 처리하도록 한 것은 견고한 오류 처리 방식입니다.
  - 새로 추가된 테스트(`test_firm_management_refactor.py`)는 핵심 변경 사항(의존성 강제, 이체 실패)을 정확하게 검증하고 있습니다.

## 💡 Suggestions

- 해당 없음. 변경 사항은 명확하고 잘 구현되었습니다.

## 🧠 Manual Update Proposal

이번 리팩토링은 "레거시 폴백 로직의 위험성"이라는 중요한 기술 부채를 해결한 좋은 사례입니다. 이 경험을 프로젝트의 지식 베이스에 기록하여 유사한 실수를 방지할 것을 제안합니다.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  - **현상 (Phenomenon)**:
    - 회사 설립 과정에서 자본금 이체가 부분적으로만 성공하여 자금이 소실될 위험(Money Leak)이 있었습니다.
  - **원인 (Cause)**:
    - `FirmSystem` 내부에 `SettlementSystem`을 사용하지 않는 레거시 폴백(Fallback) 로직이 존재했습니다. 이 로직은 자산 이동을 위해 `founder._sub_assets()`와 `firm._add_assets()`를 개별적으로 호출했습니다. 이 두 연산은 원자적(atomic)으로 묶여있지 않아, 중간에 실패할 경우 한쪽의 자산만 변경되는 데이터 불일치를 유발할 수 있었습니다.
  - **해결 (Solution)**:
    - `FirmSystem.spawn_firm`에서 레거시 폴백 로직을 완전히 제거했습니다.
    - 이제 `SettlementSystem`이 없는 경우 `RuntimeError`를 발생시켜, 중앙화된 자산 이동 시스템의 사용을 강제합니다.
    - 모든 자본금 이체는 `settlement_system.transfer`를 통해서만 이루어지도록 일원화되었습니다.
  - **교훈 (Lesson Learned)**:
    - 분산된 수동 자산 이전 로직(예: 각기 다른 객체의 `_add` / `_sub` 메서드 호출)은 기술 부채의 주요 원천이며 데이터 무결성을 심각하게 훼손할 수 있습니다.
    - 핵심 경제 행위(자산 이전 등)는 반드시 원자성을 보장하는 중앙화된 시스템(예: `SettlementSystem`)을 통해 처리해야 합니다. 또한, 이러한 핵심 시스템에 대한 의존성은 선택이 아닌 필수로 강제해야 합니다.
  ```

## ✅ Verdict

**APPROVE**

이 변경은 프로젝트의 안정성과 유지보수성을 크게 향상시킵니다. 위에 제안된 `TECH_DEBT_LEDGER.md` 업데이트는 후속 조치로 진행하는 것을 권장합니다.

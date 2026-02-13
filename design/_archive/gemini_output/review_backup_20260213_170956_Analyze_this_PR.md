이 PR은 **Mission INT-02 (Macro Shock Stress Test)** 요구사항에 따라 하이퍼인플레이션, 뱅크런, 재고 파괴 등의 'God-Mode' 개입 기능과 이를 안전하게 되돌릴 수 있는 Undo 기능을 구현한 건입니다.

---

## 🔍 Summary
- **Stress Test Implementation**: `FORCE_WITHDRAW_ALL`(뱅크런) 및 `DESTROY_INVENTORY`(재고 파괴) 명령 핸들러 추가.
- **Persistent Undo History**: `CommandService`의 Undo 스택을 `deque(maxlen=50)`로 변경하여 메모리 누수를 방지하면서도 과거 명령 복구를 지원.
- **Financial Integrity**: 뱅크런 처리 시 은행의 부채(예금)와 자산(현금)을 동시에 차감하는 2단계 프로세스를 통해 시스템 내 통화량 정합성(Zero-Sum) 유지.

## 🚨 Critical Issues
- **None**: 보안 위반, 하드코딩된 API Key 또는 외부 경로 등의 크리티컬한 이슈는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
- **Performance (O(N) Scan)**: `_handle_force_withdraw_all` 함수(line 369)에서 특정 은행의 예금주를 찾기 위해 `agent_registry.get_all_agents()`를 호출하여 전체 에이전트를 순회합니다. 이는 에이전트 수가 수만 명 단위로 확장될 경우 시뮬레이션 틱 레이턴시를 유발할 수 있습니다. (Insight 보고서에서 기술 부채로 명시됨)
- **Protocol Location**: `ISectorAgent` 프로토콜이 `command_service.py` 내부에 로컬로 정의되어 있습니다. 시스템 전반의 타입 일관성을 위해 추후 `modules/system/api.py` 등으로 이동을 권장합니다.

## 💡 Suggestions
- **Inventory Destruction Logic**: 현재 `DESTROY_INVENTORY`는 모든 에이전트의 모든 아이템을 일괄 비율로 파괴합니다. 특정 아이템(예: 'Food'만 파괴)을 지정할 수 있는 필터링 기능을 `new_value` DTO에 확장하면 더 정교한 시나리오 테스트가 가능할 것입니다.
- **Atomic Rollback**: 뱅크런 로직(line 417)에서 현금 이체 실패 시 `hasattr`을 이용해 예금을 복구하는 로직이 있는데, 이는 은행 구현체에 의존적입니다. `IBank` 인터페이스에 표준적인 `revert_withdrawal` 명세를 추가하는 것이 더 견고합니다.

## 🧠 Implementation Insight Evaluation
- **Original Insight**: Jules는 `deque`를 이용한 메모리 관리 전략과 뱅크런 시 M2 정합성을 지키기 위한 2단계 처리(부채 감소 후 자산 이전)를 핵심 인사이트로 기록했습니다.
- **Reviewer Evaluation**: 단순 기능 구현을 넘어, 시뮬레이션 엔진의 핵심인 **경제적 정합성(Zero-Sum)**을 유지하기 위해 발생할 수 있는 '돈 복사/증발' 버그를 사전에 차단한 점이 매우 우수합니다. 또한 $O(N)$ 성능 이슈를 감추지 않고 기술 부채로 명확히 정의한 점은 아키텍처 관리에 큰 도움이 됩니다.

## 📚 Manual Update Proposal (Draft)
- **Target File**: `design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md`
- **Draft Content**:
    ```markdown
    ## God-Mode Intervention Standards
    - **Two-Step Settlement**: 시스템 강제 명령(Stress Test)으로 자산을 이동시킬 때도 반드시 '부채 차감'과 '물리적 자산 이체'를 분리하여 수행함으로써 은행 재무제표의 균형을 유지해야 함.
    - **History Retention**: `CommandService`는 사용자 개입에 대비하여 최소 50틱 이상의 Undo 이력을 유지하되, `collections.deque`를 사용하여 Unbounded Memory 증가를 방지해야 함.
    ```

## ✅ Verdict
**APPROVE**
(보안 이슈가 없으며, 인사이트 보고서가 충실히 작성되었고, 통합 테스트를 통해 뱅크런 시 M2 정합성이 검증되었습니다.)
"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "fix-gov-structure": {
        "title": "Structural Fix: Government Singleton/List Mismatch",
        "command": "create",
        "instruction": (
            "Implement the 'Property Proxy' pattern to resolve the Government Singleton vs List mismatch.\n\n"
            "**Key Tasks:**\n"
            "1. **Refactor WorldState** (`simulation/world_state.py`): \n"
            "   - Add `@property` for `government` to access `governments[0]`.\n"
            "   - Add `@government.setter` to sync with `governments` list.\n"
            "   - Ensure `governments` is the SSoT.\n"
            "2. **Update Initializer** (`simulation/initialization/initializer.py`):\n"
            "   - Change direct `sim.government` assignment to `sim.world_state.governments.append(gov)`.\n"
            "3. **Verify**:\n"
            "   - Create a new test `tests/unit/test_government_structure.py` to verify singleton/list synchronization and initializer integrity.\n\n"
            "**Reference:** `design/3_work_artifacts/spec/STRUCT_GOV_FIX_SPEC.md`"
        ),
        "file": "design/3_work_artifacts/spec/STRUCT_GOV_FIX_SPEC.md",
        "wait": True
    },
    "cleanup-deprecations": {
        "title": "Hygiene: Cleanup Deprecated Code (Track B)",
        "command": "create",
        "instruction": (
            "Refactor deprecated code to enforce Zero-Sum Integrity and SEO patterns.\n\n"
            "**Key Tasks:**\n"
            "1. **Government.collect_tax** (`simulation/agents/government.py`):\n"
            "   - Deprecate/Replace with `settlement.settle_atomic`.\n"
            "   - Update all call sites in `tests/` to use atomic settlement logic.\n"
            "2. **HouseholdFactory** (`simulation/systems/demographic_manager.py`):\n"
            "   - Migrate to `simulation.factories.agent_factory` methodology.\n"
            "   - Inject `simulation` context where required.\n"
            "3. **StockOrder** (`simulation/models.py`):\n"
            "   - Remove class and enforce `CanonicalOrderDTO`.\n"
            "   - Update `tests/unit/test_market_adapter.py`.\n\n"
            "**Reference:** `design/3_work_artifacts/spec/DEPRECATION_CLEANUP_SPEC.md`"
        ),
        "file": "design/3_work_artifacts/spec/DEPRECATION_CLEANUP_SPEC.md",
        "wait": True
    },
}

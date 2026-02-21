"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."
   - [MANDATE]: DTO나 API가 변경되는 경우, 전수조사를 통해 모든 구현체에 변동을 반영한다.

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    # Wave 5: Data & Config Purity
    "wave5-dto-purity": {
        "title": "[Wave 5] Implement Canonical Order and UI DTOs",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave5_dto_purity_JULES_SPEC.md"
    },
    "wave5-config-purity": {
        "title": "[Wave 5] Implement Config Proxy for Runtime Binding",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave5_config_purity_JULES_SPEC.md"
    },
    
    # Wave 6: AI & Logic Refinement
    "wave6-ai-debt": {
        "title": "[Wave 6] Integrate Debt Constraints into AI Planning",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave6_ai_debt_JULES_SPEC.md"
    },
    "wave6-fiscal-masking": {
        "title": "[Wave 6] Implement Progressive Taxation and Wage Scaling",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave6_fiscal_masking_JULES_SPEC.md"
    },
    "test-stabilization": {
        "title": "[Stabilization] Protocol Alignment and Mock Restoration",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_test_stabilization_spec.md"
    },
    
    # Wave 7: Architecture & Ops Cleanup
    "wave7-firm-mutation": {
        "title": "[Wave 7] Enforce Stateless Engine Orchestration in Firm",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave7_firm_mutation_JULES_SPEC.md"
    },
    "wave7-dx-automation": {
        "title": "[Wave 7] Automate Mission Registration and Optimize Death System",
        "command": "create",
        "instruction": "Execute the full implementation spec exactly as documented.",
        "file": "artifacts/specs/MISSION_wave7_dx_automation_JULES_SPEC.md"
    }
}

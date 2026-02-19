"""
🤖 [ANTIGRAVITY] GEMINI MISSION MANIFEST GUIDE (Manual)
=====================================================

1. POSITION & ROLE
   - 역할: 로직 분석, 아키텍처 설계, MISSION_spec 작성, 코드 감사 및 보고서 생성 (No Coding).
   - 핵심 가치: "코드가 아닌 시스템의 지능과 정합성을 관리한다."

5. SMART CONTEXT (New Feature)
   - 매뉴얼(.md) 내에 링크된 아키텍처 가이드 문항들은 미션 실행 시 자동으로 'context_files'에 장착됩니다.
   - 명시적으로 모든 파일을 나열하지 않아도 시스템이 워커의 전문 지식을 위해 관련 표준을 찾아 전달합니다.

4. FIELD SCHEMA (GEMINI_MISSIONS)
   - title (str): 미션의 제목.
   - worker (str): 특정 작업 페르소나 선택 (필수).
     * [Reasoning]: 'spec', 'git', 'review', 'context', 'crystallizer'
     * [Analysis]: 'reporter', 'verify', 'audit'
   - instruction (str): 상세 지시 사항.
   - context_files (list[str]): 분석에 필요한 소스 코드 및 문서 경로 목록.
   - output_path (str, Optional): 결과물 저장 경로.
   - model (str, Optional): 모델 지정 ('gemini-3-pro-preview', 'gemini-3-flash-preview').
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "audit-mock-attribute-sync": {
        "title": "Systemic Audit: Mock Attribute Regressions (Cockpit 2.0)",
        "worker": "audit",
        "instruction": (
            "Scan the entire `tests/` directory to identify all Mock/MagicMock setups that use "
            "deprecated attribute names, specifically focusing on the recent Cockpit 2.0 refactor.\n\n"
            "**Target Mismatch:**\n"
            "- Old: `system_command_queue` (List-like)\n"
            "- New: `system_commands` (List[SystemCommand])\n\n"
            "**Objective:**\n"
            "1. Find every file in `tests/` where `system_command_queue` is assigned to a Mock or MagicMock.\n"
            "2. Identify if there are other stale attributes on `WorldState` mocks (e.g. `god_command_queue` vs naming in world_state.py).\n"
            "3. Provide a list of files and line numbers that need fixing.\n"
            "4. Check for `AttributeError: Mock object has no attribute...` patterns in recent failure logs if available."
        ),
        "context_files": [
            "simulation/world_state.py",
            "simulation/orchestration/tick_orchestrator.py",
            "tests/orchestration/test_state_synchronization.py",
            "tests/modules/governance/test_cockpit_flow.py",
            "tests/integration/test_tick_normalization.py",
            "tests/integration/test_cockpit_integration.py",
            "tests/integration/test_lifecycle_cycle.py"
        ],
        "output_path": "design/3_work_artifacts/reports/AUDIT_MOCK_REGRESSIONS.md"
    },
}

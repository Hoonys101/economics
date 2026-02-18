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
    "MISSION_TEST_MODERNIZATION_EXEC": {
        "title": "Execute Test Modernization & SSoT Fixes",
        "instruction": "Resolve the 17 identified test failures by formally registering 'escrow_agent' in WorldState and modernizing SettlementSystem tests to use a mocked IAgentRegistry. Resolve DeprecationWarnings for collect_tax.",
        "file": "C:\\Users\\Gram Pro\\.gemini\\antigravity\\brain\\3c6114c9-8ad4-4eaa-833d-49722a642486\\MISSION_TEST_MODERNIZATION_EXEC_IMG.md",
        "wait": True
    },
}

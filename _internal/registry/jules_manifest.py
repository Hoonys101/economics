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
   - session_id (str, Optional): '장착'된 미션의 세션 ID.
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "dto-api-repair": {
        "title": "DTO & API Repair: Float Leakage & God Factory",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MISSION_dto-api-repair_SPEC.md",
        "instruction": "Execute the DTO and API repair as specified in the MISSION_dto-api-repair_SPEC.md. Secure the 'Integer Pennies' standard in Config DTOs and enforce IFirmStateProvider protocol in FirmStateDTO."
    }
}

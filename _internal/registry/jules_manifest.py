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
    # Add missions here
    "fix-dto-integrity": {
        "title": "DTO 정합성 수정 (Float 제거 및 Purity 복구)",
        "command": "create",
        "instruction": """
첨부된 감사 보고서(MISSION_dto-audit_AUDIT.md)의 'Recommended Actions'를 수행하여 아키텍처 위반 사항을 수정하라.

1. **Int Migration (Pennies)**:
   - `simulation/dtos/api.py`의 `EconomicIndicatorData` 내 화폐 필드를 `Dict[CurrencyCode, float]` -> `Dict[CurrencyCode, int]`로 변경.
   - `department_dtos.py`의 `FinanceStateDTO`도 동일하게 변경.

2. **Restore Purity (Assembler Extraction)**:
   - `simulation/dtos/firm_state_dto.py`에 있는 `from_firm` 메서드의 로직을 제거하고 순수 데이터 클래스로 복구.
   - 해당 로직은 `simulation/assemblers/firm_assembler.py` (신규 생성)의 `FirmSnapshotAssembler`로 이동.

3. **Cleanup Dead Code**:
   - `modules/household/dtos.py`의 `HouseholdStateDTO` (Deprecated) 삭제.
""",
        "file": "design/3_work_artifacts/audits/MISSION_dto-audit_AUDIT.md",
        "context_files": [
            "simulation/dtos/api.py",
            "simulation/dtos/department_dtos.py",
            "simulation/dtos/firm_state_dto.py",
            "modules/household/dtos.py"
        ],
        "wait": False
    }
}

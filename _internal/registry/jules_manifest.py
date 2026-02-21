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
    "fix_penny_standard_tests": {
        "title": "Fix Penny Standard Migration Test Failures",
        "instruction": (
            "Fix the 5 failing tests caused by Penny Standard migration. "
            "1. C:/coding/economics/modules/government/components/infrastructure_manager.py:43 - Fix unpacking error (`issue_treasury_bonds_synchronous` returns bool, list). "
            "2. test_double_entry.py - test_market_bond_issuance_generates_transaction (20.0 -> 2000). "
            "3. test_double_entry.py - test_qe_bond_issuance_generates_transaction (10.0 -> 1000). "
            "4. test_sovereign_debt.py - test_issue_treasury_bonds_calls_settlement_system (1.0 -> 100). "
            "5. test_system.py - test_issue_treasury_bonds_market (1000.0 -> 100000). "
            "Verify with `pytest -rfE --tb=line --no-header tests/`."
        )
    }
}

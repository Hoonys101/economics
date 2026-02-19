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
    "exec-test-modernization": {
        "title": "Execute Test Modernization & Stabilization",
        "instruction": (
            "Align the test suite with Phase 19/20 architecture as per the modernization spec.\n\n"
            "**Core Tasks:**\n"
            "1. **Conftest**: Add `mock_household_factory_context` fixture to `tests/conftest.py`.\n"
            "2. **Audit Integrity**: Refactor `tests/system/test_audit_integrity.py` to use real `HouseholdFactory` + `mock_context` to verify birth gift transfers.\n"
            "3. **Mock IDs**: Ensure all mocks in `tests/unit/test_transaction_handlers.py` have explicit `id` attributes.\n"
            "4. **Factory Tests**: Update `tests/simulation/factories/test_agent_factory.py` to use `HouseholdFactoryContext`.\n"
            "5. **Engine Tests**: Update `tests/integration/test_government_refactor_behavior.py` to test `FiscalEngine` directly.\n"
            "6. **Government Tests**: Remove `collect_tax` calls in `tests/integration/test_government_fiscal_policy.py` and `tests/unit/test_tax_collection.py`, replacing them with `settlement_system.transfer` or service-level recording.\n\n"
            "**Verification**: The goal is 100% test pass rate for the affected files."
        ),
        "file": "design/3_work_artifacts/spec/TEST_MODERNIZATION_SPEC.md"
    },
    "exec-test-failure-fix": {
        "title": "Restore Test Suite: Fix 10 Failures in Fiscal/Demographics/Auth",
        "instruction": (
            "Restore the test suite to a Green State as per the specific instructions in the spec.\n\n"
            "**Key Instructions:**\n"
            "1. **Fiscal/Taxation**: Replace `collect_tax` assertions in `test_transaction_handlers.py`, `test_tax_collection.py`, and `test_government_fiscal_policy.py` with `record_revenue` and `settle_atomic`. Ensure all agent mocks have explicit `.id` attributes.\n"
            "2. **Demographics**: In `test_audit_integrity.py`, use a REAL `HouseholdFactory` with a mock `HouseholdFactoryContext` instead of mocking the factory class. Verify the birth gift transfer call.\n"
            "3. **Auth**: Update `test_websocket_auth.py` and `test_server_auth.py` to catch BOTH `InvalidStatus` and `InvalidMessage` from websockets, as library version v14+ behavior changed.\n\n"
            "**Constraint**: Do NOT modify simulation logic in `modules/`. Only modify files in `tests/` or create test-specific utilities."
        ),
        "file": "design/3_work_artifacts/spec/TEST_FAILURE_FIX_SPEC.md"
    },
}

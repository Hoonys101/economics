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
    "analyze-test-failures": {
        "title": "Comprehensive Test Failure Analysis: 10 Failures in 3 Categories",
        "worker": "spec",
        "instruction": (
            "Analyze all 10 test failures and produce a single, actionable specification for Jules.\n\n"
            "## Category A: Stale `collect_tax` References (6 failures)\n"
            "- `test_government_fiscal_policy.py::test_tax_collection_and_bailouts` calls `government.collect_tax(...)` which was removed.\n"
            "- `test_tax_collection.py::test_government_collect_tax_adapter_success` and `_failure` call the same removed method.\n"
            "- `test_transaction_handlers.py::TestLaborTransactionHandler` (2 tests) assert `government.collect_tax.assert_called_with(...)` but production `LaborTransactionHandler` now uses `settlement.settle_atomic()` + `government.record_revenue()`. The mock `government` also lacks an explicit `id` attribute (only set via `spec=ITaxCollector` which may not include `id`).\n\n"
            "**Fix Pattern**: Update test assertions to match the NEW production flow:\n"
            "  - `settle_atomic(debit_agent=..., credits_list=[...], tick=...)` for FIRM tax payer\n"
            "  - `transfer(buyer, seller, amount, memo)` + `settle_atomic(debit_agent=seller, credits_list=[(gov, tax, memo)], tick=...)` for HOUSEHOLD tax payer\n"
            "  - `government.record_revenue({...})` instead of `government.collect_tax(...)`\n"
            "  - Add `self.government.id = 99` explicitly in `TestLaborTransactionHandler.setUp`\n\n"
            "## Category B: Birth Gift Factory Wiring (1 failure)\n"
            "- `test_audit_integrity.py::test_birth_gift_rounding` — `DemographicManager.process_births()` calls `factory.create_newborn()` which calls `context.settlement_system.transfer()` with kwargs `sender=`, `receiver=`, `amount=`, `transaction_type=`, `tick=`. But the mock's `transfer` is never called because the test mock setup doesn't provide `HouseholdFactoryContext`. Fix: Provide a real `HouseholdFactory` with a mock context containing a mock `settlement_system`, then assert `settlement_system.transfer` was called.\n\n"
            "## Category C: WebSocket Auth Exception Mismatch (4 failures)\n"
            "- `test_websocket_auth.py` and `test_server_auth.py` expect `websockets.exceptions.InvalidStatus` but get `websockets.exceptions.InvalidMessage`. This is a `websockets` library version issue. The `_process_request` callback signature changed in v14+. Check if the server's `_process_request(self, connection, request)` signature matches the installed `websockets` version. If the server returns an HTTP response tuple but the library expects a different rejection mechanism, the client gets `InvalidMessage` instead of `InvalidStatus`.\n"
            "**Fix Pattern**: Either update `_process_request` to use `websockets.http.Response` or catch `InvalidMessage` in tests, or fix the server handler signature to match the installed version.\n\n"
            "## Constraints\n"
            "- Every refactored test must enforce Zero-Sum integer penny integrity.\n"
            "- All mocks implementing financial protocols MUST have explicit `id` attributes.\n"
            "- Production code in `labor.py`, `goods.py`, `server.py` MUST NOT be modified — only tests.\n"
        ),
        "context_files": [
            "simulation/agents/government.py",
            "simulation/factories/household_factory.py",
            "simulation/systems/settlement_system.py",
            "simulation/systems/demographic_manager.py",
            "modules/finance/transaction/handlers/labor.py",
            "modules/finance/transaction/handlers/protocols.py",
            "modules/system/server.py",
            "modules/system/security.py",
            "tests/integration/test_government_fiscal_policy.py",
            "tests/system/test_audit_integrity.py",
            "tests/unit/test_tax_collection.py",
            "tests/unit/test_transaction_handlers.py",
            "tests/security/test_websocket_auth.py",
            "tests/system/test_server_auth.py"
        ],
        "output_path": "design/3_work_artifacts/spec/TEST_FAILURE_FIX_SPEC.md"
    },
}


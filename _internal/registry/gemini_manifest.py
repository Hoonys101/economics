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
    "modernize-tests": {
        "title": "Test Modernization: Aligning with Phase 19/20 Architecture",
        "worker": "spec",
        "instruction": (
            "Analyze current test failures and deprecation warnings to design a modernization plan.\n\n"
            "**Primary Objectives:**\n"
            "1. **Taxation Fix**: Replace `government.collect_tax(...)` calls with `government.settlement_system.settle_atomic(...)` or proper service-based calls.\n"
            "2. **Birth Gift Fix**: Update `test_birth_gift_rounding` to assert against `settle_atomic` or `transfer` within the context of the new `HouseholdFactory`.\n"
            "3. **Mock Hardening**: Fix `AttributeError: Mock object has no attribute 'id'` by ensuring mocks in `test_transaction_handlers.py` correctly simulate `IAgent` or `IFinancialAgent` protocols.\n"
            "4. **Factory Migration**: Update `test_agent_factory.py` and others to use `simulation.factories.household_factory` and the mandatory `simulation` injection.\n"
            "5. **Engine Migration**: Replace `GovernmentDecisionEngine` with `FiscalEngine` in tests.\n\n"
            "**Constraint:** Every refactor must enforce Zero-Sum integrity and match the current `SettlementSystem` API."
        ),
        "context_files": [
            "simulation/agents/government.py",
            "simulation/factories/household_factory.py",
            "simulation/systems/settlement_system.py",
            "simulation/systems/demographic_manager.py",
            "tests/integration/test_government_fiscal_policy.py",
            "tests/system/test_audit_integrity.py",
            "tests/unit/test_tax_collection.py",
            "tests/unit/test_transaction_handlers.py",
            "tests/simulation/factories/test_agent_factory.py",
            "tests/integration/test_government_refactor_behavior.py"
        ],
        "output_path": "design/3_work_artifacts/spec/TEST_MODERNIZATION_SPEC.md"
    },
}

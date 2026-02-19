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
    "spec-comprehensive-liquidation-plan": {
        "title": "SPEC: Comprehensive Post-Wave Liquidation Plan",
        "worker": "spec",
        "instruction": "Analyze all remaining items in TECH_DEBT_LEDGER.md after the current transition (Wave 1 & 2). Create a multi-wave liquidation plan for the next phase. Group tasks that modify the same files (e.g., config, testing, finance) to avoid merge conflicts. Optimize for parallel execution by Gemini (specs) and Jules (code). Output a structured markdown plan.",
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "design/2_operations/ledgers/TECH_DEBT_HISTORY.md",
            "PROJECT_STATUS.md"
        ],
        "output_path": "design/4_hard_planning/FUTURE_LIQUIDATION_ROADMAP.md"
    },
    "spec-lifecycle-init-fix": {
        "title": "SPEC: Lifecycle Manager Initialization & Cycle Fix",
        "worker": "spec",
        "instruction": "Analyze the 'ValueError: IHouseholdFactory is mandatory' failure in AgentLifecycleManager. Investigate potential import cycles between AgentLifecycleManager, HouseholdFactory, and BirthSystem. Propose a fix that allows clean initialization for both production and test environments (mocks). Also address the DeprecationWarnings related to Government.collect_tax and HouseholdFactory locations.",
        "context_files": [
            "simulation/systems/lifecycle_manager.py",
            "simulation/systems/lifecycle/birth_system.py",
            "simulation/factories/household_factory.py",
            "modules/household/api.py",
            "simulation/systems/api.py",
            "tests/unit/test_lifecycle_reset.py",
            "tests/integration/test_wo167_grace_protocol.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_LIFECYCLE_INIT_FIX_SPEC.md"
    },
    "spec-test-modernization-audit": {
        "title": "SPEC: Full-Suite Test Modernization Audit",
        "worker": "audit",
        "instruction": "Conduct a comprehensive audit of the entire test suite (tests/). Identify: 1) Unit mismatches (asserting USD float vs Penny int). 2) Stale mocks that don't satisfy updated protocols (e.g., missing mandatory dependencies, outdated DTO attributes). 3) Direct agent attribute access (SSoT violations). Group findings by module and prioritize by failure impact. Generate a modernization spec for Jules. Use the provided failure logs as a starting point.",
        "context_files": [
            "design/1_governance/architecture/standards/TESTING_STABILITY.md",
            "design/1_governance/architecture/ARCH_TRANSACTIONS.md",
            "design/3_work_artifacts/reports/current_test_failures.md",
            "simulation/models.py",
            "simulation/systems/api.py",
            "tests/unit/test_transaction_processor.py",
            "tests/modules/finance/transaction/test_processor.py",
            "tests/unit/markets/test_housing_transaction_handler.py",
            "tests/unit/test_lifecycle_reset.py",
            "tests/integration/test_wo167_grace_protocol.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_TEST_MODERNIZATION_AUDIT_SPEC.md"
    }
}

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
    "fix-dto-naming-alignment": {
        "title": "Align SimulationState DTO Naming",
        "worker": "spec",
        "instruction": "Align SimulationState DTO naming with WorldState as per MISSION_PHASE23_HYGIENE_SPEC.md. Specifically rename government and god_commands to avoid singleton/deque mismatches.",
        "context_files": [
            "c:/coding/economics/simulation/dtos/api.py",
            "c:/coding/economics/simulation/world_state.py",
            "c:/coding/economics/simulation/orchestration/tick_orchestrator.py",
            "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_PHASE23_HYGIENE_SPEC.md"
        ]
    },
    "modernize-test-and-legacy-api": {
        "title": "Modernize Test & Legacy API",
        "worker": "spec",
        "instruction": "Modernize tests and resolve legacy module/API imports as per MISSION_PHASE23_HYGIENE_SPEC.md. Replace HouseholdFactory, collect_tax, and _handle_agent_liquidation with modern counterparts.",
        "context_files": [
            "c:/coding/economics/tests/system/test_engine.py",
            "c:/coding/economics/tests/integration/test_tick_normalization.py",
            "c:/coding/economics/tests/orchestration/test_state_synchronization.py",
            "c:/coding/economics/scripts/audit_zero_sum.py",
            "c:/coding/economics/simulation/systems/demographic_manager.py",
            "c:/coding/economics/simulation/initialization/initializer.py",
            "c:/coding/economics/simulation/systems/tax_agency.py",
            "c:/coding/economics/simulation/systems/api.py",
            "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_PHASE23_HYGIENE_SPEC.md"
        ]
    },
    "phase23-fix-household-integration-test": {
        "title": "Analyze & Fix Household Integration Test",
        "worker": "spec",
        "instruction": "Analyze the failing integration test in test_household_integration_new.py. The test is currently skipped because BudgetEngine/ConsumptionEngine interaction results in empty orders. Determine if this is a test setup issue (missing initial assets/config) or a logic flaw in engine synchronization, and write a MISSION_spec for the fix.",
        "context_files": [
            "c:/coding/economics/tests/unit/decisions/test_household_integration_new.py",
            "c:/coding/economics/simulation/core_agents.py",
            "c:/coding/economics/modules/household/engines/budget.py",
            "c:/coding/economics/modules/household/engines/consumption_engine.py",
            "c:/coding/economics/modules/household/api.py"
        ]
    },
    "phase23-forensic-debt-audit": {
        "title": "Phase 23 Forensic Debt Audit",
        "worker": "audit",
        "instruction": "Analyze the provided diagnostic logs and AUTOPSY_REPORT for any recurring errors, architectural drifts (e.g., God-class behavior, DTO violations), or patterns of failure. identify technical debt candidates and output an Insight Report.",
        "context_files": [
            "reports/AUTOPSY_REPORT.md",
            "logs/full_log.txt",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "design/1_governance/architecture/ARCH_AGENTS.md"
        ]
    }
}

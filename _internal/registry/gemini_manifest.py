"""
🤖 [ANTIGRAVITY] GEMINI MISSION MANIFEST GUIDE (Manual)
=====================================================

1. POSITION & ROLE
   - 역할: 로직 분석, 아키텍처 설계, MISSION_spec 작성, 코드 감사 및 보고서 생성 (No Coding).
   - 핵심 가치: "코드가 아닌 시스템의 지능과 정합성을 관리한다."

5. SMART CONTEXT (New Feature)
   - 매뉴얼(.md) 내에 링크된 아키텍처 가이드 문항들은 미션 실행 시 자동으로 'context_files'에 장착됩니다.
   - 명시적으로 모든 파일을 나열하지 않아도 시스템이 워커의 전문 지식을 위해 관련 표준을 찾아 전달합니다.
   - **MANDATORY**: DAO/DTO의 스키마 변경 시, 해당 DTO/DAO를 참조하는 모든 구현체(Call Sites)를 찾아 `context_files`에 포함하십시오.

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
    "lane1-finance-audit": {
        "title": "Lane 1 Audit: Finance & M2 Logic",
        "worker": "audit",
        "instruction": """
Perform a deep audit of the financial engine and money supply logic.
1. Trace the `MONEY_SUPPLY_CHECK` failure from diagnostic logs back to `world_state.py`.
2. Review `MatchingEngine` for residual float precision issues.
3. Propose a hardened `IFinancialEntity` protocol that prevents negative M2 values.
""",
        "context_files": [
            "reports/diagnostic_refined.md",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "modules/finance/engine.py",
            "simulation/world_state.py",
            "modules/finance/api.py",
            "simulation/systems/settlement_system.py"
        ],
        "output_path": "design/3_work_artifacts/audits/MISSION_lane1-finance-audit_REPORT.md"
    },
    "lane2-structural-audit": {
        "title": "Lane 2 Audit: Structural Lifecycle & Sagas",
        "worker": "audit",
        "instruction": """
Audit the agent lifecycle and Saga orchestration logic.
1. Identify the race condition in `firm_management.py` that causes capital transfers to fail for newly spawned firms.
2. Review the DTO mismatch for `HousingTransactionSagaStateDTO` across modules.
3. Propose an atomic agent registration-before-injection sequence.
""",
        "context_files": [
            "reports/diagnostic_refined.md",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "simulation/systems/firm_management.py",
            "modules/finance/sagas/orchestrator.py",
            "modules/finance/sagas/housing_api.py",
            "simulation/orchestration/tick_orchestrator.py"
        ],
        "output_path": "design/3_work_artifacts/audits/MISSION_lane2-structural-audit_REPORT.md"
    },
    "lane3-dx-audit": {
        "title": "Lane 3 Audit: DX & Test Stabilization",
        "worker": "audit",
        "instruction": """
Audit the test suite and orchestrator resilience.
1. Review `TickOrchestrator` for fragile DTO attribute access that leads to runtime crashes when attributes are missing.
2. Audit the transaction mock strategy in the test suite to ensure alignment with the production `IFinancialAgent` protocols.
3. Propose a plan to modernize deprecated tax collection calls in legacy tests.
""",
        "context_files": [
            "reports/diagnostic_refined.md",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "simulation/dtos/api.py",
            "simulation/orchestration/phases_recovery.py",
            "tests/test_settlement_system.py"
        ],
        "output_path": "design/3_work_artifacts/audits/MISSION_lane3-dx-audit_REPORT.md"
    },
    "lane1-finance-spec": {
        "title": "Lane 1 Spec: Monetary & Precision Hardening",
        "worker": "spec",
        "instruction": """
Create a detailed MISSION_SPEC for Lane 1 based on the Lane 1 Audit Report.
1. Define the exact refactor for `WorldState.calculate_total_money()`.
2. Specify the `IFinancialEntity` protocol changes in `modules/finance/api.py`.
3. Ensure all M2 check logic is synchronized with the new asset/liability split.
4. Provide a step-by-step implementation roadmap for Jules.
""",
        "context_files": [
            "design/3_work_artifacts/audits/MISSION_lane1-finance-audit_REPORT.md",
            "simulation/world_state.py",
            "modules/finance/api.py",
            "modules/finance/engine.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_lane1-finance_JULES_SPEC.md"
    },
    "lane2-structural-spec": {
        "title": "Lane 2 Spec: Lifecycle & Saga Unification",
        "worker": "spec",
        "instruction": """
Create a detailed MISSION_SPEC for Lane 2 based on the Lane 2 Audit Report.
1. Define the atomic `register_agent()` and `onboard_agent()` protocols.
2. Specify the code reordering in `firm_management.py` to ensure registration happens before funding.
3. Provide a unified `HousingTransactionSagaStateDTO` schema that resolves participant ID desync.
4. Outline the exact implementation steps for Jules.
""",
        "context_files": [
            "design/3_work_artifacts/audits/MISSION_lane2-structural-audit_REPORT.md",
            "simulation/systems/firm_management.py",
            "modules/finance/sagas/orchestrator.py",
            "modules/finance/sagas/housing_api.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_lane2-structural_JULES_SPEC.md"
    },
    "lane3-dx-spec": {
        "title": "Lane 3 Spec: Orchestrator & Test Recovery",
        "worker": "spec",
        "instruction": """
Create a detailed MISSION_SPEC for Lane 3 based on the Lane 3 Audit Report.
1. Specify the hardening of `TickOrchestrator` to handle missing DTO attributes via `getattr`.
2. Provide the refactor plan for `test_phase_housing_saga.py` to use dataclass DTOs.
3. Outline the steps to modernize legacy tax collection tests in `test_tax_agency.py`.
4. Ensure all transaction mocks in the test suite align with `IFinancialAgent` protocols.
""",
        "context_files": [
            "design/3_work_artifacts/audits/MISSION_lane3-dx-audit_REPORT.md",
            "simulation/orchestration/tick_orchestrator.py",
            "tests/test_settlement_system.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_lane3-dx_JULES_SPEC.md"
    }
}

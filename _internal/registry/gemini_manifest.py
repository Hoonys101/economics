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
    # --- MODULE A: FINANCE & ACCOUNTING ---
    "mod-finance-audit": {
        "title": "Module A Audit: Finance & Accounting Deep-Dive",
        "worker": "audit",
        "instruction": """
Perform a deep audit of Finance/Accounting modules (settlement_system.py, engine.py, accounting.py).
Focus on: TD-CRIT-FLOAT-CORE, TD-ECON-M2-INV, TD-SYS-ACCOUNTING-GAP.

REPORT STRUCTURE:
1. Root Cause: Identify exactly why floats or incorrect logic persist.
2. Solution: Define the integer conversion and reciprocal accounting rules.
3. Pseudo Code & Structural Proposal: Provide the specific DTO/API changes needed.
""",
        "context_files": ["simulation/systems/settlement_system.py", "modules/finance/engine.py", "simulation/systems/accounting.py", "simulation/dtos/api.py", "modules/finance/api.py"],
        "output_path": "design/3_work_artifacts/audits/MOD_FINANCE_AUDIT.md"
    },

    # --- MODULE B: ARCHITECTURE & ORCHESTRATION ---
    "mod-arch-audit": {
        "title": "Module B Audit: Architecture & Orchestration Resilience",
        "worker": "audit",
        "instruction": """
Audit Architecture/Orchestration modules (world_state.py, tick_orchestrator.py, firm.py).
Focus on: TD-ARCH-GOV-MISMATCH, TD-ARCH-ORCH-HARD, TD-ARCH-FIRM-COUP.

REPORT STRUCTURE:
1. Root Cause: Explain the singleton mismatch and fragile attribute access triggers.
2. Solution: Define the singleton enforcement and defensive access layer.
3. Pseudo Code & Structural Proposal: Provide the IWorldState/IOrchestrator interface updates.
""",
        "context_files": ["simulation/world_state.py", "simulation/orchestration/tick_orchestrator.py", "simulation/models/firm.py", "simulation/dtos/api.py"],
        "output_path": "design/3_work_artifacts/audits/MOD_ARCH_AUDIT.md"
    },

    # --- MODULE C: LIFECYCLE & SAGAS ---
    "mod-lifecycle-audit": {
        "title": "Module C Audit: Lifecycle & Saga Reliability",
        "worker": "audit",
        "instruction": """
Audit Lifecycle/Saga logic (firm_management.py, sagas/orchestrator.py, bank.py).
Focus on: TD-ARCH-STARTUP-RACE, TD-FIN-SAGA-ORPHAN, TD-INT-BANK-ROLLBACK.

REPORT STRUCTURE:
1. Root Cause: Trace the race condition and Saga ID desync.
2. Solution: Define the atomic onboarding protocol and DTO normalization.
3. Pseudo Code & Structural Proposal: Provide the step-by-step lifecycle code reordering.
""",
        "context_files": ["simulation/systems/firm_management.py", "modules/finance/sagas/orchestrator.py", "simulation/systems/bank.py", "simulation/dtos/api.py"],
        "output_path": "design/3_work_artifacts/audits/MOD_LIFECYCLE_AUDIT.md"
    },

    # --- MODULE D: TEST INFRASTRUCTURE ---
    "mod-test-audit": {
        "title": "Module D Audit: Test Suite Modernization",
        "worker": "audit",
        "instruction": """
Audit Test Infrastructure (tests/unit, simulation/dtos/api.py).
Focus on: TD-TEST-TX-MOCK-LAG, TD-TEST-TAX-DEPR, TD-TEST-COCKPIT-MOCK, TD-TEST-LIFE-STALE.

REPORT STRUCTURE:
1. Root Cause: Identify why mocks drifted from production protocols.
2. Solution: Define the Mock Factory and Assertion modernization strategy.
3. Pseudo Code & Structural Proposal: Provide examples of the new contract-based assertions.
""",
        "context_files": ["tests/unit/test_transaction_engine.py", "tests/unit/test_engine.py", "simulation/dtos/api.py"],
        "output_path": "design/3_work_artifacts/audits/MOD_TEST_AUDIT.md"
    },

    # --- SPECIFICATION PHASE (CONTRACT-FIRST) ---
    "mod-finance-spec": {
        "title": "Module A Spec: Finance & DTO Hardening",
        "worker": "spec",
        "instruction": """
Based on MOD_FINANCE_AUDIT.md, draft a MISSION_SPEC for Jules:
1. [DTO/API] Define exact integer-only signatures for IFinancialAgent and Loan/Debt DTOs.
2. [CORE] Define the M2 calculation logic (floored liquidity + liability tracking).
3. [LOGIC] Specify reciprocal expense logging for accounting.py.
""",
        "context_files": ["design/3_work_artifacts/audits/MOD_FINANCE_AUDIT.md", "simulation/dtos/api.py", "modules/finance/api.py"],
        "output_path": "design/3_work_artifacts/specs/MOD_FINANCE_SPEC.md"
    },
    "mod-arch-spec": {
        "title": "Module B Spec: Architecture & Orchestration Resilience",
        "worker": "spec",
        "instruction": """
Based on MOD_ARCH_AUDIT.md, draft a MISSION_SPEC for Jules:
1. [DTO/API] Define IWorldState protocol and decorate SimulationState as a strict dataclass.
2. [CORE] Implement IGovernmentRegistry logic for singleton/list synchronization.
3. [STRUCT] Specify the transition to DepartmentContextDTO for Firm decoupling.
""",
        "context_files": ["design/3_work_artifacts/audits/MOD_ARCH_AUDIT.md", "simulation/dtos/api.py", "simulation/world_state.py"],
        "output_path": "design/3_work_artifacts/specs/MOD_ARCH_SPEC.md"
    },
    "mod-lifecycle-spec": {
        "title": "Module C Spec: Lifecycle & Saga Reliability",
        "worker": "spec",
        "instruction": """
Based on MOD_LIFECYCLE_AUDIT.md, draft a MISSION_SPEC for Jules:
1. [DTO/API] Define IAgentRegistration protocol and unified SagaParticipantDTO schema.
2. [CORE] Define the atomic onboarding protocol (Instantiate -> Register -> Fund).
3. [STRUCT] Remove hasattr dependencies in bank rollback via strict interfaces.
""",
        "context_files": ["design/3_work_artifacts/audits/MOD_LIFECYCLE_AUDIT.md", "simulation/dtos/api.py", "simulation/systems/firm_management.py"],
        "output_path": "design/3_work_artifacts/specs/MOD_LIFECYCLE_SPEC.md"
    },
    "mod-test-spec": {
        "title": "Module D Spec: Test Suite Modernization",
        "worker": "spec",
        "instruction": """
Based on MOD_TEST_AUDIT.md, draft a MISSION_SPEC for Jules:
1. [CORE] Define a unified MockFactory protocol to sync mocks with production DTOs.
2. [TESTS] Specify the migration of legacy tax and liquidation tests to current APIs.
3. [VERIFY] Sync all test verification logic with the new Module A/B/C contracts.
""",
        "context_files": ["design/3_work_artifacts/audits/MOD_TEST_AUDIT.md", "simulation/dtos/api.py", "tests/unit/test_transaction_engine.py"],
        "output_path": "design/3_work_artifacts/specs/MOD_TEST_SPEC.md"
    }
}

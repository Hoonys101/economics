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
    "phase23-spec-safety-net": {
        "title": "P1 Mission Spec: Operation Safety Net",
        "worker": "spec",
        "instruction": """Create a MISSION_spec.md for Jules to restore test suite integrity. 
Focus on:
1. Aligning Transaction Mocks (tests/mocks/) with ITransactionParticipant.
2. Updating Lifecycle tests (test_engine.py) for Phase_Bankruptcy sequencing.
3. Patching Cockpit mocks to use CockpitOrchestrator.

Refer to 'Mission 1.1' and '1.2' in the Roadmap.""",
        "context_files": [
            "design/3_work_artifacts/specs/PHASE23_LIQUIDATION_ROADMAP.md",
            "tests/mocks/agent_mocks.py",
            "tests/system/test_engine.py",
            "simulation/orchestration/tick_orchestrator.py"
        ]
    },
    "phase23-spec-penny-perfect": {
        "title": "P2 Mission Spec: Operation Penny Perfect",
        "worker": "spec",
        "instruction": """Create a MISSION_spec.md for Jules to enforce the Penny Standard.
Focus on:
1. Converting SettlementSystem state and matching logic to absolute 'int' pennies.
2. Registering 'bailout' and 'bond_issuance' handlers in TransactionProcessor.
3. Eliminating 'hasattr' logic leaks in BankTransactionHandler.

Refer to 'Mission 2.1' and '2.2' in the Roadmap.""",
        "context_files": [
            "design/3_work_artifacts/specs/PHASE23_LIQUIDATION_ROADMAP.md",
            "simulation/systems/settlement_system.py",
            "simulation/systems/transaction_processor.py",
            "simulation/systems/handlers/monetary_handler.py"
        ]
    },
    "phase23-spec-surgical-separation": {
        "title": "P3 Mission Spec: Operation Surgical Separation",
        "worker": "spec",
        "instruction": """Create a MISSION_spec.md for Jules to decouple Firm departments.
Focus on:
1. Extracting HR/Finance logic into stateless engines.
2. Removing 'self.parent' references in departments.
3. Standardizing WorldState.government as a singleton.

Refer to 'Mission 3.1' and '3.2' in the Roadmap.""",
        "context_files": [
            "design/3_work_artifacts/specs/PHASE23_LIQUIDATION_ROADMAP.md",
            "simulation/core_agents.py",
            "simulation/decisions/firm/hr_department.py",
            "simulation/world_state.py"
        ]
    }
}

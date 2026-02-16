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
    "firm-household-decomp-spec": {
        "title": "God Class Decomposition: Firm & Household",
        "worker": "spec",
        "instruction": "Firm(1200+줄)과 Household(1000+줄) 거대 클래스를 추가 분해하여 Stateless Orchestrator 패턴을 완성하십시오. 로직은 이미 엔진으로 분리되었으나, 클래스 자체가 여전히 비대합니다. 병렬 실행 가능성을 분석하여 Firm과 Household 작업을 독립적으로 수행할 수 있는 설계를 제안하십시오.",
        "context_files": [
            "simulation/firms.py",
            "simulation/core_agents.py",
            "PROJECT_STATUS.md",
            "design/4_hard_planning/PARALLEL_CLEARANCE_STRATEGY.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_agent-decomposition_SPEC.md"
    },
    "test-unit-standardization-spec": {
        "title": "Test Unit Scale Standardization (Dollar -> Penny)",
        "worker": "spec",
        "instruction": "테스트 코드 전반의 'Dollar'(float) 단위를 'Penny'(int)로 표준화하십시오. Naming convention(`amount_pennies`)이나 helper function 도입을 포함한 전환 스펙을 작성하십시오. Agent 분해 작업과 병렬 진행 시의 충돌 위험을 평가하십시오.",
        "context_files": [
            "tests/unit/test_firms.py",
            "tests/integration/test_fiscal_integrity.py",
            "modules/finance/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_test-unit-scale_SPEC.md"
    },
    "mock-drift-automation-spec": {
        "title": "Mock Drift Automation & Protocol Enforcement",
        "worker": "spec",
        "instruction": "Protocol 변경 시 Mock이 자동으로 동기화되거나 정지(Fail)되도록 하는 자동화 체계를 설계하십시오. `create_autospec` 활용 또는 MockRegistry 도입 방안을 포함하십시오.",
        "context_files": [
            "modules/common/protocol.py",
            "modules/finance/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_mock-automation_SPEC.md"
    }
}

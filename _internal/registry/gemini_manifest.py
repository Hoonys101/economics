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
    "fix-dto-subscripting": {
        "title": "Finance & Credit Purity Fix",
        "worker": "spec",
        "instruction": "Design the specific patches to fix DTO subscripting issues in Bank and Credit Scoring modules based on MISSION_fix-dto-subscripting_SPEC.md.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_fix-dto-subscripting_SPEC.md",
            "simulation/bank.py",
            "modules/finance/credit_scoring.py",
            "simulation/loan_market.py",
            "tests/unit/finance/test_bank_service_interface.py"
        ],
        "model": "gemini-3-pro-preview"
    },
    "fix-firm-engine-logic": {
        "title": "Firm Structure & Engine Repair",
        "worker": "spec",
        "instruction": "Analyze Firm agent decomposition and fix engine-level unit/type mismatches according to MISSION_fix-firm-struct-and-engines_SPEC.md.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_fix-firm-struct-and-engines_SPEC.md",
            "simulation/firms.py",
            "simulation/decisions/ai_driven_firm_engine.py",
            "tests/simulation/components/engines/test_asset_management_engine.py"
        ],
        "model": "gemini-3-pro-preview"
    },
    "fix-system-integrity": {
        "title": "Registry & System Integrity Fix",
        "worker": "reporter",
        "instruction": "Investigate M2 leak (-100 mismatch) and Registry LOCK_PATH error as specified in MISSION_fix-system-integrity_SPEC.md.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_fix-system-integrity_SPEC.md",
            "_internal/registry/service.py",
            "modules/government/components/monetary_ledger.py",
            "tests/integration/test_m2_integrity.py"
        ],
        "model": "gemini-3-pro-preview"
    },
    "fix-behavioral-scenarios": {
        "title": "Scenario & AI Behavior Alignment",
        "worker": "audit",
        "instruction": "Audit the breeding and survival override logic failures and propose calibration fixes per MISSION_fix-behavioral-scenarios_SPEC.md.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_fix-behavioral-scenarios_SPEC.md",
            "tests/integration/test_wo048_breeding.py",
            "tests/unit/decisions/test_animal_spirits_phase2.py",
            "simulation/ai/household_ai.py"
        ],
        "model": "gemini-3-pro-preview"
    }
}

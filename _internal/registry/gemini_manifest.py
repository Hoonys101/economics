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
   - output_path (str, Optional): 결과물 저장 경로 (예: gemini-output/spec/MISSION_name_SPEC.md).
   - model (str, Optional): 모델 지정 ('gemini-3-pro-preview', 'gemini-3-flash-preview').
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "forensics_escheatment_analysis": {
        "title": "[Forensics] Escheatment Handler NoneType Analysis",
        "worker": "audit",
        "instruction": "Analyze the 'NoneType' error in EscheatmentHandler. Identify why tx.metadata might be None and propose a hardening fix that ensures zero-sum integrity during agent liquidation.",
        "context_files": [
            "simulation/systems/handlers/escheatment_handler.py",
            "simulation/systems/transaction_processor.py",
            "reports/diagnostic_refined.md"
        ],
        "output_path": "gemini-output/spec/MISSION_escheatment_fix_SPEC.md"
    },
    "forensics_account_registry_analysis": {
        "title": "[Forensics] Missing Account 100 Analysis",
        "worker": "audit",
        "instruction": "Investigate the 'Destination account does not exist: 100' errors in the forensics report. Determine if this is an initialization race condition or a hardcoded ID mismatch in stress tests. Propose a registry hardening plan.",
        "context_files": [
            "simulation/systems/settlement_system.py",
            "simulation/initialization/initializer.py",
            "modules/system/constants.py",
            "reports/diagnostic_refined.md"
        ],
        "output_path": "gemini-output/spec/MISSION_account_registry_fix_SPEC.md"
    },
    "forensics_saga_integrity_analysis": {
        "title": "[Forensics] Saga Participant Integrity Analysis",
        "worker": "audit",
        "instruction": "Analyze the 'SAGA_SKIP' warnings due to missing participant IDs. Audit the SagaOrchestrator and HousingSaga logic to ensure all transition states capture the required agent IDs correctly.",
        "context_files": [
            "modules/finance/sagas/orchestrator.py",
            "simulation/orchestration/phases/housing_saga.py",
            "reports/diagnostic_refined.md"
        ],
        "output_path": "gemini-output/spec/MISSION_saga_integrity_fix_SPEC.md"
    }
}


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
    "spec_firm_decoupling": {
        "title": "TD-ARCH-FIRM-COUP: Firm Decoupling Spec",
        "worker": "spec",
        "instruction": "Analyze Firm-Department coupling (self.parent) and design Orchestrator-based messaging pattern. Write specification to output_path.",
        "context_files": [
            "c:/coding/economics/simulation/agents/firm.py",
            "c:/coding/economics/simulation/orchestration/tick_orchestrator.py"
        ],
        "output_path": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_td_firm_coup_spec.md"
    },
    "spec_missing_tx_handlers": {
        "title": "TD-RUNTIME-TX-HANDLER: Missing Tx Handlers Spec",
        "worker": "spec",
        "instruction": "Design missing transaction handlers (bailout, bond_issuance) and their registration in the TransactionEngine. Write specification to output_path.",
        "context_files": [
            "c:/coding/economics/modules/transaction/engine.py"
        ],
        "output_path": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_td_tx_handlers_spec.md"
    },
    "spec_cockpit_test_regression": {
        "title": "TD-TEST-COCKPIT-MOCK: Cockpit Regression Fix Spec",
        "worker": "spec",
        "instruction": "Analyze test failures related to deprecated system_command_queue in Cockpit 2.0 tests. Write spec to modernize test mocks.",
        "context_files": [
            "c:/coding/economics/tests/unit/modules/command/test_service.py"
        ],
        "output_path": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_td_cockpit_mock_spec.md"
    },
    "spec_stale_lifecycle_tests": {
        "title": "TD-TEST-LIFE-STALE: Stale Lifecycle Tests Spec",
        "worker": "spec",
        "instruction": "Analyze and specify fixes for stale lifecycle test logic calling refactored liquidation methods.",
        "context_files": [
            "c:/coding/economics/tests/unit/simulation/test_engine.py"
        ],
        "output_path": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_td_life_stale_spec.md"
    }
}

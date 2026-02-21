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
    "analyze_13_failures": {
        "title": "Analyze 13 Test Failures and Draft Remediation Spec",
        "worker": "audit",
        "instruction": "분석 대상: artifacts/recent_13_test_failures.txt에 나열된 13개의 테스트 실패. \n작업: 실패를 모듈/원인별로 그룹화하고, 각 그룹에 대해 반드시 다음 구조로 문서를 작성하시오:\n1. 원인 파악 (Root Cause) \n2. 해결방안 (Solution) \n3. 구체적인 spec (Detailed Spec).\n\n특이사항: 'MagicMock'과 'int'의 비교 에러 및 'get_financial_snapshot' 속성 누락 등 Mock 객체 관련 에러에 주목하여 기존 DTO/SSoT 마이그레이션과의 연관성을 파악하시오.",
        "context_files": [
            "artifacts/recent_13_test_failures.txt",
            "tests/integration/test_liquidation_waterfall.py",
            "tests/unit/systems/test_liquidation_manager.py",
            "tests/system/test_phase29_depression.py",
            "tests/integration/scenarios/diagnosis/test_agent_decision.py",
            "tests/test_firm_surgical_separation.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_13_failures_analysis_spec.md"
    }
}

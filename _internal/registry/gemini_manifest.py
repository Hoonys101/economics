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
    "spec-matching-engine-int-math": {
        "title": "SPEC: MatchingEngine Integer Math Hardening",
        "worker": "spec",
        "instruction": "Refactor the MatchingEngine math to use integer pennies exclusively. Define rounding rules (Round-Down/Floor) for mid-price discovery to eliminate M2 drift. Ensure execution prices and total values are calculated as integers.",
        "context_files": [
            "simulation/markets/matching_engine.py",
            "simulation/dtos/api.py",
            "modules/system/api.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_MATCH_ENGINE_INT_SPEC.md"
    },
    "spec-dto-reporting-pennies": {
        "title": "SPEC: Reporting DTO Penny Hardening",
        "worker": "spec",
        "instruction": "Analyze all DTOs in simulation/dtos/api.py. Identify any fields currently using float for monetary values (assets, price, wealth, indicators) and refactor them to integer pennies (int). Ensure backward compatibility with existing serialization logic where possible.",
        "context_files": [
            "simulation/dtos/api.py",
            "modules/simulation/dtos/api.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_REPORTING_DTO_INT_SPEC.md"
    }
}

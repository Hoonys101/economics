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
    "MISSION_harvest_optimizer_SPEC": {
        "title": "Harvest Algorithm Optimization Spec",
        "worker": "spec",
        "instruction": "weighted_harvester.py의 성능 병목 지점(과도한 git subprocess 호출, 특히 파일별 git log 호출 및 순차 처리)을 분석하고, 이를 최적화하기 위한 기술 사양서(SPEC)를 작성하십시오. ls-tree와 한 번의 git log (branch level) 호출로 필요한 정보를 일괄 추출하는 방식이나, 병렬 처리를 통해 수확 속도를 10배 이상 향상시키는 방안을 제시하십시오.",
        "context_files": [
            "_internal/scripts/weighted_harvester.py",
            "_internal/scripts/launcher.py",
            "harvest-go.bat"
        ],
        "output_path": "gemini-output/spec/MISSION_harvest_optimizer_SPEC.md"
    }
}

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
    "phase41_bank_registry_planning": {
        "title": "Wave 2: BankRegistry API/DTO Freeze",
        "worker": "spec",
        "instruction": "Define the IBankRegistry protocol and update ISettlementSystem to include it. Focus strictly on freezing the interface and DTOs to enable parallel implementation. Ensure backward compatibility.",
        "context_files": [
            "modules/finance/api.py",
            "simulation/systems/settlement_system.py",
            "simulation/bank.py"
        ],
        "output_path": "gemini-output/spec/MISSION_bank_registry_FREEZE.md"
    },
    "phase41_labor_config_planning": {
        "title": "Wave 2: Labor Config API/DTO Freeze",
        "worker": "spec",
        "instruction": "Define LaborConfigDTO and specify how MAJORS will be loaded from economy_params.yaml. Freeze the interface between constants.py and the config system.",
        "context_files": [
            "modules/labor/api.py",
            "modules/labor/constants.py",
            "config/economy_params.yaml"
        ],
        "output_path": "gemini-output/spec/MISSION_labor_config_FREEZE.md"
    },
    "phase41_labor_metadata_planning": {
        "title": "Wave 2: Labor Metadata DTO Migration Planning",
        "worker": "spec",
        "instruction": "Design LaborMatchDTO to replace Order.metadata/brand_info usage in LaborMarket. Specify the changes needed in LaborMarket.place_order and the overall matching engine.",
        "context_files": [
            "modules/labor/api.py",
            "modules/labor/system.py",
            "modules/market/api.py"
        ],
        "output_path": "gemini-output/spec/MISSION_labor_metadata_SPEC.md"
    },
    "phase41_test_dto_hygiene_planning": {
        "title": "Wave 2: DTO Test Hygiene Planning",
        "worker": "spec",
        "instruction": "Analyze tests using MagicMock for DTOs (e.g., test_firm_brain_scan.py). Propose a plan to use concrete DTOs or strictly spec'd mocks to improve test stability and detect schema drifts.",
        "context_files": [
            "modules/finance/api.py",
            "modules/firm/api.py",
            "tests/unit/test_firm_brain_scan.py"
        ],
        "output_path": "gemini-output/spec/MISSION_test_dto_hygiene_SPEC.md"
    }
}

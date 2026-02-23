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
    },
    "MISSION_tech_debt_clearance_spec": {
        "title": "Technical Debt Liquidation & API/DTO Realignment Plan",
        "worker": "spec",
        "instruction": "기술부채 장부(TECH_DEBT_LEDGER.md)와 진단 보고서(diagnostic_refined.md)를 분석하여 모듈간 결합도를 낮추고 데이터 정합성을 확보하기 위한 전면적인 청산 계획을 수립하십시오. 특히 M2 반전(TD-ECON-M2-REGRESSION)과 초기화 순서(TD-FIN-INVISIBLE-HAND)를 최우선으로 다루며, 모든 모듈의 DTO/API 표준화 방안을 포함한 'Wave' 기반의 구현 전략(SPEC)을 생성하십시오.",
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "reports/diagnostic_refined.md",
            "modules/finance/dtos.py",
            "simulation/dtos/api.py",
            "simulation/initialization/initializer.py"
        ],
        "output_path": "gemini-output/spec/MISSION_tech_debt_clearance_spec_SPEC.md"
    },
    "MISSION_finance_api_dto_spec": {
        "title": "Finance Module API & DTO Realignment",
        "worker": "spec",
        "instruction": "Finance 모듈의 DTO(`modules/finance/dtos.py`)를 전수 조사하여 TypedDict로 된 유산을 @dataclass로 전환하고, SettlementSystem과의 인터페이스 정합성을 분석하십시오. M2 역전 방지 및 통화 무결성을 보장하기 위한 API 명세를 작성하십시오.",
        "context_files": ["modules/finance/dtos.py", "modules/finance/api.py", "simulation/systems/settlement_system.py"],
        "output_path": "gemini-output/spec/MISSION_finance_api_dto_SPEC.md"
    },
    "MISSION_firm_api_dto_spec": {
        "title": "Firm Module API & DTO Realignment",
        "worker": "spec",
        "instruction": "Firm 모듈의 내부 DTO와 외부 노출 API의 불일치를 분석하십시오. 특히 FirmStateDTO와 FirmConfigDTO가 모든 시스템 엔진에서 일관되게 사용되도록 정렬 계획을 수립하십시오.",
        "context_files": ["modules/firm/api.py", "modules/simulation/dtos/api.py", "simulation/firms.py"],
        "output_path": "gemini-output/spec/MISSION_firm_api_dto_SPEC.md"
    },
    "MISSION_household_api_dto_spec": {
        "title": "Household Module API & DTO Realignment",
        "worker": "spec",
        "instruction": "Household의 자산 및 소비 정보가 DTO를 통해 안전하게 전달되도록 구조를 설계하십시오. 직접적인 속성 접근을 지양하고 Snapshot 기반의 데이터 통신 스펙을 정의하십시오.",
        "context_files": ["modules/household/api.py", "simulation/core_agents.py"],
        "output_path": "gemini-output/spec/MISSION_household_api_dto_SPEC.md"
    },
    "MISSION_government_api_dto_spec": {
        "title": "Government Module API & DTO Realignment",
        "worker": "spec",
        "instruction": "정부 정책 DTO(GovernmentPolicyDTO)와 하위 시스템(Tax, Treasury) 간의 API 연계를 최적화하십시오. 법인세 정합성 수정 사항을 반영한 통합 API 명세를 작성하십시오.",
        "context_files": ["modules/government/api.py", "modules/government/dtos.py", "modules/government/taxation/system.py"],
        "output_path": "gemini-output/spec/MISSION_government_api_dto_SPEC.md"
    },
    "MISSION_labor_api_dto_spec": {
        "title": "Labor Module API & DTO Realignment",
        "worker": "spec",
        "instruction": "LaborMarket의 매칭 데이터와 Order DTO 간의 결합도를 낮추고, 가독성 높은 인터페이스를 설계하십시오. Major 매칭 로직의 DTO 전환 계획을 포함하십시오.",
        "context_files": ["modules/labor/api.py", "simulation/systems/labor_market.py"],
        "output_path": "gemini-output/spec/MISSION_labor_api_dto_SPEC.md"
    }
}

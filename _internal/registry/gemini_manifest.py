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
    "phase41_bank_registry_spec": {
        "title": "Extract BankRegistry Service (TD-ARCH-SETTLEMENT-BLOAT)",
        "worker": "spec",
        "instruction": "Extract bank account management logic from SettlementSystem into a dedicated BankRegistry service. Define IBankRegistry protocol in modules/finance/api.py and implement the service in simulation/systems/bank_registry.py. Ensure backward compatibility in SettlementSystem by delegating calls to the new registry.",
        "context_files": [
            "simulation/systems/settlement_system.py",
            "simulation/bank.py",
            "modules/finance/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "gemini-output/spec/MISSION_bank_registry_SPEC.md"
    },
    "phase41_firm_refinement_spec": {
        "title": "Rename Firm Capital Stock & Firm SEO Migration (TD-LIFECYCLE-NAMING, TD-ARCH-SEO-LEGACY)",
        "worker": "spec",
        "instruction": "Rename 'capital_stock_pennies' to 'capital_stock_units' in firms.py and update associated valuation logic to prevent 100x inflation. Also, migrate Firm.make_decision to a pure SEO (Stateless Engine Orchestration) path by removing legacy decision branches.",
        "context_files": [
            "simulation/firms.py",
            "modules/finance/api.py",
            "design/HANDOVER.md"
        ],
        "output_path": "gemini-output/spec/MISSION_firm_refinement_SPEC.md"
    },
    "phase41_labor_config_spec": {
        "title": "Externalize Labor Majors to Configuration (TD-CONFIG-HARDCODED-MAJORS)",
        "worker": "spec",
        "instruction": "Move the hardcoded MAJORS list from modules/labor/constants.py to config/economy_params.yaml. Update the constants.py to load this list dynamically via ConfigManager to improve system flexibility.",
        "context_files": [
            "modules/labor/constants.py",
            "config/economy_params.yaml",
            "modules/common/config_manager/api.py"
        ],
        "output_path": "gemini-output/spec/MISSION_labor_config_SPEC.md"
    }
}

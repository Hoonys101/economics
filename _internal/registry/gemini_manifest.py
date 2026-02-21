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
    # Wave 5: Data & DTO Purity
    "wave5-dto-purity": {
        "title": "[TD-UI-DTO-PURITY] Enforce Canonical Order and UI DTOs",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave5_dto_purity_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave5_dto_purity_SPEC.md",
            "modules/market/api.py",
            "modules/system/telemetry_exchange.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave5_dto_purity_JULES_SPEC.md"
    },
    "wave5-config-purity": {
        "title": "[TD-CONF-GHOST-BIND] Implement Config Proxy for Runtime Binding",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave5_config_purity_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave5_config_purity_SPEC.md",
            "modules/finance/engine.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave5_config_purity_JULES_SPEC.md"
    },
    
    # Wave 6: AI & Logic Refinement
    "wave6-ai-debt": {
        "title": "[TD-AI-DEBT-AWARE] Integrate Debt Constraints into AI Planning",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave6_ai_debt_aware_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave6_ai_debt_aware_SPEC.md",
            "modules/firm/planner.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave6_ai_debt_JULES_SPEC.md"
    },
    "wave6-fiscal-masking": {
        "title": "[TD-ECON-WAR-STIMULUS] Implement Progressive Taxation and Wage Scaling",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave6_fiscal_masking_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave6_fiscal_masking_SPEC.md",
            "modules/government/policy_engine.py",
            "modules/firm/hr_engine.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave6_fiscal_masking_JULES_SPEC.md"
    },
    
    # Wave 7: Architecture & Ops Cleanup
    "wave7-firm-mutation": {
        "title": "[TD-ARCH-FIRM-MUTATION] Enforce Stateless Engine Orchestration in Firm",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave7_firm_mutation_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave7_firm_mutation_SPEC.md",
            "simulation/firms.py",
            "modules/firm/sales_engine.py",
            "modules/firm/brand_engine.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave7_firm_mutation_JULES_SPEC.md"
    },
    "wave7-dx-automation": {
        "title": "[TD-DX-AUTO-CRYSTAL] Automate Mission Registration and Optimize Death System",
        "worker": "spec",
        "instruction": "Read artifacts/specs/MISSION_wave7_dx_automation_SPEC.md and generate a full Jules implementation spec.",
        "context_files": [
            "artifacts/specs/MISSION_wave7_dx_automation_SPEC.md",
            "_internal/scripts/launcher.py",
            "_internal/registry/service.py",
            "modules/system/death_system.py"
        ],
        "output_path": "artifacts/specs/MISSION_wave7_dx_automation_JULES_SPEC.md"
    }
}

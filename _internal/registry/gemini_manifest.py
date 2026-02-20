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
    "audit-agent-lifecycle": {
        "worker": "audit",
        "instruction": "Audit Agent Lifecycle stability for registration-before-transfer violations.",
        "context_files": [
            "c:/coding/economics/design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md",
            "c:/coding/economics/simulation/systems/lifecycle_manager.py",
            "c:/coding/economics/simulation/systems/firm_management.py"
        ]
    },
    "audit-government-solvency": {
        "worker": "audit",
        "instruction": "Audit Government Solvency guardrails and partial execution state.",
        "context_files": [
            "c:/coding/economics/design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md",
            "c:/coding/economics/simulation/systems/settlement_system.py",
            "c:/coding/economics/modules/government/engines/fiscal_engine.py"
        ]
    },
    "audit-handler-alignment": {
        "worker": "audit",
        "instruction": "Audit Transaction Handler alignment and SSoT registration.",
        "context_files": [
            "c:/coding/economics/design/_archive/insights/2026-02-19_Handler_Alignment_Map.md",
            "c:/coding/economics/simulation/systems/simulation_initializer.py",
            "c:/coding/economics/modules/finance/transaction/engine.py"
        ]
    },
    "audit-ma-penny-migration": {
        "worker": "audit",
        "instruction": "Audit M&A module for float-to-penny violations and type integrity.",
        "context_files": [
            "c:/coding/economics/design/_archive/insights/2026-02-19_MA_Penny_Migration.md",
            "c:/coding/economics/simulation/systems/ma_manager.py",
            "c:/coding/economics/modules/market/stock_market.py"
        ]
    },
    "audit-structural-integrity-crystallization": {
        "worker": "crystallizer",
        "instruction": "Summarize insights from Phase 22 merges and update ARCHITECTURAL_INSIGHTS.md accordingly.",
        "context_files": [
            "c:/coding/economics/design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md",
            "c:/coding/economics/design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md",
            "c:/coding/economics/design/_archive/insights/2026-02-19_Handler_Alignment_Map.md",
            "c:/coding/economics/design/_archive/insights/2026-02-19_MA_Penny_Migration.md"
        ]
    }
}

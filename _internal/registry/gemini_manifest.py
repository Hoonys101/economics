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
    "phase4-ai-logic-audit": {
        "title": "Phase 4.1: AI & Logic Planning Audit",
        "worker": "audit",
        "instruction": "Mission 4.1 기획 및 설계를 위한 코드 감사. AI의 부채 한도 인식, 라이프사이클 큐 정합성(Scrubbing), 재정 정책 튜닝 포인트를 분석하여 수석과의 논의를 위한 기술 제안 보고서를 작성하라. MISSION_spec 문서를 엄격히 준수할 것.",
        "context_files": [
            "simulation/decisions/ai_driven_household_engine.py",
            "simulation/decisions/ai_driven_firm_engine.py",
            "simulation/systems/lifecycle_manager.py",
            "simulation/agents/government.py",
            "modules/government/engines/fiscal_engine.py",
            "simulation/dtos/api.py"
        ],
        "output_path": "design/3_work_artifacts/reports/active/REPORT_phase4-ai-logic-audit.md"
    },
    "phase4-ai-impact-audit": {
        "title": "Phase 4.1: AI & Labor Market Impact Audit",
        "worker": "audit",
        "instruction": "신규 'Market Insight' 엔진 및 '노동 시장 가성비 매칭' 도입으로 인한 시스템 전반의 여파를 분석하라. 기존 AI 엔진, DTO 흐름, 오케스트레이션 정합성을 중점적으로 감사하고, '다 깨질 수 있는' 지점들을 식별하여 안전한 API/DTO 전환 설계를 제안하라. MISSION_phase4-ai-impact-audit_SPEC.md를 따를 것.",
        "context_files": [
            "simulation/dtos/api.py",
            "simulation/decisions/ai_driven_household_engine.py",
            "simulation/decisions/ai_driven_firm_engine.py",
            "simulation/orchestration/tick_orchestrator.py",
            "simulation/systems/settlement_system.py",
            "design/3_work_artifacts/reports/active/REPORT_phase4-ai-asymmetry-planning.md"
        ],
        "output_path": "design/3_work_artifacts/reports/active/REPORT_phase4-ai-impact-audit.md"
    },
    "phase4-ai-dto-coding": {
        "title": "Phase 4.1: AI & Labor DTO/API Precision Coding",
        "worker": "spec",
        "instruction": "Impact Audit 및 Architect 지침을 바탕으로, 시스템 전반의 DTO 및 API 코드를 완성하라. market_insight 필드 단일화, Fiscal 상수 레지스트리 이관, Monetary 프로토콜 정합성 확보를 위한 '최종 코드 블록'을 작성하라. MISSION_phase4-ai-dto-standardization_SPEC.md를 엄격히 준수하며, Jules가 즉시 적용할 수 있는 형태의 Diff 또는 전체 코드를 제공하라.",
        "context_files": [
            "simulation/dtos/api.py",
            "modules/household/dtos.py",
            "modules/simulation/dtos/api.py",
            "modules/government/engines/fiscal_engine.py",
            "modules/finance/handlers/monetary_handler.py",
            "design/3_work_artifacts/reports/active/REPORT_phase4-ai-impact-audit.md",
            "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-dto-standardization_SPEC.md"
        ],
        "output_path": "design/3_work_artifacts/reports/active/REPORT_phase4-ai-dto-final-code.md"
    }
}

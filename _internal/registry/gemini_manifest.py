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
    "analyze-runtime-structural-failures": {
        "title": "Structural Runtime Failure & Cleanup Analysis",
        "worker": "audit",
        "instruction": "초기 분석 완료. design/_archive/insights/2026-02-19_Structural_Analysis_Report.md 참고.",
        "context_files": ["design/_archive/insights/2026-02-19_Structural_Analysis_Report.md"],
        "output_path": "reports/diagnostics/structural_analysis_summary.md"
    },
    "audit-structural-integrity-crystallization": {
        "title": "Structural Integrity Wisdom Crystallization",
        "worker": "crystallizer",
        "instruction": """
목표: 이번 '구조적 안정성 진단' 세션에서 얻은 건축학적 통찰을 영구 지식 자산으로 전환.

추출 대상:
1. 'Registration-before-Transfer' (원자적 생애주기 시퀀스)의 중요성과 구현 지침.
2. 'Solvency Guardrails' (예산 기반 지출 제어)의 설계 패턴.
3. 'Penny Standard Expansion' (M&A 및 시장 지표의 정수화)의 기술적 교훈.
4. 'Queue Scrubbing' (시스템 큐 클리닝)을 통한 참조 무결성 확보 방안.

결과물:
- ARCHITECTURAL_INSIGHTS.md에 추가할 마크다운 스니펫.
- 각 통찰별 '가동 가능한(Actionable)' 설계 원칙 요약.
""",
        "context_files": [
            "design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md",
            "design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md",
            "design/_archive/insights/2026-02-19_Handler_Alignment_Map.md",
            "design/_archive/insights/2026-02-19_MA_Penny_Migration.md",
            "design/_archive/insights/2026-02-19_Structural_Analysis_Report.md"
        ],
        "output_path": "design/3_work_artifacts/drafts/STRUCTURAL_INTEGRITY_CRYSTALLIZATION.md"
    },
    # Previous granular audit missions (Restored for persistence)
    "audit-agent-lifecycle-atomicity": {
        "title": "Agent Lifecycle & Transaction Routing Atomicity Audit",
        "worker": "audit",
        "instruction": "AGENT_LIFECYCLE_STABILITY.md 생성을 위해 기수행됨.",
        "context_files": ["design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md"],
        "output_path": "design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md"
    },
    "audit-fiscal-monetary-handlers": {
        "title": "Fiscal & Monetary Transaction Handler Alignment Audit",
        "worker": "audit",
        "instruction": "HANDLER_ALIGNMENT_MAP.md 생성을 위해 기수행됨.",
        "context_files": ["design/_archive/insights/2026-02-19_Handler_Alignment_Map.md"],
        "output_path": "design/_archive/insights/2026-02-19_Handler_Alignment_Map.md"
    },
    "audit-government-solvency-checks": {
        "title": "Government Budget Guardrails & Solvency Check Audit",
        "worker": "audit",
        "instruction": "GOVT_SOLVENCY_GUARDRAILS.md 생성을 위해 기수행됨.",
        "context_files": ["design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md"],
        "output_path": "design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md"
    },
    "audit-ma-pennies-migration": {
        "title": "M&A Module Penny Standard Migration Audit",
        "worker": "audit",
        "instruction": "MA_PENNIES_MIGRATION_PLAN.md 생성을 위해 기수행됨.",
        "context_files": ["design/_archive/insights/2026-02-19_MA_Penny_Migration.md"],
        "output_path": "design/_archive/insights/2026-02-19_MA_Penny_Migration.md"
    }
}

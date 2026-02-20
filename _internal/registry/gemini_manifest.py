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
    "firm-ai-audit": {
        "title": "Firm Refactor & AI Debt Awareness Audit",
        "worker": "audit",
        "instruction": """
        Check for two specific technical debts and report their current status... (Already Run)
        """,
        "context_files": [
            "simulation/firms.py",
            "simulation/components/engines/hr_engine.py",
            "simulation/components/engines/finance_engine.py",
            "modules/firm/orchestrators/firm_action_executor.py",
            "simulation/ai/firm_system2_planner.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "design/1_governance/architecture/ARCH_AGENTS.md"
        ],
        "output_path": "artifacts/reports/firm_ai_audit_report.md"
    },
    "firm-ai-spec": {
        "title": "Firm Refactor & AI Hardening Specification",
        "worker": "spec",
        "instruction": """
        Based on output in artifacts/reports/firm_ai_audit_report.md, create a MISSION_spec for Jules to implement:
        1. Refactor InventoryComponent and FinancialComponent to remove .attach(self) and satisfy the SEO pattern.
        2. Update FirmSystem2Planner._calculate_npv to factor in debt interest and repayment.
        3. Pass leverage/debt data to AI to penalize over-spending intents.
        
        Ensure the spec follows the 7-Step Protocol and the Jules Delegation Protocol.
        """,
        "context_files": [
            "artifacts/reports/firm_ai_audit_report.md",
            "simulation/firms.py",
            "modules/agent_framework/components/inventory_component.py",
            "modules/agent_framework/components/financial_component.py",
            "simulation/ai/firm_system2_planner.py",
            "modules/firm/api.py"
        ],
        "output_path": "artifacts/specs/MISSION_firm_ai_hardening_spec.md"
    }
}

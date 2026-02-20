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
        "title": "Firm Architecture & AI Debt Audit",
        "worker": "audit",
        "instruction": "Audit the Firm agent and its components for remaining parent pointer coupling (TD-ARCH-FIRM-COUP) and check if FirmSystem2Planner is aware of debt/interest constraints (TD-AI-DEBT-AWARE).",
        "context_files": [
            "simulation/firms/firm.py",
            "simulation/firms/components/inventory_component.py",
            "simulation/firms/components/financial_component.py",
            "simulation/ai/planners/firm_system2_planner.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/reports/firm_ai_audit_report.md"
    },
    "firm-ai-spec": {
        "title": "Firm Decoupling & AI Hardening Spec",
        "worker": "spec",
        "instruction": "Based on the audit report, create a MISSION_spec for Jules to: 1. Remove parent pointers from Inventory/Financial components. 2. Harden FirmSystem2Planner with debt constraint awareness.",
        "context_files": [
            "artifacts/reports/firm_ai_audit_report.md",
            "simulation/firms/firm.py",
            "modules/firm/api.py"
        ],
        "output_path": "artifacts/specs/MISSION_firm_ai_hardening_spec.md"
    },
    "market-systems-spec": {
        "title": "Market Precision & Robustness Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to resolve TD-MARKET-FLOAT-CAST (unsafe cast) and TD-MARKET-STRING-PARSE (brittle parsing).",
        "context_files": [
            "simulation/markets/matching_engine.py",
            "simulation/markets/order_book_market.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_market_systems_hardening_spec.md"
    },
    "finance-purity-spec": {
        "title": "Finance Protocol Purity Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to resolve TD-PROTO-MONETARY by refactoring MonetaryTransactionHandler to use strict Protocols.",
        "context_files": [
            "simulation/systems/handlers/monetary_handler.py",
            "modules/common/interfaces.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_finance_purity_refactor_spec.md"
    },
    "firm-decoupling-spec": {
        "title": "Firm Architecture Decoupling Spec (Constants & Protocols)",
        "worker": "spec",
        "instruction": """
        Create a MISSION_spec for Jules to:
        1. Resolve TD-CONF-MAGIC-NUMBERS: Move hardcoded constants in FinanceEngine (365, 1.8, repayment rates) to Config DTOs or EconomyConstants.
        2. Resolve TD-ARCH-LOAN-CIRCULAR: Introduce ILoanMarket Protocol to break circular dependency between Firm and LoanMarket.
        """,
        "context_files": [
            "simulation/firms/firm.py",
            "simulation/firms/engines/finance_engine.py",
            "simulation/loan_market.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_firm_decoupling_spec.md"
    }
}

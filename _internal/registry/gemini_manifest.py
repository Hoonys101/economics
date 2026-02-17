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
    "liquidate-residual": {
        "title": "Liquidate Residual Failures Diagnostic",
        "worker": "spec",
        "instruction": "Based on the Integrated Mission Guide, conduct a diagnostic audit of the remaining ~10 test failures. Specifically, identify the legacy field 'executive_salary_freeze' in welfare_service.py and propose the replacement with 'executive_bonus_allowed'. Refactor SalesEngine and FinanceEngine to eliminate Dollar-vs-Penny induction errors and precision drift in pricing logic. Output a precise spec for Jules to liquidate these specific items.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_liquidate_residual_and_precision_SPEC.md",
            "modules/government/services/welfare_service.py",
            "simulation/components/engines/sales_engine.py",
            "simulation/components/engines/finance_engine.py",
            "modules/finance/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_liquidate-residual-implementation_SPEC.md"
    },
    "market-precision-spec": {
        "title": "Market Precision Refactor Spec (Integer Math)",
        "worker": "spec",
        "instruction": "Draft a high-fidelity implementation spec for refactoring the MatchingEngine into Integer Math with Zero-Sum rounding rules. Analyze the weighted average price calculation and define the integer-based formula to eliminate drift. Design the collection mechanism for residual pennies to ensure M2 integrity.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_market_precision_refactor_SPEC.md",
            "simulation/markets/matching_engine.py",
            "simulation/markets/order_book_market.py",
            "modules/finance/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_market-precision-refactor_SPEC.md"
    },
    "protocol-lockdown-spec": {
        "title": "Protocol Enforcement & Lockdown Spec",
        "worker": "spec",
        "instruction": "Design the technical implementation for Phase 15 Architectural Lockdown. Propose custom Ruff rules or static analysis scripts to block direct private member access (like .inventory, .wallet). Update QUICKSTART.md with mandatory protocol sections for contributors.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_protocol_lockdown_SPEC.md",
            "design/QUICKSTART.md",
            "design/1_governance/platform_architecture.md",
            "simulation/components/engines/sales_engine.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_protocol-lockdown-implementation_SPEC.md"
    },
    "lifecycle-decomposition-spec": {
        "title": "Lifecycle Manager Decomposition Spec",
        "worker": "spec",
        "instruction": "Based on the Integrated Mission Guide, design the decomposition of the LifecycleManager monolith into discrete systems: BirthSystem, DeathSystem, and AgingSystem. Focus on stateless coordination and improved unit testability. Output a high-fidelity implementation spec for Jules.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_lifecycle_decomposition_SPEC.md",
            "simulation/systems/lifecycle_manager.py",
            "main.py",
            "modules/government/services/welfare_service.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_lifecycle-decomposition-implementation_SPEC.md"
    },
    "transaction-unification-spec": {
        "title": "Transaction Logic Unification Spec",
        "worker": "spec",
        "instruction": "Design the unification of transaction processing by deprecating the legacy TransactionManager and migrating all logic to the TransactionProcessor. Ensure safety parity (double-spending protection) and strict SettlementSystem API adherence. Output a precise spec for Jules.",
        "context_files": [
            "design/3_work_artifacts/specs/MISSION_transaction_unification_SPEC.md",
            "simulation/systems/transaction_manager.py",
            "simulation/systems/transaction_processor.py",
            "simulation/markets/matching_engine.py",
            "modules/finance/api.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_transaction-unification-implementation_SPEC.md"
    },
    "regression-audit": {
        "title": "Post-Merge Regression & Deprecation Audit",
        "worker": "audit",
        "instruction": "Conduct a comprehensive audit of current test failures and deprecation warnings. 1) Analyze why 'test_validator_insufficient_funds' is failing (likely a mock discrepancy with the new 'allows_overdraft' property). 2) Catalog the 10 identified DeprecationWarnings (Government.collect_tax, GovernmentDecisionEngine, HouseholdFactory, StockOrder) and propose a systematic liquidation plan. Output an audit report with clear migration steps for Jules.",
        "context_files": [
            "tests/unit/test_transaction_engine.py",
            "modules/finance/transaction/api.py",
            "modules/finance/transaction/engine.py",
            "simulation/systems/transaction_manager.py",
            "modules/government/agents.py",
            "tests/integration/test_government_fiscal_policy.py"
        ],
        "output_path": "design/3_work_artifacts/audits/MISSION_post-merge-regression-audit_REPORT.md"
    }
}

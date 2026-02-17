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
    "liquidate-dto-contracts": {
        "title": "Liquidate DTO Contract Desyncs",
        "worker": "spec",
        "instruction": "Draft a SPEC to fix BorrowerProfileDTO signature errors and residual LoanInfoDTO subscripting across Firm logic and 700+ tests. Ensure all keyword arguments match the frozen dataclass definition. Refer to TD-DTO-DESYNC-2026.",
        "context_files": [
            "simulation/decisions/firm/financial_strategy.py",
            "tests/unit/corporate/test_financial_strategy.py",
            "tests/unit/finance/test_finance_system_refactor.py"
        ]
    },
    "liquidate-loan-market": {
        "title": "Liquidate LoanMarket Dict-Leak",
        "worker": "spec",
        "instruction": "Draft a SPEC to resolve the AttributeError in loan_market.py where a 'dict' is returned instead of a LoanInfoDTO object. Trace the origin in bank.stage_loan and ensure dot notation is used throughout.",
        "context_files": [
            "simulation/loan_market.py",
            "simulation/bank.py",
            "tests/unit/markets/test_loan_market_mortgage.py"
        ]
    },
    "modernize-omo-tests": {
        "title": "Modernize OMO & Settlement Tests (SSoT Alignment)",
        "worker": "spec",
        "instruction": "Draft a SPEC to refactor test_omo_system.py and test_atomic_settlement.py. Replace direct Agent.assets checks with settlement_system.get_balance() as per TEST_REFRACTORING_GUIDE.md. Resolve existing 500 != (500 +/- 100) failures.",
        "context_files": [
            "tests/integration/test_omo_system.py",
            "tests/integration/test_atomic_settlement.py",
            "design/1_governance/architecture/standards/TEST_REFRACTORING_GUIDE.md"
        ]
    },
    "modernize-bailout-tests": {
        "title": "Modernize Bailout & DTO Signature Tests",
        "worker": "spec",
        "instruction": "Draft a SPEC to fix BailoutCovenant attribute errors (executive_salary_freeze vs bonus) and BorrowerProfileDTO signature desyncs in remaining test files. Ensure mocks return strict Dataclasses.",
        "context_files": [
            "tests/integration/test_finance_bailout.py",
            "tests/unit/modules/finance/test_system.py",
            "modules/finance/api.py",
            "design/1_governance/architecture/standards/TEST_REFRACTORING_GUIDE.md"
        ]
    },
    "modernize-regression-tests": {
        "title": "Modernize General Behavioral Regressions",
        "worker": "spec",
        "instruction": "Draft a SPEC to resolve logic regressions in judicial systems and manufacturing ratios. Ensure all balance assertions query the SSoT.",
        "context_files": [
            "tests/unit/governance/test_judicial_system.py",
            "tests/unit/components/test_engines.py",
            "design/1_governance/architecture/standards/TEST_REFRACTORING_GUIDE.md"
        ]
    }
}

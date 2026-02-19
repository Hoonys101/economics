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
        "instruction": """
분석 목표: 시뮬레이션 런타임 중 발생하는 구조적 오류의 근본 원인 파악.

분석 대상:
1. 'Destination account does not exist: 120' 오류:
   - Agent 120 (또는 다른 ID)이 Liquidation/Death 이후에도 왜 트랜잭션의 대상으로 남아있는지 분석.
   - DeathSystem의 에이전트 제거 로직과 TransactionProcessor의 에이전트 참조 로직 간의 정합성 유무 확인.
2. 'No handler for tx type: bond_interest' 경고:
   - FiscalEngine이 생성하는 bond_interest 트랜잭션이 시스템에 왜 누락되었는지 확인.
3. 'Insufficient funds' 오류:
   - 정부 또는 중앙은행이 예산 범위를 초과하여 집행을 시도하는 코드 경로 식별.
   - '예산 없이는 집행 없다'는 원칙이 위배되는 지점 탐색.

결과물:
- 각 오류별 root cause 분석 리포트.
- 구조적 해결을 위한 'Integrity Guard' 및 'Cleanup Sync' 설계 제안.
""",
        "context_files": [
            "simulation/systems/settlement_system.py",
            "simulation/systems/transaction_processor.py",
            "simulation/systems/lifecycle_manager.py",
            "simulation/systems/handlers/financial_handler.py",
            "modules/system/builders/simulation_builder.py",
            "reports/diagnostics/runtime_audit.log"
        ],
        "output_path": "reports/diagnostics/structural_analysis_report.md",
        "model": "gemini-2.0-pro-exp-02-05"
    }
}

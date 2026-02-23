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
    "MISSION_global_tech_debt_liquidation_plan": {
        "title": "Global Technical Debt Liquidation & API/DTO Standardization Plan",
        "worker": "spec",
        "instruction": "기술부채 장부(TECH_DEBT_LEDGER.md)와 핵심 모듈의 DTO/API 정의를 분석하여 시스템 전반의 'DTO 하드닝 및 부채 청산 마스터 플랜'을 수립하십시오.\n\n1. **모듈별 API/DTO 표준 확립**: Finance, Firm, Household, Government, Labor 각 모듈의 최종 @dataclass 구조를 먼저 정의하십시오. 모든 금융 필드에 Penny Standard(int)를 적용하고, 상호 참조를 최소화하는 인터페이스 규약을 수립하십시오.\n2. **청산 시퀀스 설계**: 기술부채 장부의 우선순위에 따라, 데이터 무결성을 보장하며 순차적으로 기능을 구현/수정할 수 있는 'Wave' 기반 실행 계획을 작성하십시오.\n3. **검증 가이드**: 각 단계별로 Zero-Sum Integrity와 SSoT(Single Source of Truth)가 유지되는지 확인할 수 있는 구체적인 검증 지표를 포함하십시오.\n\n결과물은 Jules가 각 모듈별 상세 작업을 수행할 때 가이드로 사용할 수 있는 수준의 마스터 스펙이어야 합니다.",
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "modules/finance/api.py",
            "modules/finance/dtos.py",
            "modules/firm/api.py",
            "modules/household/api.py",
            "modules/government/api.py",
            "modules/government/dtos.py",
            "modules/labor/api.py",
            "simulation/dtos/api.py"
        ],
        "output_path": "gemini-output/spec/GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md"
    },
    "MISSION_spec_liquidation_wave1": {
        "title": "Wave 1: Shared Financial Kernel Implementation Spec",
        "worker": "spec",
        "instruction": "GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md를 바탕으로 `modules/common/financial` 패키지를 생성하고, `Claim`, `MoneyDTO`, `IFinancialEntity`를 이관하기 위한 상세 구현 스펙을 작성하십시오. 특히 Finance와 HR 간의 순환 참조를 제거하는 구체적인 리팩토링 경로를 명시하십시오.",
        "context_files": ["gemini-output/spec/GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md", "modules/finance/api.py", "modules/hr/api.py"],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave1_SPEC.md"
    },
    "MISSION_spec_liquidation_wave1_5": {
        "title": "Wave 1.5: Initialization Order & Concurrency Stability Spec",
        "worker": "spec",
        "instruction": "DIAG_ACCOUNT_ZERO_SPEC.md와 DIAG_CONCURRENCY_SPEC.md를 바탕으로, 시뮬레이션 초기화 순서(`SimulationInitializer`) 수정 및 Agent 0(정부) 등록 로직, 그리고 Windows 환경에서의 크로스 플랫폼 파일 락킹 전략을 수립하는 상세 스펙을 작성하십시오.",
        "context_files": [
            "gemini-output/spec/DIAG_ACCOUNT_ZERO_SPEC.md",
            "gemini-output/spec/DIAG_CONCURRENCY_SPEC.md",
            "simulation/initialization/initializer.py",
            "simulation/systems/settlement_system.py"
        ],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave1_5_SPEC.md"
    },
    "MISSION_spec_liquidation_wave2": {
        "title": "Wave 2: Finance Core Penny Standard & Reserve Sync Spec",
        "worker": "spec",
        "instruction": "Finance 모듈의 Penny Standard(int) 적용 및 DIAG_MONETARY_SPEC.md에서 제안된 '지급준비금 동기화(Reserve Sync)' 상세 스펙을 작성하십시오. SettlementSystem(실물 현금)과 FinanceSystem(장부상의 예금)을 원자적으로 연동하여 은행의 지급 불능 문제를 해결해야 합니다.",
        "context_files": [
            "gemini-output/spec/GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md",
            "gemini-output/spec/DIAG_MONETARY_SPEC.md",
            "modules/finance/api.py",
            "simulation/bank.py"
        ],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave2_SPEC.md"
    },
    "MISSION_spec_liquidation_wave3": {
        "title": "Wave 3: Agent State Penny Sync & Budget Gatekeeper Spec",
        "worker": "spec",
        "instruction": "Firm/Household/Labor의 Penny Standard 동기화와 DIAG_INSOLVENCY_SPEC.md에서 제안된 'Budget Gatekeeper' 도입 상세 스펙을 작성하십시오. 기업의 임금/세금 우선순위(Prioritization)를 강제하고, 지불 불능 시 파산 절차로 안전하게 유도하는 로직을 포함하십시오.",
        "context_files": [
            "gemini-output/spec/GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md",
            "gemini-output/spec/DIAG_INSOLVENCY_SPEC.md",
            "simulation/firms.py",
            "simulation/orchestration/sequencer.py"
        ],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave3_SPEC.md"
    },
    "MISSION_spec_liquidation_wave4": {
        "title": "Wave 4: Government Policy & Fiscal Engine Separation Spec",
        "worker": "spec",
        "instruction": "정부의 정책 결정(Decision)과 실행(Fiscal Execution)을 분리하기 위한 SRP 리팩토링 스펙을 작성하십시오. `FiscalCommandDTO` 도입과 FiscalEngine의 명령어 기반 실행 구조를 설계하십시오.",
        "context_files": ["gemini-output/spec/GLOBAL_TECH_DEBT_LIQUIDATION_SPEC.md", "modules/government/api.py", "modules/government/dtos.py"],
        "output_path": "gemini-output/spec/MISSION_liquidation_wave4_SPEC.md"
    }
    # Add missions here
}

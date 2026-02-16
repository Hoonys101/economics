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
    "audit-tick1-leak": {
        "title": "Forensic Audit: Tick 1 Financial Leak (-99,680.00)",
        "worker": "audit",
        "instruction": "Tick 1에서 발생하는 대규모 자산 누출(-99,680.00)의 근본 원인을 추적하십시오. 1. 초기 상태 설정(`create_simulation`), 2. 은행 초기 자산 부여(`Bank` 초기화), 3. 틱 시작 시의 이자/수수료 계산 등을 중점적으로 분석하십시오. `diagnose_money_leak.py`의 로직과 실제 엔진 코드 간의 불일치가 있는지 확인하고, M2 합계가 보존되지 않는 임계 지점을 특정하십시오.",
        "context_files": [
            "main.py",
            "simulation/orchestration/tick_orchestrator.py",
            "simulation/bank.py",
            "modules/finance/system.py",
            "scripts/diagnose_money_leak.py",
            "config/defaults.py",
            "design/_archive/sessions/20260216_123510/audits/ROOT_CAUSE_PROFILE.md"
        ],
        "output_path": "design/3_work_artifacts/audits/MISSION_tick1-leak_AUDIT.md"
    },
    "audit-tick-loop-sequence": {
        "title": "Architectural Audit: Tick Loop Re-sequencing for Corporate Tax",
        "worker": "spec",
        "instruction": "현재 `Corporate Tax` 계산이 `firm.produce()` 이후에 위치해야 하는 제약사항으로 인해 블락되어 있습니다. `TickOrchestrator`의 페이즈 순서를 분석하여, (1) 기업의 생산/이익 확정, (2) 이에 따른 세금 계산, (3) 모든 트랜잭션의 통합 처리(Transaction Phase)가 논리적 모순 없이 실행될 수 있도록 틱 루프 시퀀스 재설계안을 제안하십시오. `Phase_Production`, `Phase_TaxationIntents`, `Phase_FirmProductionAndSalaries`, `Phase3_Transaction` 간의 데이터 흐름과 의존성을 중점적으로 검토하십시오.",
        "context_files": [
            "simulation/orchestration/tick_orchestrator.py",
            "simulation/orchestration/phases/production.py",
            "simulation/orchestration/phases/taxation_intents.py",
            "simulation/orchestration/phases/firm_operations.py",
            "simulation/orchestration/phases/transaction.py",
            "design/HANDOVER.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_tick-loop-sequence_SPEC.md"
    }
}

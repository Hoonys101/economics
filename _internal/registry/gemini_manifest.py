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
    "WO-WAVE5-MONETARY-AUDIT": {
        "title": "Wave 5 Monetary Audit & Leakage Diagnosis",
        "worker": "audit",
        "instruction": "Analyze the 2.6B penny leakage identified in reports/diagnostic_refined.md. Pinpoint why Expected money supply (authorized changes) diverges from Current wallet summation. Identify the root cause of the 102M jump in Tick 1. Verify if SettlementSystem, TickOrchestrator, or WorldState logic restoration introduced accounting gaps. Provide a fix specification for Jules.",
        "context_files": [
            "reports/diagnostic_refined.md",
            "simulation/world_state.py",
            "simulation/orchestration/tick_orchestrator.py",
            "modules/government/components/monetary_ledger.py",
            "simulation/systems/settlement_system.py",
            "simulation/agents/government.py",
            "simulation/systems/central_bank_system.py",
            "simulation/orchestration/phases/monetary_processing.py",
            "simulation/orchestration/phases/transaction.py",
            "modules/system/constants.py",
            "scripts/operation_forensics.py"
        ],
        "output_path": "gemini-output/spec/MISSION_wave5_monetary_audit_SPEC.md"
    },
    "WO-WAVE6-RESTORATION-SPEC": {
        "title": "Wave 6: Tooling Restoration & Domain Hardening Spec",
        "worker": "spec",
        "instruction": "Generate a comprehensive Integrated Mission Guide for Wave 6. Focus on: 1) Restoring 'ContextInjectorService' in 'dispatchers.py' using lazy imports to resolve circular dependencies. 2) Implementing a 'DefaultTransferHandler' for legacy 'transfer' type transactions to ensure ledger visibility (resolving TD-SYS-TRANSFER-HANDLER-GAP). 3) Auditing 'LaborTransactionHandler' and 'models.py' to enforce 'total_pennies' SSoT and resolve unit inconsistencies (dollars vs pennies). Reference 'QUICKSTART.md' for architectural standards.",
        "context_files": [
            "_internal/registry/commands/dispatchers.py",
            "simulation/initialization/initializer.py",
            "simulation/systems/transaction_processor.py",
            "simulation/systems/handlers/labor_handler.py",
            "simulation/models.py",
            "simulation/systems/settlement_system.py",
            "design/QUICKSTART.md",
            "design/HANDOVER.md",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "gemini-output/spec/MISSION_wave6_restoration_SPEC.md"
    },
    "WO-GRAND-LIQUIDATION-STRATEGY": {
        "title": "Phase 22: Grand Tech-Debt Liquidation Analysis",
        "worker": "spec",
        "instruction": "Analyze the remaining 20+ technical debt items in TECH_DEBT_LEDGER.md and group them into 3 executable waves (Foundation, Finance, Evolution) as outlined in 'implementation_plan.md'. For each wave, generate a detailed MISSION_SPEC that Jules can execute. Focus on structural integrity (initialization sequence), financial soundness (M2/Sagas), and economic balance (Zombie firms). Ensure clear success criteria and verification protocols for each spec.",
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "simulation/initialization/initializer.py",
            "simulation/systems/accounting.py",
            "simulation/orchestration/tick_orchestrator.py",
            "modules/finance/sagas/orchestrator.py",
            "simulation/markets/matching_engine.py",
            "C:/Users/Gram Pro/.gemini/antigravity/brain/52999a6d-bd9f-4877-a711-ec86fe8c2185/implementation_plan.md"
        ],
        "output_path": "gemini-output/spec/MISSION_grand_liquidation_SPEC.md"
    }
}

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
   - output_path (str, Optional): 결과물 저장 경로.
   - model (str, Optional): 모델 지정 ('gemini-3-pro-preview', 'gemini-3-flash-preview').
"""
from typing import Dict, Any

GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "diag-log-analyze": {
        "title": "Analyze Refined Diagnostic Logs",
        "worker": "audit",
        "instruction": (
            "정제된 시뮬레이션 보고서(AUTOPSY_REPORT.md)와 정제된 로그(diagnostic_refined.md), 그리고 아키텍처 가이드(ARCH_*)를 분석하여 시스템의 오작동 패턴을 식별하십시오.\n"
            "- 특히 다중 통화(FX) 정산에서의 부동 소수점 누수나 정산 순서 오류를 찾으십시오.\n"
            "- 발견된 이슈별로 '왜(Why)' 발생했는지 근본 원인을 기술하고, 구체적인 수정 방향을 제안하십시오."
        ),
        "context_files": [
            "reports/AUTOPSY_REPORT.md",
            "reports/diagnostic_refined.md",
            "design/1_governance/architecture/ARCH_TRANSACTIONS.md",
            "design/1_governance/architecture/ARCH_AGENTS.md"
        ],
        "output_path": "reports/diagnostic_findings.md",
        "model": "gemini-3-pro-preview"
    },
    "tech-debt-audit": {
        "title": "Tech Debt Survival Verification Audit",
        "worker": "verify",
        "instruction": (
            "TECH_DEBT_LEDGER.md에 등록된 'Open' 및 'Identified' 기술 부채 항목들이 현재 코드베이스에 실제로 잔존하는지 검증하십시오.\n"
            "- 특히 Wave 1-3(Finance Protocol, Firm Architecture, Operational Purity 등)을 통해 해결되었어야 할 항목들이 여전히 장부에 남아있는지 체크하십시오.\n"
            "- 각 부채별로 [잔존 / 수정됨(False Positive) / 부분 수정] 상태를 판정하고 이유를 기술하십시오."
        ),
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "modules/finance/transaction/engine.py",
            "simulation/initialization/initializer.py",
            "simulation/agents/government.py",
            "simulation/agents/central_bank.py"
        ],
        "output_path": "reports/tech_debt_audit_report.md",
        "model": "gemini-3-pro-preview"
    },
    "spec-fix-sys-registry": {
        "title": "SPEC: Fix System Agent Registration",
        "worker": "spec",
        "instruction": (
            "중앙은행(ID 0)과 공공관리자(PublicManager)가 SimulationInitializer에서 AgentRegistry에 등록되지 않는 문제를 해결하기 위한 MISSION_spec을 작성하십시오.\n"
            "- `SimulationInitializer.build_simulation()`에서 이들을 `sim.agents`에 명시적으로 추가하는 로직을 포함하십시오.\n"
            "- 모든 시스템 예약 ID(0-99)가 일관되게 관리되도록 설계하십시오."
        ),
        "context_files": [
            "simulation/initialization/initializer.py",
            "modules/system/constants.py",
            "modules/system/registry.py"
        ],
        "output_path": "artifacts/specs/MISSION_fix_sys_registry_spec.md"
    },
    "spec-fix-pm-funding": {
        "title": "SPEC: Public Manager funding & Escheatment",
        "worker": "spec",
        "instruction": (
            "공공관리자(PublicManager)가 파산 기업의 자산을 인수(Escheatment)할 때 자금 부족으로 실패하는 문제를 해결하기 위한 MISSION_spec을 작성하십시오.\n"
            "- PM에게 무제한 당좌대월(overdraft) 권한을 부여하거나, 화폐 발행(Mint) 권한을 가진 IMonetaryAuthority 인터페이스를 연동하십시오.\n"
            "- `escheatment_handler` 및 `FinancialEntityAdapter`를 수정하여 PM의 강제 자산 인수가 보장되도록 하십시오."
        ),
        "context_files": [
            "modules/system/execution/public_manager.py",
            "simulation/systems/handlers/escheatment_handler.py",
            "modules/finance/api.py"
        ],
        "output_path": "artifacts/specs/MISSION_fix_pm_funding_spec.md"
    },
    "spec-fix-db-migration": {
        "title": "SPEC: Database Schema Migration (total_pennies)",
        "worker": "spec",
        "instruction": (
            "SQLite 테이블(`transactions`)에 `total_pennies` 컬럼이 누락되어 발생하는 저장 오류를 해결하기 위한 MISSION_spec을 작성하십시오.\n"
            "- 코드에서 해당 컬럼 존재 여부를 체크하고, 없을 경우 `ALTER TABLE`을 수행하거나 스키마를 자동 갱신하는 로직을 설계하십시오.\n"
            "- legacy DB로 인한 런타임 에러 방지를 최우선으로 하십시오."
        ),
        "context_files": [
            "simulation/db/schema.py",
            "simulation/db/db_manager.py",
            "simulation/db/repository.py"
        ],
        "output_path": "artifacts/specs/MISSION_fix_db_migration_spec.md"
    },
    "tech-debt-full-audit": {
        "title": "Full Tech Debt Exhaustive Audit",
        "worker": "verify",
        "instruction": (
            "TECH_DEBT_LEDGER.md에 등록된 '모든' 미결 부채(Open, Identified, Partial) 항목들이 현재 코드베이스에 실제로 어떻게 존재하는지 전수 조사를 수행하십시오.\n"
            "- Wave 1-3 이후의 최신 코드 상태를 반영하여, 각 항목의 실제 위험도와 잔존 여부를 판정하십시오.\n"
            "- 특히 27개의 테스트 실패 사례(`fails.txt`)와 장부상의 부채 항목들 간의 상관관계(예: DTO 불일치, FP/Int 혼용 등)를 구체적으로 식별하십시오.\n"
            "- [생존 / 해결됨 / 부분 해결] 상태를 명확히 하고, 즉시 수정이 필요한 'Critical' 항목을 우선 순위로 정렬하여 보고하십시오."
        ),
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "modules/finance/transaction/engine.py",
            "simulation/initialization/initializer.py",
            "simulation/firms.py",
            "simulation/core_agents.py",
            "simulation/engine.py",
            "modules/simulation/dtos/api.py",
            "reports/diagnostic_findings.md"
        ],
        "output_path": "reports/full_tech_debt_audit_report.md",
        "model": "gemini-3-pro-preview"
    }
}

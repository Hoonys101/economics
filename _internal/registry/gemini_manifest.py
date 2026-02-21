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
    "parallel-debt-recovery": {
        "title": "Parallel Architecture Recovery Plan (Phase 25)",
        "worker": "audit",
        "instruction": """
Analyze diagnostic logs, the tech debt ledger, and the provided source code to design a parallelized remediation strategy.

1. **Conflict-Free Partitioning**: Identify which debt items can be resolved simultaneously (e.g., Lane 1: Finance Logic, Lane 2: Structural Sequencing, Lane 3: DX & Tests).
2. **Clear API/DTO Contracts**: For each remediation unit, define the exact DTO changes or API signatures required to prevent implementation drift across lanes.
3. **Atomic Mission Specs**: Generate separate MISSION_SPEC definitions for each lane. Each spec must be a standalone unit of work for Jules.
4. **Root Cause Mapping**: Link diagnostic failures (SAGA_SKIP, SETTLEMENT_FAIL) directly to specific ledger items (e.g., TD-CRIT-FLOAT-CORE).

Prioritize M2 Integrity (TD-ECON-M2-INV) and Startup Race (TD-ARCH-STARTUP-RACE) as the foundation.
""",
        "context_files": [
            "reports/diagnostic_refined.md",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md",
            "simulation/dtos/api.py",
            "simulation/orchestration/tick_orchestrator.py",
            "simulation/orchestration/phases_recovery.py",
            "modules/finance/engine.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_parallel-debt-recovery_PLAN.md"
    }
}

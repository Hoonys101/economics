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
    "analyze-gov-structure": {
        "title": "Structural Analysis: Government Singleton vs List",
        "worker": "spec",
        "instruction": (
            "Analyze the usage of `government` (singleton) versus `governments` (list) in `WorldState` and `Simulation`.\n\n"
            "**Context:**\n"
            "- `WorldState` defines `self.governments: List[Government] = []`.\n"
            "- `TickOrchestrator` and tests often access `state.government`.\n"
            "- Determining how `state.government` is currently populated (likely dynamic injection in `Simulation`).\n\n"
            "**Objective:**\n"
            "1. Identify where `state.government` is being set (e.g., `initializer.py`, `simulation.py`).\n"
            "2. Propose a structural fix: either add a proper `@property` to `WorldState` or refactor all consumers to use `governments[0]`.\n"
            "3. Assess impact on `TickOrchestrator`, `SimulationState` DTO, and tests."
        ),
        "context_files": [
            "simulation/world_state.py",
            "simulation/engine.py",
            "simulation/initialization/initializer.py",
            "simulation/orchestration/tick_orchestrator.py"
        ],
        "output_path": "design/3_work_artifacts/spec/STRUCT_GOV_FIX_SPEC.md"
    },
    "analyze-deprecations": {
        "title": "Hygiene Analysis: Deprecation Cleanup (Track B)",
        "worker": "spec",
        "instruction": (
            "Analyze the usage of deprecated components and design a refactoring plan.\n\n"
            "**Deprecated targets:**\n"
            "1. `Government.collect_tax` -> `settlement.settle_atomic`\n"
            "2. `HouseholdFactory` (old) -> `simulation.factories.household_factory`\n"
            "3. `StockOrder` -> `CanonicalOrderDTO`\n\n"
            "**Objective:**\n"
            "1. Review the provided context files to understand how deprecated aliases are used.\n"
            "2. For each category, provide a specific `sed` or refactoring pattern.\n"
            "3. Identify any logic changes required (e.g., parameter differences between old/new factories).\n"
            "4. Output a `MISSION_spec` for Jules to execute the cleanup."
        ),
        "context_files": [
            "tests/unit/agents/test_government.py",
            "tests/integration/test_government_tax.py",
            "tests/simulation/factories/test_agent_factory.py",
            "tests/unit/test_household_factory.py",
            "tests/unit/systems/test_demographic_manager_newborn.py",
            "tests/unit/modules/demographics/test_event_consistency.py",
            "tests/system/test_audit_integrity.py",
            "tests/unit/test_market_adapter.py",
            "tests/unit/test_stock_market.py"
        ],
        "output_path": "design/3_work_artifacts/spec/DEPRECATION_CLEANUP_SPEC.md"
    },
}

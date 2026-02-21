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
from _internal.registry.api import mission_registry

LEGACY_GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "debt-liquidation-plan": {
        "title": "Technical Debt Liquidation Strategy",
        "worker": "spec",
        "instruction": "Analyze the TECH_DEBT_LEDGER.md and formulate a comprehensive technical debt liquidation plan. Design the plan such that we execute 2-3 independent missions in parallel per 'wave', and clear all remaining technical debts within 2 to 3 waves total. Ensure missions within the same wave do not have overlapping file dependencies to prevent merge conflicts. Output this execution schedule as a formatted Markdown report.",
        "context_files": [
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/reports/tech_debt_liquidation_plan.md"
    },
    
    # 🌊 WAVE 1: Foundation & Integrity 
    # wave1-finance-protocol-spec migrated to _internal.missions.wave1

    "wave1-lifecycle-hygiene-spec": {
        "title": "Wave 1: System Lifecycle & Dependency Hygiene Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to execute Mission 1.2. Resolve TD-ARCH-DI-SETTLE, TD-SYS-PERF-DEATH, and TD-LIFECYCLE-STALE by using Factory-based DI for Settlement AgentRegistry injection, optimizing DeathSystem O(N) rebuilds, and scrubbing the inter_tick_queue upon agent death.",
        "context_files": [
            "simulation/systems/settlement_system.py",
            "simulation/systems/lifecycle/death_system.py",
            "simulation/systems/lifecycle/agent_lifecycle_manager.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_wave1_lifecycle_hygiene_spec.md"
    },

    # 🌊 WAVE 2: Structural Decoupling
    "wave2-firm-architecture-spec": {
        "title": "Wave 2: Firm Architecture Overhaul Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to execute Mission 2.1. Resolve TD-ARCH-FIRM-COUP and TD-ARCH-FIRM-MUTATION by removing self.parent pointers from all Firm Departments (HR, Finance, Production, Sales), replacing them with DTO injections. Ensure BrandEngine and SalesEngine return ResultDTOs instead of mutating states in-place.",
        "context_files": [
            "simulation/firms/firm.py",
            "modules/firm/engines/brand_engine.py",
            "simulation/components/engines/sales_engine.py",
            "simulation/components/engines/hr_engine.py",
            "simulation/components/engines/production_engine.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_wave2_firm_architecture_spec.md"
    },
    "wave2-market-policy-spec": {
        "title": "Wave 2: Market & Policy Refinement Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to execute Mission 2.2. Resolve TD-DEPR-STOCK-DTO, TD-MARKET-STRING-PARSE, and TD-ECON-WAR-STIMULUS. Replace StockOrder with CanonicalOrderDTO, refactor StockMarket matching extraction to use Tuple IDs, and implement progressive taxation logically in Government handling.",
        "context_files": [
            "simulation/markets/stock_market.py",
            "simulation/agents/government.py",
            "modules/market/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_wave2_market_policy_spec.md"
    },

    # 🌊 WAVE 3: Operations & Polish
    "wave3-analytics-purity-spec": {
        "title": "Wave 3: Operational & Analytics Purity Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to execute Mission 3.1. Resolve TD-ANALYTICS-DTO-BYPASS and TD-UI-DTO-PURITY. Ensure AnalyticsSystem operates strictly on SnapshotDTOs rather than reading raw mutable agents, and enforce Pydantic Models for UI telemetry parsing.",
        "context_files": [
            "simulation/systems/analytics_system.py",
            "modules/simulation/dtos/api.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_wave3_analytics_purity_spec.md"
    },
    "wave3-dx-config-spec": {
        "title": "Wave 3: Developer Experience & Config Hardening Spec",
        "worker": "spec",
        "instruction": "Create a MISSION_spec for Jules to execute Mission 3.2. Resolve TD-DX-AUTO-CRYSTAL and TD-CONF-GHOST-BIND. Implement an auto-discovery registry decorator for Gemini missions to reduce boilerplate, and create a ConfigProxy to lazily resolve dynamic constants avoiding import-time lock-ins.",
        "context_files": [
            "_internal/registry/gemini_manifest.py",
            "config/default_config.py",
            "design/2_operations/ledgers/TECH_DEBT_LEDGER.md"
        ],
        "output_path": "artifacts/specs/MISSION_wave3_dx_config_spec.md"
    }
}

# Scan for new missions
mission_registry.scan_packages("_internal.missions")

# Merge: Priority to Registry (New) over Legacy (Old)
GEMINI_MISSIONS = LEGACY_GEMINI_MISSIONS.copy()
GEMINI_MISSIONS.update(mission_registry.to_manifest())

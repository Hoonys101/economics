"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "exec-cockpit-fe-2": {
        "title": "Cockpit 2.0 FE-2: Macro Canvas + Scatter Plot + Inspector Panel",
        "file": "design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md",
        "instruction": (
            "Implement Phase 2 of the Cockpit 2.0 Frontend. PREREQUISITE: FE-1 must be merged first.\n\n"
            "=== SAME ARCHITECTURAL MANDATE AS FE-1 ===\n"
            "HTML = Structure, CSS = Design, JS = Rendering. Container-Component pattern mandatory.\n\n"
            "=== SCOPE ===\n"
            "1. **Layer 2 — Macro Canvas** (frontend/src/containers/MacroCanvasContainer.tsx):\n"
            "   - LEFT: TimeSeriesPanel.tsx — GDP, CPI, Unemployment, Gini (Recharts LineChart)\n"
            "     * Maintain rolling buffer of last 200 ticks from WebSocket stream\n"
            "     * CSS: frontend/src/components/macro/timeseries.css\n"
            "   - CENTER: SurvivalScatter.tsx — Scatter plot (X: risk_tolerance, Y: wealth)\n"
            "     * Fetch from GET /api/v1/genealogy on tab activation\n"
            "     * Living agents = dot, Dead agents = X mark (color-coded)\n"
            "     * CSS: frontend/src/components/macro/scatter.css\n"
            "   - RIGHT: SectorFlow.tsx — Money flow summary (Household/Firm/Gov balances)\n"
            "     * CSS: frontend/src/components/macro/sectorflow.css\n\n"
            "2. **Layer 3 — Inspector Panel** (frontend/src/containers/InspectorContainer.tsx):\n"
            "   - Slide-over panel from right side on agent click\n"
            "   - Fetch GET /api/v1/inspector/{agent_id}\n"
            "   - Subcomponents:\n"
            "     * AgentIdentity.tsx: ID, type, alive status\n"
            "     * AgentWallet.tsx: currency balances\n"
            "     * AgentDecisionLog.tsx: timeline of decisions (chat-like UI)\n"
            "     * AgentInventory.tsx: item list\n"
            "   - CSS: frontend/src/components/inspector/inspector.css\n\n"
            "3. **Glassmorphism Design**: Apply dark mode + glass-card aesthetic from existing App.css. "
            "All new CSS files must use the existing design tokens (--background, --foreground, --primary, etc.).\n\n"
            "Reference: design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md"
        ),
    },
    "exec-cockpit-stabilization": {
        "title": "Cockpit 2.0 Stabilization: Fix Regressions",
        "file": "design/3_work_artifacts/specs/MISSION_COCKPIT_STABILIZATION_SPEC.md",
        "instruction": (
            "Restore the test suite to 100% PASS by fixing Pydantic-related regressions.\n\n"
            "**Fix Areas:**\n"
            "1. **dashboard/components/controls.py**: Change all `schema['key']` style accesses to `schema.key` (dot notation) for ParameterSchemaDTO.\n"
            "2. **tests/unit/modules/system/test_command_service_unit.py**: Update all `RegistryEntry()` calls to include `key='...'` (e.g. key='test_param').\n"
            "3. **tests/system/test_command_service_rollback.py**: Fix any validation errors in Registry/UndoRecord setups.\n\n"
            "Run `pytest -rfE --tb=line tests/` after fixes to verify success."
        ),
    },
}

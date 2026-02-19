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
    # Add missions here
    "exec-cockpit-be-1": {
        "title": "Cockpit 2.0 BE-1: Pydantic DTOs + GlobalRegistry",
        "file": "design/3_work_artifacts/specs/MISSION_COCKPIT_BACKEND_SPEC.md",
        "instruction": (
            "Implement Phase 1 of the Cockpit 2.0 Backend. SCOPE IS LIMITED TO:\n\n"
            "1. **Pydantic DTO Migration**: Migrate simulation/dtos/watchtower.py from dataclasses to pydantic.BaseModel. "
            "The models MUST exactly match the API Contract in design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md. "
            "Import the canonical models (WatchtowerSnapshotResponse, CockpitCommand, etc.) from modules/governance/cockpit/api.py.\n\n"
            "2. **GlobalRegistry**: Implement modules/core/global_registry.py as specified in the backend spec. "
            "Create the IGlobalRegistry Protocol, RegistryEntry, OriginType enum, and the singleton accessor. "
            "Add seed_registry() to initialize from config.py values.\n\n"
            "3. **DashboardService Hardening**: Update simulation/orchestration/dashboard_service.py to construct "
            "WatchtowerSnapshotResponse (Pydantic) instead of dataclass-based snapshots. Use .model_dump(mode='json').\n\n"
            "4. **Tests**: Create tests/unit/test_cockpit_models.py and tests/unit/test_global_registry.py.\n\n"
            "DO NOT touch: DeathSystem, Genealogy, server.py endpoints. Those are in BE-2."
        ),
    },
    "exec-cockpit-be-2": {
        "title": "Cockpit 2.0 BE-2: Genealogy System + API Endpoints",
        "file": "design/3_work_artifacts/specs/MISSION_COCKPIT_BACKEND_SPEC.md",
        "instruction": (
            "Implement Phase 2 of the Cockpit 2.0 Backend. PREREQUISITE: BE-1 must be merged first.\n\n"
            "1. **AgentGenealogy**: Create modules/watchtower/models/genealogy.py with AgentSurvivalData model "
            "and IGenealogyRepository Protocol as defined in the backend spec. Implement InMemoryGenealogyRepository.\n\n"
            "2. **DeathSystem Hook**: Inject IGenealogyRepository into DeathSystem.__init__() in "
            "simulation/systems/lifecycle/death_system.py. Archive agent traits on liquidation.\n\n"
            "3. **API Endpoints in server.py**:\n"
            "   - WebSocket /ws/live: broadcast WatchtowerSnapshotResponse at 1Hz\n"
            "   - WebSocket /ws/command: validate CockpitCommand via TypeAdapter, route to GlobalRegistry\n"
            "   - REST GET /api/v1/inspector/{agent_id}: return AgentInspectorResponse\n"
            "   - REST GET /api/v1/genealogy: return GenealogyResponse\n\n"
            "4. **Tests**: Add tests for DeathSystem genealogy hook and API endpoint validation.\n\n"
            "Reference: design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md (canonical schemas)."
        ),
    },
    "exec-cockpit-fe-1": {
        "title": "Cockpit 2.0 FE-1: Foundation (Types + WebSocket + HUD + God Bar)",
        "file": "design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md",
        "instruction": (
            "Implement Phase 1 of the Cockpit 2.0 Frontend. Tech: React 19 + Vite + TailwindCSS v4 + Recharts.\n\n"
            "=== ARCHITECTURAL MANDATE: Separation of Concerns ===\n"
            "HTML = Structure (semantic markup, container-component hierarchy)\n"
            "CSS  = Design (all visual styling, layout, animations — NO inline styles in JSX)\n"
            "JS   = Rendering logic (data binding, state management, event handlers — NO styling logic)\n\n"
            "=== CONTAINER-COMPONENT PATTERN ===\n"
            "Every UI section follows Container (data/logic) + Component (pure render):\n"
            "- Container: fetches data, manages state, passes props\n"
            "- Component: receives props, returns JSX, ZERO side effects\n"
            "- CSS: Each component gets a dedicated CSS module or BEM-scoped class block\n\n"
            "=== SCOPE ===\n"
            "1. **TypeScript Types** (frontend/src/types/watchtower.ts): "
            "Define ALL interfaces matching MISSION_COCKPIT_API_CONTRACT.md exactly. "
            "WatchtowerSnapshot, CockpitCommand, AgentInspectorResponse, GenealogyResponse.\n\n"
            "2. **WebSocket Hook** (frontend/src/hooks/useWatchtower.ts): "
            "Replace REST polling. Connect to /ws/live (data) and /ws/command (commands). "
            "Reconnection with exponential backoff. Connection status state. "
            "sendCommand() function for God Mode.\n\n"
            "3. **Layer 1 — HUD Container** (frontend/src/containers/HudContainer.tsx + frontend/src/components/hud/):\n"
            "   - VitalStrip.tsx: Tick, FPS, M2 Leak (green/red), Active Population\n"
            "   - SpeedControl.tsx: Play/Pause/Step buttons → sendCommand()\n"
            "   - CSS: frontend/src/components/hud/hud.css\n\n"
            "4. **Layer 4 — God Bar Container** (frontend/src/containers/GodBarContainer.tsx + frontend/src/components/godbar/):\n"
            "   - ParamSlider.tsx: Base Rate, Tax Rate sliders → SET_PARAM commands\n"
            "   - ShockButton.tsx: Red trigger buttons → TRIGGER_SHOCK commands\n"
            "   - CSS: frontend/src/components/godbar/godbar.css\n\n"
            "5. **App.tsx Restructure**: Replace current tab layout with:\n"
            "   <HudContainer /> (top fixed)\n"
            "   <main> (flex-1, macro canvas — placeholder for FE-2)\n"
            "   <GodBarContainer /> (bottom fixed)\n\n"
            "DO NOT implement: Macro Charts, Scatter Plot, Inspector Panel (those are FE-2)."
        ),
    },
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
}


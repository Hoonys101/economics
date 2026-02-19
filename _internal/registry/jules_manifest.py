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
    "exec-test-regression-fix": {
        "title": "Fix 3 Specific Test Regressions (Factory, Fiscal DTO, Mocks)",
        "instruction": (
            "Fix the 3 specific test regressions identified in the regression spec.\n\n"
            "**Key Instructions:**\n"
            "1. **AgentFactory**: Add the missing `mock_config_module` fixture to `tests/simulation/factories/test_agent_factory.py`.\n"
            "2. **FiscalEngine**: Update `modules/government/engines/fiscal_engine.py` to access `MarketSnapshotDTO` and `FiscalStateDTO` using dot notation (attribute access), NOT dictionary subscription.\n"
            "3. **Integration Tests**: In `tests/integration/test_government_refactor_behavior.py`, ensure `mock_config` provides concrete float/int values for `WEALTH_TAX_THRESHOLD`, `UNEMPLOYMENT_BENEFIT_RATIO`, etc., to prevent `MagicMock < float` errors.\n\n"
            "**Constraint**: Ensure DTOs are treated as objects in the Engine and Mocks are strictly typed in tests."
        ),
        "file": "design/3_work_artifacts/spec/TEST_REGRESSION_FIX_SPEC.md",
        "wait": 30
    },
    "exec-test-regression-fix-v2": {
        "title": "Fix FiscalEngine Test Regressions (DTO Instantiation)",
        "instruction": (
            "Fix the persistent `AttributeError: 'dict' object has no attribute 'market_data'` in `tests/modules/government/engines/test_fiscal_engine.py`.\n\n"
            "**Key Instructions:**\n"
            "1. **Import DTO**: Add `from modules.system.api import MarketSnapshotDTO` to `tests/modules/government/engines/test_fiscal_engine.py`.\n"
            "2. **Refactor Tests**: specificially `test_decide_expansionary`, `test_decide_contractionary`, `test_evaluate_bailout_solvent`, and `test_evaluate_bailout_insolvent`.\n"
            "3. **Instantiation**: Replace raw dictionary `market` objects with proper `MarketSnapshotDTO` instances, ensuring `market_data` is populate correctly as a nested dictionary.\n"
            "   Example:\n"
            "   ```python\n"
            "   market = MarketSnapshotDTO(\n"
            "       tick=100,\n"
            "       market_signals={},\n"
            "       market_data={'current_gdp': 1000.0, 'inflation_rate_annual': 0.02} ...\n"
            "   )\n"
            "   ```\n"
            "**Goal**: Eliminate `AttributeError` by ensuring `FiscalEngine` receives a valid DTO."
        ),
        "file": "design/3_work_artifacts/spec/TEST_REGRESSION_FIX_V2_SPEC.md",
        "wait": 30
    },
    "exec-final-test-fix": {
        "title": "Fix Final Test Regression (Government.py DTO Instantiation)",
        "instruction": (
            "Fix the `AttributeError: 'dict' object has no attribute 'market_data'` error in `simulation/agents/government.py`.\n\n"
            "**Key Instructions:**\n"
            "1. Locate the `provide_firm_bailout` method in `simulation/agents/government.py`.\n"
            "2. Find the `market_snapshot` declaration (roughly line 522).\n"
            "3. Replace the raw dictionary instantiation with a proper `MarketSnapshotDTO` instance.\n"
            "   Example:\n"
            "   ```python\n"
            "   market_snapshot = MarketSnapshotDTO(\n"
            "       tick=current_tick,\n"
            "       market_signals={},\n"
            "       market_data={\n"
            "           \"inflation_rate_annual\": 0.0,\n"
            "           \"current_gdp\": 0.0\n"
            "       }\n"
            "   )\n"
            "   ```\n"
            "**Goal**: Ensure `self.fiscal_engine.decide` receives the correct DTO dataclass, resolving the integration test failure."
        ),
        "file": "simulation/agents/government.py",
        "wait": 30
    },
}

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
    "test-repair-specs": {
        "title": "테스트 결함 원인 분석 및 수리 명세서(Spec) 작성",
        "worker": "spec",
        "instruction": """
다음 테스트 에러 로그를 분석하고, 각 모듈별 원인을 규명한 뒤 `MISSION_test-repair_SPEC.md`를 작성하라.

[Error Log Summary]
1. **MockBank Protocol Mismatch (High Critical)**
   - `TypeError: Can't instantiate abstract class MockBank without an implementation for abstract method 'get_total_deposits'`
   - Affects: `test_circular_imports_fix.py`, `test_settlement_system.py`, etc.
   - Cause: `IBank` interface updated but `MockBank` (in tests) missed the implementation.

2. **Solvency Logic Assertion Failure**
   - `tests/finance/test_solvency_logic.py:106: AssertionError: assert 10000 == 1000000`
   - Cause: Likely unit mismatch (Pennies vs Dollars) or scale factor error.

3. **Asset Management Precision Failure**
   - `tests/simulation/components/engines/test_asset_management_engine.py:41: assert 0.0001 == 0.01`
   - Cause: Expected value (0.01) vs Actual (0.0001) suggests logic using 1bps instead of 1% (or vice versa).

4. **Production Engine Attribute Error**
   - `tests/simulation/components/engines/test_production_engine.py: AttributeError: Mock object has no attribute 'id'`
   - Cause: Mock setup incomplete.

5. **Command Service Rollback Failure**
   - `tests/unit/modules/system/test_command_service_unit.py:130: AssertionError: expected call not found`
   - Cause: Mock verification drift.

[Deliverables]
1. **Root Cause Analysis**: 각 에러 그룹별로 코드 레벨 원인 분석.
2. **Repair Plan**:
   - `MockBank`에 `get_total_deposits` 메서드 추가 (return 0 or meaningful dummy value).
   - `test_solvency_logic.py`의 assertion 값 수정 또는 로직 수정 (단위 통일).
   - `AssetManagementEngine` 또는 테스트의 기대값 보정.
   - 기타 Mock 객체 설정 보완.
3. **Validation Strategy**: `pytest` 재실행을 통한 검증 절차 기술.
""",
        "context_files": [
            "tests/finance/test_circular_imports_fix.py",
            "tests/unit/systems/test_settlement_system.py",
            "tests/finance/test_solvency_logic.py",
            "tests/simulation/components/engines/test_asset_management_engine.py",
            "tests/simulation/components/engines/test_production_engine.py",
            "tests/unit/modules/system/test_command_service_unit.py",
            "modules/finance/api.py", # For IBank definition
            "simulation/components/engines/asset_management_engine.py",
            "modules/finance/system.py"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_test-repair_SPEC.md"
    }
}

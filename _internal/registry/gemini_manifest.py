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
    # Add missions here
    "spec-cockpit-stabilization": {
        "title": "Cockpit 2.0 Phase 3: Post-Merge Stabilization & Regression Fix",
        "worker": "spec",
        "instruction": (
            "Analyze and fix the 11 test failures introduced by the Cockpit 2.0 Pydantic migration.\n\n"
            "**Primary Regressions:**\n"
            "1. **RegistryValueDTO ValidationError**: `modules/system/api.py` defines `RegistryValueDTO` (and alias `RegistryEntry`) "
            "with a mandatory `key: str` field. Many unit tests (e.g., test_command_service_unit.py) instantiate it with only "
            "(value, origin). Fix all instantiation sites in the test suite to include the key.\n"
            "2. **ParameterSchemaDTO Subscripting**: `simulation/dtos/registry_dtos.py:ParameterSchemaDTO` is now a pydantic.BaseModel. "
            "Legacy code in `dashboard/components/controls.py` and some tests are trying to access it via `dto['key']`. "
            "Refactor these to `dto.key` or `.model_dump()` if dict-access is required.\n"
            "3. **Mocking/Assertion Gaps**: In `test_god_command_protocol.py`, some mocks are not receiving the expected calls "
            "due to changes in how `CommandService` interacts with the registry (using get_entry() instead of get()).\n\n"
            "**Goal**: Return a spec that identifies every failing file/line and provides the exact fix to restore the test suite to 100% PASS."
        ),

        "context_files": [
            "modules/system/api.py",
            "modules/system/registry.py",
            "simulation/dtos/registry_dtos.py",
            "modules/system/services/command_service.py",
            "tests/unit/modules/system/test_command_service_unit.py",
            "tests/system/test_command_service_rollback.py",
            "dashboard/components/controls.py",
            "design/3_work_artifacts/specs/MISSION_COCKPIT_API_CONTRACT.md"
        ],
        "output_path": "design/3_work_artifacts/specs/MISSION_COCKPIT_STABILIZATION_SPEC.md"
    },
}

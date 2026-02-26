"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST
=======================================

역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."
[MANDATE]: DTO나 API가 변경되는 경우, 전수조사를 통해 모든 구현체에 변동을 반영한다.

📋 FIELD SCHEMA (JULES_MISSIONS)
    title (str)                : 구현 업무의 제목.
    instruction (str)          : 구체적인 행동 지시. 'file' 미사용 시 필수.
    file (str, Optional)       : MISSION_spec 문서 경로. instruction과 함께 컨텍스트로 제공됨.
    command (str, Optional)    : 실행 명령 유형 (create, send-message, status, complete).
    wait (bool, Optional)      : 작업 완료까지 대기 여부 (기본값: False).

⚙️ LIFECYCLE
    1. 이 파일에 미션을 작성합니다.
    2. `jules-go <KEY>` 실행 시 미션이 JSON으로 이관되고, 이 파일은 자동 리셋됩니다.
    3. 미션 성공 시 JSON에서도 자동 삭제됩니다.
    4. `reset-go` 실행 시 JSON만 초기화됩니다 (이 파일은 보존).
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "WO-FIX-MARKET-TESTS": {
        "title": "Emergency: Market API Test Alignment",
        "file": "gemini-output/spec/MISSION_FIX_MARKET_TESTS_SPEC.md"
    },
    "WO-FIX-LIFECYCLE-MOCKS": {
        "title": "Emergency: Lifecycle Mock Hardening",
        "file": "gemini-output/spec/MISSION_FIX_LIFECYCLE_MOCKS_SPEC.md"
    },
    "WO-FIX-PLATFORM-TESTS": {
        "title": "Emergency: Platform Robustness Fix",
        "file": "gemini-output/spec/MISSION_FIX_PLATFORM_TESTS_SPEC.md"
    },
    # Add missions here
}

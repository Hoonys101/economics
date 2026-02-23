"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."
   - [MANDATE]: DTO나 API가 변경되는 경우, 전수조사를 통해 모든 구현체에 변동을 반영한다.

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "MISSION_impl_wave5_politics": {
        "title": "Wave 5: Political Orchestration & Voting Infrastructure Implementation",
        "instruction": "MISSION_W5_POLITICS_DETAIL.md를 바탕으로 정치 오케스트레이터 및 개별 투표 시스템을 구현하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_W5_POLITICS_DETAIL.md"
    },
    "MISSION_impl_wave5_gov_ai": {
        "title": "Wave 5: Populist Government AI & Reward Hardening Implementation",
        "instruction": "MISSION_W5_GOV_AI_DETAIL.md를 바탕으로 정부 AI의 보상 함수 및 상태 공간 확장을 구현하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_W5_GOV_AI_DETAIL.md"
    },
    "MISSION_impl_wave5_monetary": {
        "title": "Wave 5: Central Bank Multi-Rule Strategy Pattern Implementation",
        "instruction": "MISSION_W5_MONETARY_DETAIL.md를 바탕으로 중앙은행의 전략 패턴 및 다중 준칙을 구현하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_W5_MONETARY_DETAIL.md"
    }
    # Add missions here
}

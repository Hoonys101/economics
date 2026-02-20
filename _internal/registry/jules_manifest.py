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
    "phase23-regression-cleanup": {
        "title": "Phase 23 Regression Cleanup",
        "instruction": "Fix logical failures in the test suite following the P1-P3 merges. Restore 100% pass rate.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_phase23-regression-cleanup_SPEC.md"
    },
    "phase4-ai-dto-standardization": {
        "title": "4.1-A-2: DTO & Registry Standardization [CODE ATTACHED]",
        "instruction": "Gemini가 생성한 REPORT_phase4-ai-dto-final-code.md의 최종 코드 블럭을 모든 해당 파일에 정확히 적용하라. Registry 이관, DTO 단일화, Protocol 구현을 포함한다.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-dto-standardization_SPEC.md"
    },
    "phase4-ai-lifecycle-scrubbing": {
        "title": "4.1-A-3: Lifecycle Scrubbing & Atomic Cleanup",
        "instruction": "AgentLifecycleManager에 ScrubbingPhase를 구현하여 사망한 에이전트의 stale transaction ID를 inter_tick_queue에서 제거하라.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-lifecycle-scrubbing_SPEC.md"
    },
    "phase4-ai-insight-engine": {
        "title": "4.1-A-4: Dynamic Insight Engine (3-Pillar Learning)",
        "instruction": "AITrainingManager(Active Learning), CommerceSystem(Service Boost), Engine(Natural Decay)에 Market Insight 3대 메커니즘을 구현하라.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-insight-engine_SPEC.md"
    },
    "phase4-ai-labor-matching": {
        "title": "4.1-A-5: Labor Market Utility-Priority Matching",
        "instruction": "MatchingEngine을 개편하여 가성비(Utility-Priority) 매칭과 Signaling Game(Lemon Market) 로직을 구현하라.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-labor-matching_SPEC.md"
    },
    "phase4-ai-perception-filters": {
        "title": "4.1-A-6: Perceptual Filters & Reward Tuning",
        "instruction": "DecisionEngine에 인지 시차/노이즈 필터를 적용하고, RewardCalculator에 부채 상한 위반 페널티 로직을 추가하라.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/deea4f29-ec94-41e4-965f-ed0add30f6c7/MISSION_phase4-ai-perception-filters_SPEC.md"
    },
    "final-stabilization-test-fixes": {
        "title": "Final Stabilization & Regression Fixes",
        "instruction": "Fix the remaining 7 test failures related to TickOrchestrator and SagaOrchestrator protocol mismatches.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/spec_final_test_fixes.md"
    }
}

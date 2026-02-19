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
    "fix-agent-lifecycle-atomicity": {
        "title": "Fix Agent Lifecycle Atomicity & Queue Scrubbing",
        "instruction": "2026-02-19_Agent_Lifecycle_Atomicity.md 명세에 따라 Firm Startup 순서를 교정(등록 후 이체)하고, AgentLifecycleManager에 inter_tick_queue 클리닝 로직을 추가하세요.",
        "file": "design/_archive/insights/2026-02-19_Agent_Lifecycle_Atomicity.md",
        "wait": True
    },
    "fix-government-solvency-guardrails": {
        "title": "Implement Government Solvency Guardrails",
        "instruction": "2026-02-19_Govt_Solvency_Guardrails.md 명세에 따라 SettlementSystem에 SolvencyException을 도입하고, 지출 모듈에 부분 집행(Partial Execution) 및 사전 예산 체크를 구현하세요.",
        "file": "design/_archive/insights/2026-02-19_Govt_Solvency_Guardrails.md",
        "wait": True
    },
    "fix-handler-alignment": {
        "title": "Register Missing Fiscal & Monetary Handlers",
        "instruction": "2026-02-19_Handler_Alignment_Map.md 명세에 따라 bailout, bond_issuance 등 누락된 트랜잭션 타입의 핸들러를 SimulationInitializer에 등록하세요.",
        "file": "design/_archive/insights/2026-02-19_Handler_Alignment_Map.md",
        "wait": True
    },
    "fix-ma-pennies-migration": {
        "title": "Migrate M&A & StockMarket to Penny Standard",
        "instruction": "2026-02-19_MA_Penny_Migration.md 명세에 따라 MAManager의 모든 가격 계산에 round_to_pennies()를 적용하고 StockMarket의 가격 지표를 정수(int)로 전환하세요.",
        "file": "design/_archive/insights/2026-02-19_MA_Penny_Migration.md",
        "wait": True
    }
}

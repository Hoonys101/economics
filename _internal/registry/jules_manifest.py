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
    "implement-runtime-structural-fixes": {
        "title": "Implement Structural Runtime Stability Fixes",
        "instruction": """
구현 목표: 런타임 진단 로그에 기반한 구조적 결함 해결 및 'No Budget, No Execution' 원칙 강제.

수정 사항:
1. simulation/systems/firm_management.py:
   - spawn_firm()에서 final_startup_cost를 int()로 캐스팅하여 SettlementSystem 타입 오류 해결.
2. simulation/systems/transaction_processor.py:
   - 트랜잭션 처리 전 buyer, seller 존재 여부 확인 로직 추가 (Agent Existential Guard).
3. simulation/initialization/initializer.py:
   - bond_interest -> MonetaryTransactionHandler 연결.
   - holding_cost -> FinancialTransactionHandler 연결.
4. simulation/systems/settlement_system.py:
   - _prepare_seamless_funds() 내의 자동 은행 인출(Reflexive Liquidity) 로직 제거.
5. simulation/systems/handlers/financial_handler.py:
   - holding_cost 트랜잭션 타입 지원 추가.
6. simulation/systems/handlers/monetary_handler.py:
   - bond_interest 트랜잭션 타입 지원 추가.

검증: 
- 각각의 수정을 완료하고 python diagnose_runtime.py를 실행하여 로그에서 TypeError 및 Missing Handler 오류가 사라졌는지 확인.
""",
        "wait": True
    }
}

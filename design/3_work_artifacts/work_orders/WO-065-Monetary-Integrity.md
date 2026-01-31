# Work Order: - Monetary Integrity & Suture

**Phase:** 26 (Stabilization & Debt Liquidation)
**Priority:** **BLOCKING** (TD-031 상환)
**Assignee:** Jules Bravo (Integrity Specialist)

## 1. Problem Statement
현재 시뮬레이션 엔진에서 가계의 사망, 기업의 청산, 그리고 매크로 쇼크가 발생할 때 통화량이 장부와 일치하지 않는 'Monetary Leakage' 현상이 관찰됩니다. 이는 AI 에이전트의 거시 지표 학습에 치명적인 오류를 유발합니다.

## 2. Objective
사라지는 돈의 구멍을 모두 메우고, 정부의 통화 발행/파기 장부(`total_money_issued`, `total_money_destroyed`)를 실제 통화량과 100% 동기화합니다.

## 3. Implementation Plan

### Task A: 상속 시스템 보강 (Inheritance Suture)
- `simulation/systems/inheritance_manager.py`를 수정하여 사망자의 현금뿐만 아니라 **은행 예금(Bank Deposits)**도 상속인에게 적절히 분배되도록 하십시오.
- 상속인이 없는 경우, 해당 예금을 은행에서 인출하여 **국고(Government Assets)**로 귀속(Escheatment)시키고 장부에 기록하십시오.

### Task B: 매크로 쇼크 장부 동기화 (Shock Suture)
- `simulation/engine.py`의 Tick 600 쇼크 로직을 수정하여, 가계 자산이 50% 삭감될 때 삭감된 총액만큼 `government.total_money_destroyed`를 증가시키십시오.

### Task C: 기업 청산 잔차 처리 (Liquidation Suture)
- 기업 청산 시 주주가 없거나 연고가 없는 잔여 자산이 `engine.py`에서 공중분해되지 않도록, 국고로 환수하는 로직을 보강하십시오.

## 4. Verification
- `python scripts/failure_diagnosis.py`를 실행하여 머지 후 Monetary Delta가 0이 되는지 확인하십시오.
- `tests/test_monetary_integrity.py`를 생성하여 상속과 쇼크 시나리오를 검증하십시오.

---
> [!IMPORTANT]
> 로직 수정 중 새로운 Leakage 포인트가 발견되면 즉시 보고하십시오.

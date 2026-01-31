# Work Order: - Banking Credit Engine (Credit Creation)

**Phase:** 26 (Stabilization & Debt Liquidation)
**Priority:** **CRITICAL** (TD-030 상환)
**Assignee:** Jules Alpha (Engine Expert)

## 1. Problem Statement
현재 은행 시스템은 100% Reserve 방식을 강제하고 있어, 신용 창출을 통한 유동성 공급이 차단되어 있습니다. 이는 경제 규모 성장을 저해하는 병목이 되고 있습니다.

## 2. Objective
부분지급준비제도(Fractional Reserve)를 도입하여 은행이 보유 현금보다 많은 대출을 실해할 수 있는 '신용 창출' 엔진을 활성화합니다.

## 3. Implementation Plan

### Task A: `config.py` 연동
- `RESERVE_REQ_RATIO` 상수를 활용하도록 `bank.py`를 수정하십시오.

### Task B: `grant_loan` 로직 현대화
- `simulation/bank.py`의 `grant_loan` 메서드에서 `assets < amount` 체크를 제거하십시오.
- 대신 `assets < (total_deposits + amount) * RESERVE_REQ_RATIO`를 체크하여 유동성 규제를 구현하십시오.
- `GOLD_STANDARD_MODE`가 `True`일 때는 기존의 엄격한 자산 체크가 유지되도록 분기 처리하십시오.

### Task C: `check_solvency` 보전 시스템 강화
- 대출 실행으로 `assets`가 음수가 되는 것을 허용하되, `run_tick` 사이클 내의 `check_solvency` 호출을 통해 중앙은행(Government)으로부터 유동성을 주입받는 시퀀스를 확인하고 보강하십시오.

## 4. Verification
- `python scripts/verify_banking.py`를 실행하여 신용 창출 대출이 정상적으로 승인되는지 확인하십시오.
- 자산 부족 시 `LENDER_OF_LAST_RESORT` 로그와 함께 통화량이 증가하는지 검증하십시오.

---
> [!IMPORTANT]
> 로직 변경 후 `CREDIT_CREATION` 로그가 명확하게 출력되어야 합니다.

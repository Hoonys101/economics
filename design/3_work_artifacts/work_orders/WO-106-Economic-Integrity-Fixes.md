# Operation Heart Lung (Economic Integrity Fixes)

**Date**: 2026-01-22
**Priority**: CRITICAL (BLOCKER)
**Status**: PENDING

---

## 🎯 Mission Objective
`AUDIT_SPEC_ECONOMIC.md`에서 발견된 화폐/자산 무결성 결함을 수정하여 시뮬레이션의 경제적 안정성을 복구한다.

---

## 📋 작업 세부 지침

### 1. [TD-081] Central Bank Fiat Issuance (양적완화 복구)
**파일:** `modules/finance/system.py` (또는 `CentralBank` 클래스)
- 중앙은행이 `withdraw` 시 잔고 부족 에러를 내는 대신, 화폐를 신규 발행(Seigniorage)하여 공급할 수 있도록 수정한다.
- 중앙은행은 `assets['cash']` 제한 없이 돈을 찍어낼 수 있는 `FiatCurrencyIssuer` 역할을 수행해야 한다.

### 2. [TD-080] Immigration Funding 정상화
**파일:** `simulation/systems/immigration_manager.py`
- 이민자 생성 시 허공에서 자산이 생성되던 로직을 수정한다.
- 이민자 정착금(3000~5000)을 `government.assets`에서 차감하거나, 별도의 `ForeignReserve` 계정에서 인출하도록 처리한다. 만약 정부 자금이 부족하다면 이민이 제한되어야 한다.

### 3. [TD-082] Asset Reflux 강제 (자산 소멸 방지)
**파일:** `simulation/systems/lifecycle_manager.py`, `simulation/bank.py`
- 기업 청산이나 에이전트 소멸 시 `clear()`를 사용하여 재고/주식을 삭제하던 로직을 모두 제거한다.
- `RefluxSystem.capture(asset_type, quantity)`를 호출하여 시스템(또는 채권 은행)으로 가치가 보존되도록 수정한다.

### 4. [TD-080] Initial Wealth Sink 조사 및 수정
**파일:** `simulation/simulation_initializer.py`
- 초기화 시점의 자산 집계와 Tick 1 시점의 집계가 80% 차이나는 원인을 파악하여 로직을 일치시킨다. (현금이 아닌 Capital Stock 등이 집계에서 누락되었는지 확인)

---

## ✅ 완료 조건
1. [ ] `audit_zero_sum.py` 실행 시 Tick 0 -> Tick 1 간의 자산 변동이 설명 가능함.
2. [ ] 중앙은행의 국채 매입(QE) 시 `InsufficientFundsError` 가 발생하지 않음.
3. [ ] 이민자 발생 시 총 통화량(M2)이 허공에서 늘어나지 않음.
4. [ ] 모든 기존 테스트 통과.

---
**Antigravity (Team Leader)**

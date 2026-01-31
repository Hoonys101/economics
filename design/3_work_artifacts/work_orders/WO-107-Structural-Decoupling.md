# Operation Clean Interface (Structural Decoupling)

**Date**: 2026-01-22
**Priority**: MEDIUM
**Status**: PENDING

---

## 🎯 Mission Objective
`AUDIT_SPEC_STRUCTURAL.md`에서 지적된 `DecisionContext`의 데이터 누출(Leaky Abstraction)을 차단하고 아키텍처 결합도를 낮춘다.

---

## 📋 작업 세부 지침

### 1. [TD-078] DecisionContext Snapshot Enforce
**파일:** `simulation/decisions/decision_context.py`, `simulation/core_agents.py`
- `DecisionContext`에 `Household`나 `Firm` 인스턴스 전체를 넘기는 백도어를 폐쇄한다.
- 오직 `HouseholdStateDTO`와 `FirmStateDTO` 스냅샷만 인자로 받도록 생성자를 수정한다.

### 2. [TD-079] TickScheduler Decomposition
**파일:** `simulation/tick_scheduler.py`
- `TickScheduler`에 몰려있는 실행 로직 중 '에이전트 활성/비활성 관리' 부분을 별도의 `LifecycleManager`나 `AgentActivator` 시스템으로 이관한다.
- `TickScheduler`는 순수하게 '시퀀스 제어'와 '타이밍'에만 집중하도록 다이어트한다.

---

## ✅ 완료 조건
1. [ ] `DecisionEngine` 내부에서 `self.context.household.assets = ...` 와 같은 직접 수정 시도가 불가능해짐 (DTO는 불변 또는 복사본이므로).
2. [ ] `TickScheduler` 파일의 라인 수가 30% 이상 감소함.
3. [ ] 모든 결정 로직 엔진 테스트 통과.

---
**Antigravity (Team Leader)**

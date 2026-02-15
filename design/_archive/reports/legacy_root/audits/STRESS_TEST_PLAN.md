# 🖋️ Stress Test Plan: God-Mode Macro Shock Injection

**Status**: Draft (Scribe)
**Version**: v1.0.0
**Mission Key**: GODMODE-STRESS-PLAN
**Orchestrator**: Antigravity (Architect Prime)
**Target**: God-Mode Watchtower & Settlement System Integrity

---

## 1. 개요 (Executive Summary)

본 문서는 `God-Mode Cockpit`을 통한 시뮬레이션 개입 시 엔진의 정합성을 파괴하지 않고 거시적 충격(Macro Shock)을 주입할 수 있는지 검증하기 위한 스트레스 테스트 계획입니다. 특히 `SettlementSystem`의 자산 보존 법칙(Conservation of Money)과 `GlobalRegistry`의 파라미터 동기화 성능을 중점적으로 테스트합니다.

---

## 2. 테스트 환경 및 전제 조건 (Pre-requisites)

### 2.1 기초 공사 확인 (Pre-flight Audit Check)
- **FOUND-01 (GlobalRegistry)**: 모든 타겟 파라미터가 `Registry`에 등록되어 있어야 함.
- **FOUND-02 (Gov Service Separation)**: 정부 모듈 개입 시 부수 효과 제어를 위해 분리 작업 선행 권장.
- **Transaction Logging**: 모든 God-Mode 명령은 "External Source" 타입의 Ledger 트랜잭션으로 기록되어야 함.

---

## 3. 거시 충격 시나리오 (Macro Shock Scenarios)

### ST-001: 하이퍼 인플레이션 (Helicopter Money Injection)
- **목표**: 대규모 유동성 강제 주입 시 `SettlementSystem`의 M2 정합성 유지 및 시장 가격 창발 속도 측정.
- **조작**: 
    - `GodCommand`: `ADD_CASH_ALL_AGENTS(amount=10000)`
    - `GlobalRegistry`: `MONEY_VELOCITY_FACTOR` x 5.0
- **관측 지표**:
    - `total_m2_audit` 통과 여부 (Injection Ledger 합산 시).
    - CPI(소비자 물가 지수)의 반응 지연 시간(Tick).
- **성공 기준**: 통화량 급증 후에도 `Sum(Agent Cash) - Injection = Initial M2` 공식이 성립해야 함.

### ST-002: 시스템적 뱅크런 (Forced Liquidity Crisis)
- **목표**: 금융 신뢰 붕괴 시 `SettlementSystem`의 락(Lock) 경합 및 아토믹성 검증.
- **조작**:
    - `GlobalRegistry`: `SOCIAL_TRUST_SCORE` -> 0.0
    - `GodCommand`: `FORCE_WITHDRAW_ALL(bank_id="CENTRAL")`
- **관측 지표**:
    - 초당 트랜잭션 처리량 (TPS).
    - `SettlementSystem` 데드락 발생 여부.
- **성공 기준**: 모든 인출 요청이 순차적으로 처리되거나, 은행 잔고 고갈 시 'Graceful Failure' 응답을 Watchtower에 반환함.

### ST-003: 전쟁 및 기근 (Capital & Inventory Destruction)
- **목표**: 자산 소멸(Asset Destruction) 상황에서의 회계 정합성 및 생존 루프 동작 검증.
- **조작**:
    - `GodCommand`: `DESTROY_INVENTORY(target="FOOD", ratio=0.9)`
    - `GlobalRegistry`: `PRODUCTION_EFFICIENCY` -> 0.1
- **관측 지표**:
    - 아사(Starvation) 발생률 및 에이전트 사망 처리 로직의 무결성.
    - 소멸된 자산의 재무제표 반영 정확도.
- **성공 기준**: 자산 소멸이 'Loss'로 명확히 기록되며, 시스템 크래시 없이 인구 붕괴 시나리오(SC-003)가 재현됨.

### ST-004: 파라미터 채찍 효과 (Regulatory Whiplash)
- **목표**: 짧은 시간 내에 상반된 명령 주입 시 `GlobalRegistry`의 동기화 및 롤백 성능 검증.
- **조작**:
    - 틱 100: `TAX_RATE` -> 0.9
    - 틱 101: `UNDO_LAST_COMMAND`
    - 틱 102: `TAX_RATE` -> 0.05
- **관측 지표**:
    - `UndoStack`의 복구 정확도.
    - 엔진 내 각 모듈(Tax, Firm, Household)이 참조하는 값의 일치 여부 (Split-Brain 검사).
- **성공 기준**: 롤백 후 상태가 개입 전과 100% 일치해야 함.

---

## 4. 정합성 지표 및 감사 기준 (Audit Metrics)

| 지표 (KPI) | 측정 방법 | 임계치 (Threshold) |
| :--- | :--- | :--- |
| **M2 Integrity** | `total_m2_audit` (Internal + External Injection) | 오차 0.0001% 미만 |
| **Command Latency** | WebSocket 전송부터 Phase 0 반영까지의 시간 | < 100ms (Local) |
| **Atomic Rollback** | 실패 시 상태 복구 성공률 | 100% |
| **Consistency Check** | `GlobalRegistry` vs `Module Internal State` 비교 | 완전 일치 |

---

## 5. 단계별 실행 계획 (Execution Roadmap)

1.  **Dry Run (Tick 0-100)**: 개입 없이 베이스라인 데이터 수집.
2.  **Single Shock (Tick 101)**: ST-001 단일 명령 주입 후 10틱간 관찰.
3.  **Compound Shock (Tick 200)**: ST-002 + ST-003 동시 주입 (복합 위기).
4.  **Recovery Test (Tick 300)**: 모든 개입 파라미터 원복 후 경제 회복 탄력성 측정.
5.  **Audit Report**: `SettlementSystem` 로그를 기반으로 한 최종 무결성 보고서 생성.

---

## 6. 아키텍처적 지뢰 및 대응 (Risk Audit)

- **M2 보존 법칙 위반**: 인젝션을 Ledger에 기록하지 않으면 감사 엔진이 시스템 오류로 판단함. -> **대응**: `GodMode_Injection_Account` 가상 계좌 도입.
- **비결정성 (Non-determinism)**: 네트워크 지연으로 명령이 다른 틱에 들어갈 경우 재현 불가능. -> **대응**: 모든 명령에 `Target_Tick` 명시 및 큐잉 처리.
- **성능 저하**: 매 틱 `total_m2_audit` 실행 시 $O(N)$ 부하 발생. -> **대응**: 스트레스 테스트 모드에서만 활성화하고, 대규모 에이전트 환경에서는 샘플링 검사 실시.

---

## 7. Mandatory Reporting Verification

본 스트레스 테스트 계획 수립 과정에서 식별된 다음의 사항을 인사이트 리포트로 기록함.
- **파일 위치**: `communications/insights/GODMODE_STRESS_PLAN_INSIGHTS.md`
- **기록 항목**:
    - `SettlementSystem`의 트랜잭션 락 범위 축소 필요성 (뱅크런 시나리오 대응).
    - `GlobalRegistry` 변경 사항을 모든 엔진 컴포넌트에 즉시 전파하기 위한 Observer 패턴 도입 제안.
    - 거시 충격 시나리오에서 `Government` 모듈의 재정 파산(Insolvency) 처리 로직 미비점.

> **"Watchtower는 단순한 뷰어가 아니다. 그것은 엔진의 물리 법칙을 테스트하는 가속기다. 파괴적인 실험을 통해 시스템의 진정한 강건함을 증명하라."**
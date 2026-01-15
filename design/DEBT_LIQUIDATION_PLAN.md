# 🏦 Phase 26: Stabilization & Debt Liquidation Plan

**Subject:** 기초 금융 정합성 확보 및 핵심 기술부채(TD-030/031) 상환 계획
**Date:** 2026-01-15
**Goal:** Phase 26 전략 엔진 통합 전, 정확한 통화량 집계와 신용 창출 메커니즘을 복구함.

---

## 1. 병렬 수행 트랙 (Parallel Execution Tracks)

효율적인 부채 청산을 위해 작업을 세 가지 독립적 트랙으로 분할하여 Jules 요원들에게 배정합니다.

### 🛤️ Track A: 금융 시스템 현대화 (Banking & Credit)
- **대상 부채**: **TD-030 (Fractional Reserve)**
- **핵심 목표**: 신용 창출 공식 활성화 및 은행 유동성 병목 제거.
- **주요 작업**:
    - `config.py`: `RESERVE_REQ_RATIO` (0.1) 추가.
    - `simulation/bank.py`: `grant_loan` 자산 체크 로직 현대화 (100% -> Reserve Ratio 기반).
    - `check_solvency`와의 시퀀스 정합성 검증.
- **배정 요원**: Jules Alpha (Engine Expert)

### 🛤️ Track B: 통화 무결성 복구 (Monetary Integrity)
- **대상 부채**: **TD-031 (Money Leakage)**
- **핵심 목표**: 시스템 내 '사라지는 돈' 원천 차단 및 장부 동기화.
- **주요 작업**:
    - `simulation/systems/inheritance_manager.py`: 은행 예금 상속 로직 추가.
    - `simulation/engine.py`: 틱 600 쇼크 및 기업 청산 시 `total_money_destroyed` 장부 동기화 코드 삽입.
- **배정 요원**: Jules Bravo (Integrity Specialist)

### 🛤️ Track C: 매크로 전략 엔진 통합 (Strategy Engine)
- **기존 과업**: **Phase 26 Step 1 (Macro-Linked Portfolio)**
- **핵심 목표**: 거시 신호 연동 위험 회피 로직 구현.
- **주요 작업**:
    - `PortfolioManager`: `calculate_effective_risk_aversion` 추가.
    - `Engine`: `MacroFinancialContext` 생성 및 주입.
- **배정 요원**: Jules Charlie (AI/Strategy Expert)

---

## 2. 통합 및 검증 시퀀스 (Integration Sequence)

1.  **Track A + B 병렬 수행**: 기초 금융 데이터의 무결성 확보.
2.  **Snapshot Audit**: 수정 후 `verify_monetary_integrity.py`를 실행하여 Delta가 0에 수렴하는지 확인.
3.  **Track C 병행/후행 수행**: 깨끗해진 거시 지표를 바탕으로 AI 가계의 결정 로직 구현.
4.  **Iron Test**: 전체 시스템의 유동성 증가 및 위기 대응 능력 측정.

---

## 3. 리스크 관리 (Risk Management)

- **인플레이션 폭발**: 신용 창출(TD-030)이 시작되면 통화량이 급증할 수 있음. → 중앙은행(`CentralBank`)의 Taylor Rule 금리 인상 민감도를 사전 체크할 것.
- **데이터 비동기**: 세 요원이 서로 다른 파일을 수정하므로, `config.py`와 `engine.py` 병합 시 컨플릭트 주의.

---
> [!IMPORTANT]
> 본 계획은 **"정확한 측정 없이는 올바른 전략도 없다"**는 원칙 하에 수립되었습니다. 부채 청산 후의 데이터는 AI 모델의 학습 효율을 비약적으로 높일 것입니다.

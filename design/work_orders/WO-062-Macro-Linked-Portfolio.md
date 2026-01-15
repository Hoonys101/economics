# Work Order: WO-062 - Macro-Linked Portfolio Decisions

**Phase:** 26 (Strategy Engine Integration)
**Assignee:** Jules Charlie (AI/Strategy Expert)

## 1. Problem Statement
현재 가계의 Merton 포트폴리오 로직은 거시 경제 환경의 변화를 무시하고 기대 수익률에만 의존합니다. 이는 불황이나 고인플레이션 시기에 가계가 안전 자산으로 대피하지 못하는 비현실적인 결과를 초래합니다.

## 2. Objective
거시 경제 지표(인플레이션, GDP 성장률, 금리 추세)를 가계의 분산 투자 결정에 연동하여, 경제적 스트레스 상황에서 위험 회피도가 동적으로 상승하도록 구현합니다.

## 3. Implementation Plan

### Task A: `MacroFinancialContext` DTO 및 API 정의
- `simulation/decisions/api.py`를 생성하거나 기존 인터페이스를 확장하여 `MacroFinancialContext`를 정의하십시오.

### Task B: `PortfolioManager` 로직 확장
- `calculate_effective_risk_aversion` 메서드를 구현하십시오.
- 인플레이션 > 2% 또는 GDP 성장률 < 0%일 때 스트레스 계수를 계산하여 `base_lambda`에 곱하십시오 (최대 3배 제한).

### Task C: `Engine` 파이프라인 연동
- `simulation/engine.py`에서 매 틱마다 거시 지표를 수집하여 `MacroFinancialContext`를 생성하십시오.
- 가계의 `make_decision` 호출 시 이 컨텍스트가 전달되어 포트폴리오 최적화에 사용되도록 연결하십시오.

## 4. Verification
- `tests/test_portfolio_macro.py`를 작성하여 다음 시나리오를 검증하십시오.
    - **Normal**: Lambda 보정 없음.
    - **Stagflation**: Lambda 1.5배 이상 상승 및 주식 비중 감소 확인.
- 시뮬레이션 중 'Chaos Injection' 시기에 가계의 자산 배분 변화 리포트를 출력하십시오.

---
> [!IMPORTANT]
> 금융 데이터의 무결성(Track B)이 확보된 이후의 지표를 사용해야 하므로, 병합 시점에 타 트랙과의 정합성을 확인하십시오.

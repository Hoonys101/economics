# 경제 시뮬레이션 고도화 세부 TODO 리스트 (2025-08-27)

## Phase 1: 핵심 경제 순환 복구 및 기초 금융 확립

- [ ] **1-1. 가계 '최저 생계비 지출' 규칙 구현**
    - **목표:** 가계가 생존에 필요한 최소한의 소비를 하도록 강제하여 경제 순환을 시작시킨다.
    - **주요 수정 파일:** `simulation/decisions/household_decision_engine.py`
    - **검증 방법:** 시뮬레이션 실행 후 `analyze_results.py` 분석 시, `total_consumption` 지표가 더 이상 0이 아니고, 가계의 초기 파산율이 유의미하게 감소했는지 확인한다.

- [ ] **1-2. '은행' 주체 및 '대출 시장' 구현**
    - **목표:** 기업과 가계가 자금을 빌릴 수 있는 중앙 집중형 대출 시스템을 구축한다.
    - **신규 파일:** `simulation/agents/bank.py`, `simulation/markets/loan_market.py`
    - **주요 수정 파일:** `simulation/engine.py` (은행 및 대출시장 추가), `simulation/decisions/firm_decision_engine.py` (대출 신청 로직), `simulation/decisions/household_decision_engine.py` (대출 신청 로직)
    - **검증 방법:** 로그를 통해 기업이 대출을 받아 자본금이 증가하는지, 또는 위기에 처한 가계가 대출을 받아 파산을 면하는지 케이스를 확인한다.

## Phase 2: 거시 경제 안정성 및 내생적 성장 동력 확보

- [ ] **2-1. '정부' 주체 및 재정 정책 구현**
    - **목표:** 세금 징수 및 실업 수당 지급을 통해 경제 안정화 장치를 도입한다.
    - **신규 파일:** `simulation/agents/government.py`
    - **주요 수정 파일:** `simulation/engine.py` (정부 추가), `simulation/agents.py` 및 하위 클래스 (소득/이익 발생 시 세금 납부 로직 추가), `simulation/decisions/household_decision_engine.py` (실업 수당 수령 로직)
    - **검증 방법:** `simulation_log_EconomicIndicatorTracker.csv` 또는 별도 로그를 통해 정부의 총 세수(tax_revenue)와 총 지출(government_spending)이 기록되는지 확인한다. 실업 상태인 가계의 자산이 실업 수당만큼 증가하는지 확인한다.

- [ ] **2-2. 기업 'R&D 투자' 메커니즘 구현**
    - **목표:** 기업이 R&D 투자를 통해 스스로 생산성을 향상시키는 장기 성장 동력을 마련한다.
    - **주요 수정 파일:** `simulation/decisions/firm_decision_engine.py` (R&D 투자 결정 로직), `simulation/firms.py` (`produce` 메서드 등에서 생산성 반영)
    - **검증 방법:** 특정 기업이 R&D('education_service' 구매)에 투자한 후, 해당 기업의 `productivity_factor` 속성값이 시간이 지남에 따라 실제로 증가하는지 로그를 통해 추적 및 확인한다.

## Phase 3: 자본 시장 개방과 동적 경쟁 심화

- [ ] **3-1. '자본 시장(Stock Market)' 구현**
    - **목표:** 주식 발행 및 거래를 통해 기업의 자본 조달과 가계의 투자 활동을 가능하게 한다.
    - **신규 파일:** `simulation/markets/stock_market.py` (오더북 기반)
    - **주요 수정 파일:** `simulation/firms.py` (주식 발행 관련 속성 추가), `simulation/decisions/household_decision_engine.py` (주식 매수/매도 결정 로직), `simulation/engine.py` (주식 시장 추가)
    - **검증 방법:** `StockMarket` 관련 로그를 통해 특정 기업의 주식에 대한 매수/매도 주문이 발생하고, 거래가 체결되어 주가가 변동하는지 확인한다. 가계의 자산에 `shares_owned`가 반영되는지 확인한다.

- [ ] **3-2. 전략적 경쟁 로직 구현**
    - **목표:** 기업이 경쟁사의 가격과 시장 평균 임금을 의사결정에 반영하도록 하여 경쟁을 심화시킨다.
    - **주요 수정 파일:** `simulation/decisions/firm_decision_engine.py`
    - **검증 방법:** 로그를 통해 특정 기업이 판매가 결정 시 `market.get_best_ask()`를 호출하고, 구인 시 `labor_market`의 평균 임금 정보를 활용하는지 확인한다. 경쟁사보다 낮은 가격으로 판매 주문을 내거나, 평균보다 높은 임금으로 구인하는 구체적인 사례를 로그에서 확인한다.

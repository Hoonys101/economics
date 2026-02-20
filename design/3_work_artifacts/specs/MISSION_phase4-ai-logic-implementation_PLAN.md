# Mission 4.1 Implementation Plan: AI Intelligence & Lifecycle Hardening

## 1. Overview
Implementing "Composite Intelligence" for AI agents to handle information asymmetry and heterogeneity, and adding a "Scrubbing Phase" to the agent lifecycle to maintain queue integrity.

## 2. Proposed Changes

### 2.1. DTO & Interfaces
#### [MODIFY] [api.py](file:///c:/coding/economics/simulation/dtos/api.py)
-   Add `system_debt_to_gdp_ratio: float` and `system_liquidity_index: float` to `GovernmentPolicyDTO`.
-   Add `fiscal_stance_indicator: str` (e.g., "EXPANSION", "CONTRACTION") to `GovernmentPolicyDTO`.

### 2.2. AI Intelligence & Labor Market (Mission 4.1-A) [PIVOTED]
#### [Engine] Dynamic Insight Engine (통찰력 엔진)
- **Active Learning**: `AITrainingManager`에서 TD-Error 정규화 값을 `market_insight` 증가분으로 매핑.
- **Service Boosting**: 'Education Service' 구매 시 `market_insight` 즉시 상승.
- **Natural Decay**: 매 틱 `-0.001` 수준의 자동 감퇴 로직.

#### [Decision] Perceptual Filters (인지 필터)
- `market_insight` 값에 따라 거시 지표 수신 시차/노이즈 부여:
  - `> 0.8`: 0-Tick Lag (Smart Money)
  - `> 0.3`: 3-Tick Moving Average (Laggards)
  - `< 0.3`: 5-Tick Lag + 5% Gaussian Noise (Lemons)

#### [Market] Labor Market Matching Engine [NEW]
- **Utility-Priority**: `Value = ExpectedProductivity / Wage`.
- **Bipartite Matching**: 다대일 매칭 시스템 구현.

#### [Logic] Herd Behavior & Panic Propagation
- **Panic Index Generation**: `TickOrchestrator` calculates `Withdrawal Volume / Deposits` and broadcasts via `GovernmentPolicyDTO`.
- **Insight-Weighted Decision**: 
  - Low Insight agents: High sensitivity to `market_panic_index`. 
  - High Insight agents: Lead the market (Smart Money), reacting to fundamental lags rather than the panic index.

#### [DTO] API Extensions
- `AgentStateData`: `market_insight: float`
- `GovernmentPolicyDTO`: `market_panic_index: float`, `system_debt_to_gdp_ratio: float`
- `JobOfferDTO`: `required_education: int`
- `JobSeekerDTO`: `education_level: int`

### 2.4. Configuration (Mission 4.1-C)
#### [NEW] [dynamic_config.py](file:///c:/coding/economics/simulation/systems/dynamic_config.py)
-   Implement `GlobalRegistry` to store `DEBT_CEILING`, `AUSTERITY_TRIGGER`.
-   Provide a subscriber model or direct lookup proxy for Engines.

## 3. Verification Plan
### Automated Tests
-   `tests/unit/test_lifecycle_scrubbing.py`: Verify that dead agent transactions are removed from the queue.
-   `tests/unit/test_ai_information_asymmetry.py`: Verify that agents with low education receive "blurred" macro data.
-   `tests/system/test_heterogeneous_reaction.py`: Run 100 ticks and verify that bank-run/investment freezes occur at different times across the population.
